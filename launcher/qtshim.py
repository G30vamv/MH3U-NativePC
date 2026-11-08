"""
Widgets and dialogs for the launcher window (PySide6), with the small CTk-like API the launcher logic in core.py uses:
`configure(text=..., text_color=..., state=..., fg_color=..., hover_color=...)`, `get`/`set`/`select`, `insert`/`delete` on entries
and so on, plus message boxes and folder dialogs that can be called from any thread.
"""

import threading

import i18n
import qtanim
from PySide6.QtCore import QEasingCurve, QObject, QPointF, QRectF, QSize, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

END = "end"

# Moga Village / Tanzia palette
GOLD = "#b8791e"
GOLD_HOVER = "#d4922a"
TEAL = "#2f9488"
TEAL_HOVER = "#257a70"
SLATE = "#2b4a58"
SLATE_HOVER = "#3b6073"
PARCHMENT = "#e3d8bd"
RED = "#e0675c"
RED_HOVER = "#a9493f"

# kind -> (background, hover, text)
BUTTON_KINDS = {
    "default": (SLATE, SLATE_HOVER, "#fff6e0"),
    "gold": (GOLD, GOLD_HOVER, "#fff6e0"),
    "teal": (TEAL, TEAL_HOVER, "#fff6e0"),
    "ember": ("#e08e4a", "#eab84c", "#0d1820"),
    "danger": (RED, RED_HOVER, "#fff6e0"),
    "good": ("#7fcfa6", "#9bdcbb", "#0d1820"),
    "link": ("#22414f", SLATE_HOVER, "#fff6e0"),
}


def tx(text):
    """Button text with & kept as an ampersand (Qt reads a single & as a shortcut mark)."""
    return str(text).replace("&", "&&")


class _MainThread(QObject):
    """Runs a function on the GUI thread and gives its result back to the thread that asked."""

    run = Signal(object)

    def __init__(self):
        super().__init__()
        self.run.connect(self._call, Qt.ConnectionType.BlockingQueuedConnection)

    def _call(self, box):
        try:
            box["result"] = box["fn"]()
        except Exception as e:  # shown by the caller
            box["error"] = e


_main = None
_main_ident = threading.main_thread().ident


def on_main(fn):
    global _main
    if threading.get_ident() == _main_ident:
        return fn()
    if _main is None:
        raise RuntimeError("the GUI is not running")
    box = {"fn": fn}
    _main.run.emit(box)
    if "error" in box:
        raise box["error"]
    return box.get("result")


def init_threading():
    """Call once from the GUI thread after the QApplication exists."""
    global _main
    _main = _MainThread()


def _box(kind, title, text, buttons=QMessageBox.StandardButton.Ok, names=None):
    def show():
        box = QMessageBox(kind, i18n.t(str(title)), i18n.t(str(text)), buttons)
        # Qt's own translations are not shipped: the standard buttons are named here, in the launcher's language
        english = i18n.language() == "en"
        for which, es, en in (
            (QMessageBox.StandardButton.Yes, "Sí", "Yes"),
            (QMessageBox.StandardButton.No, "No", "No"),
            (QMessageBox.StandardButton.Ok, "Aceptar", "OK"),
        ):
            b = box.button(which)
            if b is not None:
                b.setText(en if english else es)
        for which, label in (names or {}).items():  # a question whose answers have names of their own
            b = box.button(which)
            if b is not None:
                b.setText(i18n.t(label))
        return box.exec()

    return on_main(show)


class messagebox:  # noqa: N801 - mirrors the tkinter module the logic was written for
    @staticmethod
    def showinfo(title, text):
        _box(QMessageBox.Icon.Information, title, text)

    @staticmethod
    def showwarning(title, text):
        _box(QMessageBox.Icon.Warning, title, text)

    @staticmethod
    def showerror(title, text):
        _box(QMessageBox.Icon.Critical, title, text)

    @staticmethod
    def askyesno(title, text, yes=None, no=None):
        """Yes or no; `yes` / `no` give the buttons names of their own."""
        yes_no = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        names = {QMessageBox.StandardButton.Yes: yes, QMessageBox.StandardButton.No: no}
        names = {k: v for k, v in names.items() if v}
        return _box(QMessageBox.Icon.Question, title, text, yes_no, names) == QMessageBox.StandardButton.Yes


