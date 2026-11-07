"""The drop-down menu of the gear button in the title bar: every section of the launcher, plus a few launcher options."""

from PySide6.QtCore import QPoint, QPropertyAnimation, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QFrame, QVBoxLayout

import qtanim
from qtshim import GOLD, PARCHMENT, Switch, font

WIDTH = 288


class _Row(QAbstractButton):
    """One line of the menu: lights up under the mouse, and in gold when it is the page being shown."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFont(font(10.5))
        self.current = False
        self._anim = qtanim.hover_animation(self, 120)

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
        r = QRectF(self.rect()).adjusted(2, 1, -2, -1)
        if self.current:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(GOLD))
            p.drawRoundedRect(r, 9, 9)
            color = QColor("#fff6e0")
        else:
            if self._hover > 0:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(255, 255, 255, round(34 * self._hover)))
                p.drawRoundedRect(r, 9, 9)
            color = qtanim.mix(QColor(PARCHMENT), QColor("#fff6e0"), self._hover)
        p.setPen(color)
        f = self.font()
        f.setBold(self.current)
        p.setFont(f)
        p.drawText(QRectF(14, 0, self.width() - 20, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())


class SettingsMenu(QFrame):
    def __init__(self, window):
        super().__init__(window, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(WIDTH)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(10, 10, 10, 10)
        self._lay.setSpacing(2)
        self._pages = {}
        self._fade = None
        self.on_hidden = None  # called when the menu closes (the gear stops being lit)
        self.setAttribute(Qt.WidgetAttribute.WA_NoMouseReplay)  # a click on the gear closes the menu and does not open it again

    def _add_row(self, text, command, close=True):
        row = _Row(text)
        row.clicked.connect(lambda checked=False: self._run(command, close))
        self._lay.addWidget(row)
        return row

    def _run(self, command, close):
        if close:
            self.close()
            QTimer.singleShot(0, command)  # the menu is gone before the page changes
        else:
            command()

    def add_page(self, key, text, command):
        self._pages[key] = self._add_row(text, command)

    def add_action(self, text, command):
        return self._add_row(text, command)

    def add_separator(self):
        sep = QFrame()
        sep.setFixedHeight(9)
        sep.setStyleSheet("background: transparent;")
        self._lay.addWidget(sep)
        self._sep_count = getattr(self, "_sep_count", 0) + 1

    def add_switch(self, text, checked, command, tip=None):
        sw = Switch(text, command)
        sw.setFixedHeight(34)
        sw.setContentsMargins(0, 0, 0, 0)
        if checked:
            sw.select()
        if tip:
            sw.setToolTip(tip)
        wrap = QFrame()
        wrap.setStyleSheet("background: transparent;")
        from PySide6.QtWidgets import QHBoxLayout

        h = QHBoxLayout(wrap)
        h.setContentsMargins(12, 0, 8, 0)
        h.addWidget(sw)
        self._lay.addWidget(wrap)
        return sw

    def set_current(self, key):
        for k, row in self._pages.items():
            row.current = k == key
            row.update()

    def popup_below(self, button):
        """Opens the menu under `button`, its right edge in line with the button's."""
        self.adjustSize()
        corner = button.mapToGlobal(QPoint(button.width(), button.height()))
        self.move(corner.x() - self.width() + 6, corner.y() + 2)
        self.show()

    def showEvent(self, event):
        super().showEvent(event)
        if qtanim.enabled():
            self.setWindowOpacity(0.0)
            self._fade = QPropertyAnimation(self, b"windowOpacity", self)
            self._fade.setDuration(130)
            self._fade.setStartValue(0.0)
            self._fade.setEndValue(1.0)
            self._fade.start()
        else:
            self.setWindowOpacity(1.0)

    def hideEvent(self, event):
        super().hideEvent(event)
        if self.on_hidden:
            self.on_hidden()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setBrush(QColor(10, 24, 32, 244))
        p.setPen(QPen(QColor(255, 255, 255, 50), 1))
        p.drawRoundedRect(r, 14, 14)
