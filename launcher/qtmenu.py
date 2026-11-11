"""The drop-down menu of the gear button in the title bar: the options of the launcher itself (not of the game). Also the drop-down
list of a setting with many choices (`DropList`), which opens the same way."""

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPoint, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QFrame, QHBoxLayout, QVBoxLayout

import i18n
import qtanim
from qtshim import PARCHMENT, Label, Segmented, Switch, font

WIDTH = 330
GOLD = "#d4922a"
GOLD_TEXT = "#eab84c"



class _Row(QAbstractButton):
    """One action of the menu: lights up under the mouse."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setText(i18n.t(str(text)))
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFont(font(10.5))
        self.chosen = False  # the entry in force (a list of choices marks it in gold)
        self._anim = qtanim.hover_animation(self, 140)

    def sizeHint(self):
        return QSize(WIDTH - 20, 36)

    def enterEvent(self, event):
        qtanim.hover_to(self, self._anim, 1)
        super().enterEvent(event)

    def leaveEvent(self, event):
        qtanim.hover_to(self, self._anim, 0)
        super().leaveEvent(event)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._hover > 0:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, round(40 * self._hover)))
            p.drawRoundedRect(QRectF(self.rect()).adjusted(2, 1, -2, -1), 9, 9)
        if self.chosen:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(GOLD))
            p.drawRoundedRect(QRectF(5, 9, 3, self.height() - 18), 1.5, 1.5)
        p.setPen(QColor(GOLD_TEXT) if self.chosen else qtanim.mix(QColor(PARCHMENT), QColor("#fff6e0"), self._hover))
        f = self.font()
        f.setBold(self.chosen)
        p.setFont(f)
        p.drawText(QRectF(14, 0, self.width() - 20, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())


class SettingsMenu(QFrame):
    def __init__(self, window):
        super().__init__(window, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoMouseReplay)  # a click on the gear closes the menu and does not open it again
        self.setFixedWidth(WIDTH)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(10, 10, 10, 10)
        self._lay.setSpacing(2)
        self._group = None
        self._home = QPoint(0, 0)
        self.on_hidden = None  # called when the menu closes (the gear stops being lit)

    def add_title(self, text):
        label = Label(text, "#9db3ba", 9.5, bold=True)
        label.setContentsMargins(14, 2, 0, 4)
        self._lay.addWidget(label)

    def add_choice(self, values, current, command):
        """A selector (a gold pill under the chosen entry) that stays in the menu; returns it."""
        seg = Segmented(values, command, size=10)
        seg.set(current)
        wrap = QFrame()
        wrap.setStyleSheet("background: transparent;")
        h = QHBoxLayout(wrap)
        h.setContentsMargins(10, 2, 8, 6)
        h.addWidget(seg)
        self._lay.addWidget(wrap)
        return seg

    def add_action(self, text, command):
        row = _Row(text)
        row.clicked.connect(lambda checked=False: self._run(command))
        self._lay.addWidget(row)
        return row

    def _run(self, command):
        self.close()
        QTimer.singleShot(0, command)  # the menu is gone before the action starts

    def add_separator(self):
        sep = QFrame()
        sep.setFixedHeight(10)
        sep.setStyleSheet("background: transparent;")
        self._lay.addWidget(sep)

    def add_switch(self, text, checked, command, tip=None):
        """A switch that stays in the menu when clicked (`tip` is the text shown when the mouse is over it)."""
        sw = Switch(text, command)
        sw.setFixedHeight(34)
        if checked:
            sw.select()
        if tip:
            sw.setToolTip(tip)
        wrap = QFrame()
        wrap.setStyleSheet("background: transparent;")
        h = QHBoxLayout(wrap)
        h.setContentsMargins(12, 0, 8, 0)
        h.addWidget(sw)
        self._lay.addWidget(wrap)
        return sw

    def popup_below(self, button):
        """Opens the menu under `button`, its right edge in line with the button's."""
        self.adjustSize()
        corner = button.mapToGlobal(QPoint(button.width(), button.height()))
        self._home = QPoint(corner.x() - self.width() + 6, corner.y() + 2)
        self.move(self._home)
        self.show()

    def showEvent(self, event):
        super().showEvent(event)
        if not qtanim.enabled():
            self.setWindowOpacity(1.0)
            return
        # it fades in while sliding down a few pixels
        self.setWindowOpacity(0.0)
        fade = QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(200)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        slide = QPropertyAnimation(self, b"pos")
        slide.setDuration(220)
        slide.setStartValue(self._home + QPoint(0, 12 if getattr(self, "_rise", False) else -12))
        slide.setEndValue(self._home)
        slide.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._group = QParallelAnimationGroup(self)
        self._group.addAnimation(fade)
        self._group.addAnimation(slide)
        self._group.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._group is not None:
            self._group.stop()
        if self.on_hidden:
            self.on_hidden()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setBrush(QColor(10, 24, 32, 244))
        p.setPen(QPen(QColor(255, 255, 255, 50), 1))
        p.drawRoundedRect(r, 14, 14)