def license_dialog(title, intro, text, accept="Acepto y descargar", decline="Cancelar"):
    """A window with the terms to read (scrollable) and two buttons; True only if the player accepts. Callable from any thread."""

    def show():
        dlg = QDialog()
        title, intro, text, accept, decline = (i18n.t(str(x)) for x in (title, intro, text, accept, decline))
        dlg.setWindowTitle(title)
        dlg.resize(640, 520)
        lay = QVBoxLayout(dlg)
        lab = QLabel(str(intro))
        lab.setWordWrap(True)
        lay.addWidget(lab)
        box = QPlainTextEdit(str(text))
        box.setReadOnly(True)
        lay.addWidget(box, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        no = QPushButton(str(decline))
        yes = QPushButton(str(accept))
        no.clicked.connect(dlg.reject)
        yes.clicked.connect(dlg.accept)
        no.setDefault(True)  # Enter must not accept legal terms
        row.addWidget(no)
        row.addWidget(yes)
        lay.addLayout(row)
        return dlg.exec() == QDialog.DialogCode.Accepted

    return on_main(show)


class filedialog:  # noqa: N801
    @staticmethod
    def askdirectory(title="", initialdir=""):
        return on_main(lambda: QFileDialog.getExistingDirectory(None, title, initialdir)) or ""


def font(size=None, bold=False, family=None, pixel=False):
    f = QFont(family or "Segoe UI")
    if size:
        f.setPointSizeF(size * 0.75 if pixel else size)
    f.setBold(bold)
    return f


class Label(QLabel):
    def __init__(self, text="", color=None, size=10.5, bold=False, family=None, wrap=0, parent=None):
        super().__init__(i18n.t(str(text)), parent)
        self._src = str(text)
        self.setFont(font(size, bold, family))
        self._color = color or PARCHMENT
        self._paint_color()
        if wrap:
            self.setWordWrap(True)
            self.setMaximumWidth(wrap)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

    def _paint_color(self):
        self.setStyleSheet(f"color: {self._color}; background: transparent;")

    def setText(self, text):
        self._src = str(text)
        super().setText(i18n.t(self._src))

    def text(self):
        """The text as the logic wrote it (what is shown may be a translation)."""
        return getattr(self, "_src", super().text())

    def configure(self, **kw):
        if "text" in kw:
            self.setText(str(kw["text"]))
        if "text_color" in kw:
            self._color = kw["text_color"]
            self._paint_color()


class Button(QPushButton):
    """A button painted here (so its colour can follow the mouse softly); `configure` keeps the CTk-like API of the logic."""

    def __init__(self, text="", kind="default", command=None, width=None, height=34, size=10.5, bold=True, parent=None):
        super().__init__(tx(i18n.t(str(text))), parent)
        self._fg, self._hover_c, self._tc = BUTTON_KINDS[kind]
        self._command = None
        self.glow = 0.0  # 0..1, set by qtanim.Glow on the PLAY button
        self.setFont(font(size, bold))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(height)
        if width:
            self.setMinimumWidth(width)
        self._anim = qtanim.hover_animation(self)
        self.configure(command=command)

    def _shown_text(self):
        return self.text().replace("&&", "&")

    def sizeHint(self):
        fm = self.fontMetrics()
        return QSize(max(fm.horizontalAdvance(self._shown_text()) + 34, self.minimumWidth()), max(fm.height() + 10, self.minimumHeight()))

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        shape = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self.isEnabled():
            t = self._hover
            bg = qtanim.mix(QColor(self._fg), QColor(self._hover_c), t)
            border = qtanim.mix(QColor(255, 255, 255, 40), QColor(242, 201, 104, 210), t)
            width = 1.0
            if self.glow:  # the PLAY button breathes in the gold of the palette: a gold edge and a gold line inside it
                bg = qtanim.mix(bg, QColor("#3bb3a4"), self.glow * 0.35)
                border = qtanim.mix(border, QColor(242, 201, 104, 255), self.glow)
                width = 1.0 + 2.0 * self.glow
            text = QColor(self._tc)
        else:
            t, width = 0.0, 1.0
            bg, border, text = QColor(60, 80, 90, 150), QColor(255, 255, 255, 20), QColor(227, 216, 189, 110)
        p.setPen(QPen(border, width))
        p.setBrush(bg)
        p.drawRoundedRect(shape, 10, 10)
        if self.glow > 0.05 and self.isEnabled():
            p.setPen(QPen(QColor(242, 201, 104, round(120 * self.glow)), 1.2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(shape.adjusted(4, 4, -4, -4), 7, 7)
        if t > 0:  # a soft light on the upper half while the mouse is over it
            light = QLinearGradient(0, 0, 0, self.height())
            light.setColorAt(0.0, QColor(255, 255, 255, round(46 * t)))
            light.setColorAt(0.6, QColor(255, 255, 255, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(light)
            p.drawRoundedRect(shape, 10, 10)
        p.setPen(text)
        p.setFont(self.font())
        dy = 1 if (self.isDown() and self.isEnabled()) else 0
        p.drawText(QRectF(self.rect()).adjusted(8, dy, -8, dy), Qt.AlignmentFlag.AlignCenter, self._shown_text())

    def enterEvent(self, event):
        qtanim.hover_to(self, self._anim, 1)
        super().enterEvent(event)

    def leaveEvent(self, event):
        qtanim.hover_to(self, self._anim, 0)
        super().leaveEvent(event)

    def configure(self, **kw):
        if "text" in kw:
            self.setText(tx(i18n.t(str(kw["text"]))))
            self.updateGeometry()
        if "state" in kw:
            self.setEnabled(kw["state"] != "disabled")
        if "fg_color" in kw:
            self._fg = kw["fg_color"]
        if "hover_color" in kw:
            self._hover_c = kw["hover_color"]
        if "text_color" in kw:
            self._tc = kw["text_color"]
        if "command" in kw:
            if self._command is not None:
                try:
                    self.clicked.disconnect(self._command)
                except (RuntimeError, TypeError):
                    pass
            command = kw["command"]
            self._command = (lambda checked=False, c=command: c()) if command else None
            if self._command:
                self.clicked.connect(self._command)
        if any(k in kw for k in ("fg_color", "hover_color", "text_color", "state", "text")):
            self.update()


class Entry(QLineEdit):
    def __init__(self, placeholder="", width=None, height=34, parent=None):
        super().__init__(parent)
        self.setFont(font(10.5))
        self.setPlaceholderText(i18n.t(placeholder))
        self.setMinimumHeight(height)
        if width:
            self.setFixedWidth(width)

    def get(self):
        return self.text()

    def delete(self, first=0, last=None):
        self.clear()

    def insert(self, index, text):
        self.setText(str(text))

    def on_change(self, fn):
        self.textEdited.connect(lambda _t: fn())


class _Toggle(QAbstractButton):
    """A check box or a switch; painted here so the palette and the glass look match."""

    def __init__(self, text="", command=None, switch=False, parent=None):
        super().__init__(parent)
        self.setText(i18n.t(str(text)))
        self.setCheckable(True)
        self.setFont(font(10.5, bold=switch))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._switch = switch
        self._knob = 0.0  # 0 = off, 1 = on: where the knob of a switch is
        self._knob_anim = QVariantAnimation(self)
        self._knob_anim.setDuration(190)
        self._knob_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._knob_anim.valueChanged.connect(self._knob_step)
        self.toggled.connect(self._moved)
        if command:
            self.clicked.connect(lambda checked=False: command())

    def _knob_step(self, v):
        self._knob = float(v)
        self.update()

    def _moved(self, on):
        self._knob_anim.stop()
        if not self._switch or not self.isVisible() or not qtanim.enabled():
            self._knob = 1.0 if on else 0.0
            self.update()
            return
        self._knob_anim.setStartValue(self._knob)
        self._knob_anim.setEndValue(1.0 if on else 0.0)
        self._knob_anim.start()

    def get(self):
        return 1 if self.isChecked() else 0

    def select(self):
        self.setChecked(True)

    def deselect(self):
        self.setChecked(False)

    def sizeHint(self):
        box = 44 if self._switch else 22
        return QSize(box + 10 + self.fontMetrics().horizontalAdvance(self.text()) + 4, 28)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        on = self.isChecked()
        hover = self.underMouse()
        y = (self.height() - 22) / 2
        if self._switch:
            track = QRectF(1, y + 2, 40, 18)
            k = max(0.0, min(1.0, self._knob))
            p.setPen(QPen(QColor(255, 255, 255, 60), 1))
            p.setBrush(qtanim.mix(QColor("#1b3441"), QColor(TEAL), k))
            p.drawRoundedRect(track, 9, 9)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#f2c968" if hover else "#eab84c"))
            x = 3 + 20 * self._knob
            p.drawEllipse(QRectF(x, y + 4, 14, 14))
            left = 52
        else:
            box = QRectF(1, y + 1, 20, 20)
            p.setPen(QPen(QColor(255, 255, 255, 110 if hover else 70), 1))
            p.setBrush(QColor(TEAL if on else "#0d1820"))
            p.drawRoundedRect(box, 6, 6)
            if on:
                pen = QPen(QColor("#fff6e0"), 2.2)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                p.setPen(pen)
                path = QPainterPath()
                path.moveTo(QPointF(6, y + 11.5))
                path.lineTo(QPointF(9.5, y + 15))
                path.lineTo(QPointF(16, y + 7.5))
                p.drawPath(path)
            left = 32
        p.setPen(QColor(PARCHMENT))
        p.setFont(self.font())
        p.drawText(QRectF(left, 0, self.width() - left, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())


def CheckBox(text="", command=None, parent=None):  # noqa: N802
    return _Toggle(text, command, switch=False, parent=parent)


def Switch(text="", command=None, parent=None):  # noqa: N802
    return _Toggle(text, command, switch=True, parent=parent)


def plain(name):
    """A tab's name without the icon that starts it."""
    n = name.strip()
    first = n.split(" ", 1)
    if len(first) == 2 and not first[0].isascii():
        return first[1].strip()
    return n


class _TabButton(QAbstractButton):
    """One choice of a bar of tabs or of a selector: text only, a light under the mouse that fades in and out."""

    def __init__(self, text, size=10.5, bold=True, radius=14, parent=None):
        super().__init__(parent)
        self.setText(i18n.t(str(text)))
        self.setCheckable(True)
        self.setFont(font(size, bold))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._radius = radius
        self._anim = qtanim.hover_animation(self)

    def sizeHint(self):
        return QSize(self.fontMetrics().horizontalAdvance(self.text()) + 38, 34)

    def enterEvent(self, event):
        qtanim.hover_to(self, self._anim, 1)
        super().enterEvent(event)

    def leaveEvent(self, event):
        qtanim.hover_to(self, self._anim, 0)
        super().leaveEvent(event)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.isChecked() and self._hover > 0:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, round(40 * self._hover)))
            p.drawRoundedRect(QRectF(self.rect()), self._radius, self._radius)
        color = QColor("#fff6e0") if self.isChecked() else qtanim.mix(QColor(PARCHMENT), QColor("#ffffff"), self._hover)
        p.setPen(color)
        p.setFont(self.font())
        p.drawText(QRectF(self.rect()), Qt.AlignmentFlag.AlignCenter, self._shown_text())

    def _shown_text(self):
        return self.text().replace("&&", "&")


class PillBar(QFrame):
    """A bar of choices that paints a gold pill under the chosen one; the pill slides to the next choice when it changes."""

    def __init__(self, radius=18, pill_radius=14, parent=None):
        super().__init__(parent)
        self.radius = radius
        self.pill_radius = pill_radius
        self.pill = None  # QRectF, in the bar's coordinates
        self.on_resize = None
        self._slide = QVariantAnimation(self)
        self._slide.setDuration(300)
        self._slide.setEasingCurve(QEasingCurve.Type.OutBack)
        self._slide.valueChanged.connect(self._slide_step)

    def _slide_step(self, rect):
        self.pill = QRectF(rect)
        self.update()

    def move_pill(self, target, animate):
        target = QRectF(target)
        if not animate and self._slide.state() == QVariantAnimation.State.Running:
            self._slide.setEndValue(target)  # the layout moved while sliding (a scroll bar came or went): aim at the new place
            return
        self._slide.stop()
        if animate and qtanim.enabled() and self.pill is not None and self.isVisible():
            self._slide.setStartValue(QRectF(self.pill))
            self._slide.setEndValue(target)
            self._slide.start()
        else:
            self.pill = target
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.on_resize:
            self.on_resize()

    def showEvent(self, event):
        super().showEvent(event)
        if self.on_resize:
            self.on_resize()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(255, 255, 255, 40), 1))
        p.setBrush(QColor(8, 20, 28, 170))
        p.drawRoundedRect(r, self.radius, self.radius)
        if self.pill is not None:
            g = QLinearGradient(0, self.pill.top(), 0, self.pill.bottom())
            g.setColorAt(0.0, QColor(GOLD_HOVER))
            g.setColorAt(1.0, QColor(GOLD))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(g)
            p.drawRoundedRect(self.pill, self.pill_radius, self.pill_radius)


class _TabBar(PillBar):
    def __init__(self, parent=None):
        super().__init__(18, 14, parent)
        self.setObjectName("tabbar")


class Segmented(PillBar):
    def __init__(self, values, command=None, parent=None, size=10.5, bold=False):
        super().__init__(12, 9, parent)
        self.setObjectName("seg")
        self._command = command
        self._buttons = {}
        self._value = None
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)
        for v in values:
            b = _TabButton(tx(v), size, bold, 9)
            b.setMinimumHeight(30)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.clicked.connect(lambda checked=False, v=v: self._clicked(v))
            lay.addWidget(b)
            self._buttons[v] = b
        self.on_resize = lambda: self._place_pill(False)

    def _place_pill(self, animate):
        b = self._buttons.get(self._value)
        if b is not None and b.width() > 0:
            self.move_pill(b.geometry(), animate)

    def set(self, value, animate=False):
        self._value = value
        for v, b in self._buttons.items():
            b.setChecked(v == value)
        self._place_pill(animate)

    def get(self):
        return self._value

    def _clicked(self, value):
        self.set(value, animate=True)
        if self._command:
            self._command(value)


class OptionMenu(QComboBox):
    def __init__(self, values, width=None, parent=None):
        super().__init__(parent)
        self.set_values(values)
        self.setFont(font(10.5))
        self.setMinimumHeight(34)
        if width:
            self.setFixedWidth(width)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def get(self):
        """The chosen entry as the logic wrote it (the list shows a translation)."""
        data = self.currentData()
        return data if data is not None else self.currentText()

    def set_values(self, values):
        self.clear()
        for v in values:
            self.addItem(i18n.t(str(v)), str(v))

    def set(self, text):
        i = self.findData(text)
        if i < 0:
            i = self.findText(text)
        if i >= 0:
            self.setCurrentIndex(i)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(PARCHMENT), 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        cx, cy = self.width() - 18, self.height() / 2
        p.drawLine(QPointF(cx - 4, cy - 2), QPointF(cx, cy + 2))
        p.drawLine(QPointF(cx, cy + 2), QPointF(cx + 4, cy - 2))


class Slider(QSlider):
    def __init__(self, from_, to, command=None, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setRange(int(from_), int(to))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._command = command
        self.valueChanged.connect(self._changed)
        self._quiet = False

    def _changed(self, value):
        if self._command and not self._quiet:
            self._command(value)

    def set(self, value):
        self._quiet = True
        self.setValue(int(round(value)))
        self._quiet = False


class ProgressBar(QWidget):
    def __init__(self, height=10, parent=None):
        super().__init__(parent)
        self.setFixedHeight(height)
        self._value = 0.0

    def set(self, value):
        self._value = max(0.0, min(1.0, float(value)))
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0, 0, self.width(), self.height())
        radius = self.height() / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(8, 20, 28, 190))
        p.drawRoundedRect(r, radius, radius)
        w = max(self.height(), self._value * self.width()) if self._value > 0 else self.height()
        p.setBrush(QColor("#eab84c"))
        p.drawRoundedRect(QRectF(0, 0, w, self.height()), radius, radius)


