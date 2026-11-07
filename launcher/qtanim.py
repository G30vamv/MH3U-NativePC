"""Small, cheap animations for the launcher, and the hover explanations (tooltips).

Everything here costs nothing while the window sits still: an animation only runs for a fraction of a second after a click or a
hover, and the only thing that keeps running (the glow of the PLAY button) stops by itself when the window is not in front, when
the game is running, or when animations are off. They are off if the user switches them off in the menu or has asked Windows to
reduce animations.
"""

import ctypes
import sys

from PySide6.QtCore import QEasingCurve, QObject, QPropertyAnimation, QTimer, QVariantAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QProxyStyle, QStyle

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


def fade_in(widget, ms=170):
    """Fades a widget in with an opacity effect that is taken off again at the end (an effect left on makes every repaint slower)."""
    if not enabled() or not widget.isVisible():
        return
    old = getattr(widget, "_fade", None)
    if old is not None:
        old.stop()
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def done():
        if widget.graphicsEffect() is effect:
            widget.setGraphicsEffect(None)
        widget._fade = None

    anim.finished.connect(done)
    widget._fade = anim
    anim.start()


def fade_window_in(window, ms=300):
    """The window appears softly (the desktop composes it, so it costs the launcher nothing)."""
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


def hover_animation(owner, ms=140):
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
    from PySide6.QtGui import QColor

    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
        round(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


class Glow(QObject):
    """A slow breathing of one widget (the PLAY button): `target.glow` goes 0..1..0 about every 2.8 s, at 25 frames a second.

    It only runs while `allowed()` says so (window in front, game not running, animations on); otherwise the timer is stopped and
    the widget goes back to rest, so a launcher left open beside the game costs nothing.
    """

    PERIOD = 2.8

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
        import math

        self._t += 0.04 / self.PERIOD
        self._target.glow = (1 - math.cos(2 * math.pi * self._t)) / 2
        self._target.update()


def tip_html(text):
    """Wraps a tooltip's text so Qt lays it out as a block of readable width (plain tooltips do not wrap)."""
    import html

    body = html.escape(str(text)).replace("\n", "<br>")
    return f'<table width="360"><tr><td>{body}</td></tr></table>'


class TipStyle(QProxyStyle):
    """The same look as the default style, with the explanations appearing a little sooner (0.25 s) and staying while they are read."""

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.StyleHint.SH_ToolTip_WakeUpDelay:
            return 250
        if hint == QStyle.StyleHint.SH_ToolTip_FallAsleepDelay:
            return 600
        return super().styleHint(hint, option, widget, returnData)