class _ListPopup(SettingsMenu):
    """The entries of a `DropList`, as wide as its button and right under it (above it when there is no room below)."""

    def __init__(self, window, width):
        super().__init__(window)
        self.setFixedWidth(max(int(width), 180))
        self._lay.setContentsMargins(6, 6, 6, 6)
        self._rise = False

    def popup_under(self, button):
        self.adjustSize()
        corner = button.mapToGlobal(QPoint(0, button.height()))
        home = QPoint(corner.x(), corner.y() + 4)
        screen = QGuiApplication.screenAt(corner) or QGuiApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            if home.y() + self.height() > area.bottom():
                home.setY(button.mapToGlobal(QPoint(0, 0)).y() - self.height() - 4)
                self._rise = True
            home.setX(max(area.left(), min(home.x(), area.right() - self.width())))
        self._home = home
        self.move(home)
        self.show()


class DropList(QAbstractButton):
    """A setting with many choices that takes one line: it shows the choice in force and, when clicked, unrolls the list of all of
    them under it (it fades in and slides down, as the gear's menu). `tips` gives an entry its own explanation."""

    def __init__(self, values, command=None, tips=None, width=None, parent=None):
        super().__init__(parent)
        self._values = [str(v) for v in values]
        self._tips = dict(tips or {})
        self._value = self._values[0] if self._values else ""
        self._command = command
        self._popup = None
        self.rows = []  # the entries of the open list (for the tests)
        self.setFixedHeight(34)
        if width:
            self.setFixedWidth(width)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFont(font(10.5))
        self._anim = qtanim.hover_animation(self, 160)
        self.clicked.connect(self.toggle_list)

    def sizeHint(self):
        return QSize(260, 34)

    def get(self):
        """The chosen entry as the logic wrote it (the list shows a translation)."""
        return self._value

    def set(self, value):
        value = str(value)
        if value in self._values and value != self._value:
            self._value = value
            self.update()

    def is_open(self):
        return self._popup is not None and self._popup.isVisible()

    def enterEvent(self, event):
        qtanim.hover_to(self, self._anim, 1)
        super().enterEvent(event)

    def leaveEvent(self, event):
        qtanim.hover_to(self, self._anim, 0)
        super().leaveEvent(event)

    def toggle_list(self):
        if self.is_open():
            self._popup.close()
            return
        pop = _ListPopup(self.window(), self.width())
        self.rows = []
        for v in self._values:
            row = pop.add_action(v, lambda v=v: self._pick(v))
            row.chosen = v == self._value
            tip = self._tips.get(v)
            if tip:
                row.setToolTip(qtanim.tip_html(tip))
            self.rows.append(row)
        pop.on_hidden = self.update  # the arrow turns back
        self._popup = pop
        pop.popup_under(self)
        self.update()

    def _pick(self, value):
        if value == self._value:
            return
        self._value = value
        self.update()
        if self._command:
            self._command(value)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        lit = 1.0 if self.is_open() else self._hover
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setBrush(QColor(6, 15, 21, 185))
        p.setPen(QPen(qtanim.mix(QColor(255, 255, 255, 45), QColor(GOLD), lit), 1))
        p.drawRoundedRect(r, 9, 9)
        p.setPen(QColor("#fff6e0"))
        p.setFont(self.font())
        p.drawText(QRectF(12, 0, self.width() - 44, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, i18n.t(self._value))
        pen = QPen(qtanim.mix(QColor(PARCHMENT), QColor(GOLD_TEXT), lit), 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        cx, cy = self.width() - 18, self.height() / 2
        d = -2 if self.is_open() else 2  # the arrow points up while the list is open
        p.drawLine(QPointF(cx - 4, cy - d), QPointF(cx, cy + d))
        p.drawLine(QPointF(cx, cy + d), QPointF(cx + 4, cy - d))