class LogBox(QPlainTextEdit):
    def __init__(self, height=150, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(font(9.5, family="Consolas"))
        self.setMinimumHeight(height)
        self.setObjectName("log")

    def insert(self, where, text):
        self.moveCursor(self.textCursor().MoveOperation.End)
        self.insertPlainText(i18n.t(text))

    def see(self, where):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def delete(self, first, last=None):
        self.clear()


class TabView(QWidget):
    """A row of tab buttons over a stack of pages."""

    changed = Signal(str)

    def __init__(self, parent=None, show_bar=True):
        super().__init__(parent)
        from PySide6.QtWidgets import QVBoxLayout

        self.animate = False  # the pages fade in once the window is built (set by the app)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.bar = _TabBar()
        self._bar_lay = QHBoxLayout(self.bar)
        self._bar_lay.setContentsMargins(5, 5, 5, 5)
        self._bar_lay.setSpacing(4)
        self.stack = QStackedWidget()
        lay.addWidget(self.bar, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self.stack, 1)
        self._pages = {}
        self._buttons = {}
        self.bar.setVisible(show_bar)
        self.bar.on_resize = self._snap_pill

    def add(self, name, page):
        b = _TabButton(plain(i18n.t(name)))
        b.clicked.connect(lambda checked=False, n=name: self.set(n))
        self._bar_lay.addWidget(b)
        self.stack.addWidget(page)
        self._pages[name.strip()] = page
        self._buttons[name.strip()] = b
        if len(self._pages) == 1:
            self.set(name)

    def set(self, name):
        key = name.strip()
        if key not in self._pages:
            return
        page = self._pages[key]
        moved = self.stack.currentWidget() is not page
        self.stack.setCurrentWidget(page)
        for k, b in self._buttons.items():
            b.setChecked(k == key)
        self._place_pill(animate=moved and self.animate)
        if moved and self.animate:
            qtanim.reveal(page, 260, 18)
        self.changed.emit(key)

    def _place_pill(self, animate):
        key = self.current()
        b = self._buttons.get(key)
        if b is not None and b.width() > 0:
            self.bar.move_pill(b.geometry(), animate)

    def _snap_pill(self):
        self._place_pill(animate=False)

    def current(self):
        """The name (as given to `add`, without the spaces around it) of the page showing."""
        for k, page in self._pages.items():
            if page is self.stack.currentWidget():
                return k
        return None
