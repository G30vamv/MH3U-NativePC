"""Small, cheap animations for the launcher, and the hover explanations (tooltips).

Everything here costs nothing while the window sits still: an animation only runs for a fraction of a second after a click or a
hover, and the only thing that keeps running (the glow of the PLAY button) stops by itself when the window is not in front, when
the game is running, or when animations are off. They are off if the user switches them off in the menu or has asked Windows to
reduce animations.
"""

import ctypes
import math
import sys

from PySide6.QtCore import QEasingCurve, QEvent, QObject, QParallelAnimationGroup, QPoint, QPropertyAnimation, QRectF, Qt, QTimer, QVariantAnimation
from PySide6.QtGui import QColor, QGuiApplication, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QApplication, QFrame, QGraphicsOpacityEffect, QLabel, QProxyStyle, QStyle, QVBoxLayout, QWidget

_user_wants = True  # the "Animaciones" switch of the menu
_windows_allows = None  # cached answer of Windows ("Show animations in Windows")


def windows_allows():
    """Whether Windows has animations on (SPI_GETCLIENTAREAANIMATION); true when it cannot tell."""
    global _windows_allows
    if _windows_allows is None:
        _windows_allows = True
        if sys.platform == "win32":
            try:
                flag = ctypes.c_int(1)
                if ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(flag), 0):
                    _windows_allows = bool(flag.value)
            except Exception:
                pass
    return _windows_allows


def set_user_choice(on):
    global _user_wants
    _user_wants = bool(on)


def enabled():
    return _user_wants and windows_allows()


def reveal(widget, ms=260, dy=18, delay=0):
    """Fades a widget in while it rises `dy` pixels into its place (an opacity effect, taken off at the end: an effect left on makes
    every repaint slower). With a `delay` the widget waits invisible, so several can come in one after the other."""
    if not enabled() or not widget.isVisible():
        return
    old = getattr(widget, "_reveal", None)
    if old is not None:
        old[0].stop()
        if old[1].graphicsEffect() is old[2]:
            old[1].setGraphicsEffect(None)
    end = widget.geometry()
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)
    fade = QPropertyAnimation(effect, b"opacity", widget)
    fade.setDuration(ms)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(QEasingCurve.Type.OutCubic)
    slide = None
    if dy:
        slide = QPropertyAnimation(widget, b"pos", widget)
        slide.setDuration(ms)
        slide.setStartValue(end.topLeft() + QPoint(0, dy))
        slide.setEndValue(end.topLeft())
        slide.setEasingCurve(QEasingCurve.Type.OutCubic)

    def done():
        if widget.graphicsEffect() is effect:
            widget.setGraphicsEffect(None)
        if dy and widget.pos() != end.topLeft() and widget.geometry().size() == end.size():
            widget.move(end.topLeft())
        widget._reveal = None

    fade.finished.connect(done)

    def go():
        if widget._reveal is None:
            return
        if slide is not None:
            widget.move(end.topLeft() + QPoint(0, dy))
            slide.start()
        fade.start()

    widget._reveal = (fade, widget, effect)
    if delay:
        QTimer.singleShot(delay, go)
    else:
        go()


_NO_LIMIT = 16777215  # QWIDGETSIZE_MAX


def _end_fold(widget):
    """Stops a fold that is running and puts the widget back to its normal size limits."""
    old = getattr(widget, "_fold", None)
    if old is not None:
        old.stop()
        widget._fold = None
    widget.setMaximumHeight(_NO_LIMIT)
    if widget.graphicsEffect() is not None:
        widget.setGraphicsEffect(None)


def _fold(widget, start_h, end_h, start_o, end_o, ms, after):
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(start_o)
    widget.setGraphicsEffect(effect)
    group = QParallelAnimationGroup(widget)
    height = QPropertyAnimation(widget, b"maximumHeight")
    height.setDuration(ms)
    height.setStartValue(start_h)
    height.setEndValue(end_h)
    height.setEasingCurve(QEasingCurve.Type.OutCubic)
    fade = QPropertyAnimation(effect, b"opacity")
    fade.setDuration(ms)
    fade.setStartValue(start_o)
    fade.setEndValue(end_o)
    fade.setEasingCurve(QEasingCurve.Type.OutCubic)
    group.addAnimation(height)
    group.addAnimation(fade)

    def done():
        widget._fold = None
        widget.setMaximumHeight(_NO_LIMIT)
        if widget.graphicsEffect() is effect:
            widget.setGraphicsEffect(None)
        after()

    group.finished.connect(done)
    widget._fold = group
    group.start()


