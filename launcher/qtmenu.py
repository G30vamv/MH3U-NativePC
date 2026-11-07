"""The drop-down menu of the gear button in the title bar: the options of the launcher itself (not of the game)."""

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QFrame, QHBoxLayout, QVBoxLayout

import qtanim
from qtshim import PARCHMENT, Label, Switch, font

WIDTH = 330


class _Row(QAbstractButton):
    """One action of the menu: lights up under the mouse."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFont(font(10.5))
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
        p.setPen(qtanim.mix(QColor(PARCHMENT), QColor("#fff6e0"), self._hover))
        p.setFont(self.font())
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
        slide.setStartValue(self._home + QPoint(0, -12))
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