def expand_in(widget, ms=260):
    """Shows a hidden widget by unfolding it (its height grows from nothing while it fades in), so what is below it slides down."""
    _end_fold(widget)
    parent = widget.parentWidget()
    if not enabled() or parent is None or not parent.isVisible():
        widget.show()
        return
    widget.setMaximumHeight(0)
    widget.show()
    target = max(widget.sizeHint().height(), widget.minimumSizeHint().height(), 1)
    _fold(widget, 0, target, 0.0, 1.0, ms, lambda: None)


def collapse_out(widget, ms=220):
    """Hides a widget by folding it away (its height shrinks to nothing while it fades out), so what is below it slides up."""
    _end_fold(widget)
    if not enabled() or not widget.isVisible():
        widget.hide()
        return
    _fold(widget, widget.height(), 0, 1.0, 0.0, ms, widget.hide)


def fade_in(widget, ms=170):
    """A plain fade (no movement)."""
    reveal(widget, ms, 0)


def fade_window_in(window, ms=200):
    """The window appears at once but softly (the desktop composes it, so it costs the launcher nothing)."""
    if not enabled():
        window.setWindowOpacity(1.0)
        return
    window.setWindowOpacity(0.0)
    anim = QPropertyAnimation(window, b"windowOpacity", window)
    anim.setDuration(ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    window._intro = anim
    anim.start()


def minimize_window(window, ms=170):
    """Minimises the window softly: it fades out while it sinks a little towards the taskbar, then Windows minimises it. The window
    is put back in its place and opaque while it is minimised, so restoring it finds it whole (`fade_window_in` shows it again).
    With animations off, or if it is already going down, it minimises at once."""
    if not enabled() or window.isMinimized() or getattr(window, "_minimizing", None) is not None:
        window.showMinimized()
        return
    start = window.pos()
    group = QParallelAnimationGroup(window)
    fade = QPropertyAnimation(window, b"windowOpacity", window)
    fade.setDuration(ms)
    fade.setStartValue(1.0)
    fade.setEndValue(0.0)
    fade.setEasingCurve(QEasingCurve.Type.InCubic)
    group.addAnimation(fade)
    if not window.isMaximized():
        sink = QPropertyAnimation(window, b"pos", window)
        sink.setDuration(ms)
        sink.setStartValue(start)
        sink.setEndValue(QPoint(start.x(), start.y() + 36))
        sink.setEasingCurve(QEasingCurve.Type.InCubic)
        group.addAnimation(sink)

    def done():
        window._minimizing = None
        if not window.isMaximized():
            window.move(start)
        window.showMinimized()
        window.setWindowOpacity(1.0)

    group.finished.connect(done)
    window._minimizing = group
    group.start()


def intro(parts, first_delay=60, step=90, ms=420):
    """The parts of the window (header, tabs, page, footer) come in one after the other, rising a little, when the launcher opens."""
    for i, part in enumerate(parts):
        reveal(part, ms, 16, first_delay + step * i)


def hover_animation(owner, ms=180):
    """A 0..1 value that follows the mouse: `owner._hover` is set and `owner.update()` called on each step."""
    owner._hover = 0.0
    anim = QVariantAnimation(owner)
    anim.setDuration(ms)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def step(v):
        owner._hover = float(v)
        owner.update()

    anim.valueChanged.connect(step)
    return anim


def hover_to(owner, anim, target):
    """Moves the hover value of `owner` to 0 or 1, softly when animations are on."""
    anim.stop()
    if not enabled():
        owner._hover = float(target)
        owner.update()
        return
    anim.setStartValue(owner._hover)
    anim.setEndValue(float(target))
    anim.start()


def mix(a, b, t):
    """Blends two QColor (t = 0 gives a, t = 1 gives b)."""
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
        round(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


class Glow(QObject):
    """A slow breathing of one widget (the PLAY button): `target.glow` goes 0..1..0 about every 2.4 s, at 25 frames a second.

    It only runs while `allowed()` says so (window in front, game not running, animations on); otherwise the timer is stopped and
    the widget goes back to rest, so a launcher left open beside the game costs nothing.
    """

    PERIOD = 2.4

    def __init__(self, target, allowed, parent=None):
        super().__init__(parent or target)
        self._target = target
        self._allowed = allowed
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._tick)
        self._check = QTimer(self)  # looks every second whether the glow may run (cheap)
        self._check.setInterval(1000)
        self._check.timeout.connect(self.refresh)
        self._check.start()

    def refresh(self):
        ok = bool(self._allowed())
        if ok and not self._timer.isActive():
            self._timer.start()
        elif not ok and self._timer.isActive():
            self._timer.stop()
            self._target.glow = 0.0
            self._target.update()

    def _tick(self):
        self._t += 0.04 / self.PERIOD
        self._target.glow = (1 - math.cos(2 * math.pi * self._t)) / 2
        self._target.update()


def tip_html(text):
    """Wraps a tooltip's text so Qt lays it out as a block of readable width (plain tooltips do not wrap)."""
    import html

    import i18n

    body = html.escape(i18n.t(str(text))).replace("\n", "<br>")
    return f'<table width="360"><tr><td>{body}</td></tr></table>'


class TipStyle(QProxyStyle):
    """The same look as the default style, with the explanations appearing a little sooner (0.25 s) and staying while they are read."""

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.StyleHint.SH_ToolTip_WakeUpDelay:
            return 250
        if hint == QStyle.StyleHint.SH_ToolTip_FallAsleepDelay:
            return 600
        return super().styleHint(hint, option, widget, returnData)


class TipPopup(QFrame):
    """The explanation that shows when the mouse rests on an option: the colours of the launcher's own backdrop (deep teal-navy with a
    warm corner), light text on it so it reads well, and it fades in while rising a few pixels."""

    def __init__(self):
        super().__init__(None, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color: #f6efdc; background: transparent; font-family: 'Segoe UI'; font-size: 10pt;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 11, 16, 12)
        lay.addWidget(self.label)
        self._group = None

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        g = QLinearGradient(0, 0, r.width(), r.height())
        g.setColorAt(0.0, QColor(13, 40, 48, 250))
        g.setColorAt(0.65, QColor(14, 30, 40, 250))
        g.setColorAt(1.0, QColor(24, 30, 32, 250))
        p.setBrush(g)
        p.setPen(QPen(QColor(255, 255, 255, 60), 1))
        p.drawRoundedRect(r, 12, 12)
        warm = QRadialGradient(r.right(), r.bottom(), r.width() * 0.8)  # the amber corner of the backdrop
        warm.setColorAt(0.0, QColor(184, 121, 30, 70))
        warm.setColorAt(1.0, QColor(184, 121, 30, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(warm)
        p.drawRoundedRect(r, 12, 12)

    def show_text(self, text, global_pos):
        self.label.setText(text)
        self.setMaximumWidth(420)
        self.adjustSize()
        screen = QGuiApplication.screenAt(global_pos) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        x = min(global_pos.x() + 14, area.right() - self.width() - 8)
        y = global_pos.y() + 22
        if y + self.height() > area.bottom() - 8:  # not enough room below: above the pointer
            y = global_pos.y() - self.height() - 10
        home = QPoint(max(area.left() + 4, x), max(area.top() + 4, y))
        self.move(home)
        self.show()
        if self._group is not None:
            self._group.stop()
        if not enabled():
            self.setWindowOpacity(1.0)
            return
        self.setWindowOpacity(0.0)
        fade = QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(170)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        rise = QPropertyAnimation(self, b"pos")
        rise.setDuration(200)
        rise.setStartValue(home + QPoint(0, 8))
        rise.setEndValue(home)
        rise.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._group = QParallelAnimationGroup(self)
        self._group.addAnimation(fade)
        self._group.addAnimation(rise)
        self._group.start()


class TipManager(QObject):
    """Shows `TipPopup` instead of Qt's plain tooltip for every widget that has a tooltip."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.popup = TipPopup()
        self._owner = None

    def hide(self):
        self._owner = None
        if self.popup.isVisible():
            self.popup.hide()

    def eventFilter(self, obj, event):
        try:
            return self._filter(obj, event)
        except RuntimeError:  # the popup is already gone (the application is closing)
            return False

    def _filter(self, obj, event):
        t = event.type()
        if t == QEvent.Type.ToolTip and isinstance(obj, QWidget) and obj is not self.popup:
            text = obj.toolTip()
            if text:
                self._owner = obj
                self.popup.show_text(text, event.globalPos())
                return True
            return False
        if t in (QEvent.Type.Leave, QEvent.Type.Hide) and obj is self._owner:
            self.hide()
        elif t in (QEvent.Type.MouseButtonPress, QEvent.Type.Wheel, QEvent.Type.KeyPress, QEvent.Type.WindowDeactivate):
            self.hide()
        return False


def install_tips(app=None):
    """Turns on the launcher's own tooltips for the whole application (keeps a reference so it lives as long as the app)."""
    app = app or QApplication.instance()
    manager = TipManager(app)
    app.installEventFilter(manager)
    app.aboutToQuit.connect(lambda: app.removeEventFilter(manager))
    app._tip_manager = manager
    return manager
