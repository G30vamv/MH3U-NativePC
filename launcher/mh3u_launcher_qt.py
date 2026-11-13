"""
MH3U NativePC - launcher for the native PC port of Monster Hunter 3 Ultimate
Author: g30wolff99
The launcher window (PySide6, glass look). What the launcher does lives in core.py.
"""

import os
import queue
import sys
import threading
import webbrowser

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import i18n
import qtanim
import qtmenu
import qtshim
import padmap
import qtmapping
import qttitle
import winfx
from core import (
    APP_VERSION,
    CHEATS,
    MODS,
    mod_enabled,
    DEFAULT_OUT_DIR,
    FPS_LIMITS,
    FPS_NO_LIMIT,
    LauncherLogic,
    fps_limit_label,
    fps_limit_of,
    fps_limit_tips,
    get_assets_dir,
    get_base_dir,
    gpu_thread_mode,
    get_local_ip_addresses,
    list_graphics_cards,
    dxc_installer,
    updater,
)
import qtglass
from qtglass import BackdropWidget, BannerPanel, GlassPanel
from qtshim import (
    CheckBox,
    Button,
    Entry,
    Label,
    LogBox,
    OptionMenu,
    ProgressBar,
    Segmented,
    Slider,
    Switch,
    TabView,
    font,
)

TAB_MAIN = "🎮 Principal"
TAB_INSTALL = "⚙️ Instalación & Dump"
TAB_SETTINGS = "🛠️ Configuración Gráfica"
TAB_CONTROLS = "🕹️ Controles y Mandos"
MAP_NOTE_IDLE = "Elige una acción y pulsa en tu mando el botón que quieres usar para ella. Los cambios valen la próxima vez que pulses JUGAR."
MAP_NOTE_ARMED = "Pulsa en tu mando el botón que quieres usar como {}… (10 s)"
MAP_NOTE_DONE = "Listo: el botón {} del mando hará de {}."
MAP_NOTE_NO_ENGINE = "No se pudo leer el mando: falta mh3u-tools.exe junto al launcher."
TAB_ONLINE = "🌐 Modo Online (Beta)"
TAB_TOOLS = "💾 Partidas & Logs"

STYLE = """
* { font-family: "Segoe UI"; }
QToolTip { background: #0d1820; color: #e3d8bd; border: 1px solid #2b4a58; padding: 4px; }
QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: rgba(120,170,185,110); border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: rgba(212,146,42,200); }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QLineEdit { background: rgba(6,15,21,185); color: #fff6e0; border: 1px solid rgba(255,255,255,45);
            border-radius: 9px; padding: 4px 10px; selection-background-color: #2f9488; }
QLineEdit:focus { border: 1px solid #d4922a; }
QComboBox { background: rgba(6,15,21,185); color: #fff6e0; border: 1px solid rgba(255,255,255,45);
            border-radius: 9px; padding: 4px 34px 4px 10px; }
QComboBox:hover { border: 1px solid #d4922a; }
QComboBox::drop-down { border: none; width: 0; }
QComboBox QAbstractItemView { background: #0d1820; color: #e3d8bd; border: 1px solid #2b4a58;
            selection-background-color: #b8791e; selection-color: #fff6e0; outline: none; }
QSlider::groove:horizontal { height: 6px; background: rgba(6,15,21,200); border-radius: 3px; }
QSlider::sub-page:horizontal { background: #2f9488; border-radius: 3px; }
QSlider::handle:horizontal { background: #eab84c; width: 16px; margin: -6px 0; border-radius: 8px; }
QSlider::handle:horizontal:hover { background: #f2c968; }
QPlainTextEdit#log { background: rgba(5,12,17,205); color: #cfe3e6; border: 1px solid rgba(255,255,255,40);
            border-radius: 10px; padding: 6px; selection-background-color: #2f9488; }
QMessageBox, QDialog { background: #10202a; }
QMessageBox QLabel { color: #e3d8bd; }
QMessageBox QPushButton { background: #2b4a58; color: #fff6e0; border: 1px solid rgba(255,255,255,40);
            border-radius: 8px; padding: 6px 18px; min-width: 70px; }
QMessageBox QPushButton:hover { background: #b8791e; }
"""


def _transparent_scroll(inner):
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QScrollArea.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.viewport().setAutoFillBackground(False)
    inner.setAutoFillBackground(False)
    area.setWidget(inner)
    return area


def _card(level="card", radius=16):
    panel = GlassPanel(level, radius)
    lay = QVBoxLayout(panel)
    lay.setContentsMargins(18, 14, 18, 14)
    lay.setSpacing(8)
    return panel, lay


def _grid_card(level="card", radius=16):
    panel = GlassPanel(level, radius)
    grid = QGridLayout(panel)
    grid.setContentsMargins(18, 14, 18, 14)
    grid.setHorizontalSpacing(12)
    grid.setVerticalSpacing(8)
    return panel, grid


def _hint(text, color="#9db3ba", size=9.5):
    return Label(text, color, size, wrap=0)


def _tip(label, text, *others):
    """The explanation of an option shows when the mouse is over it (on the label and on the widgets in `others`); the label starts
    with a lightbulb so people know it is there. A leading icon of the label (a stethoscope, a crown...) is replaced by the bulb."""
    text = text.removeprefix("💡").strip()  # some texts already carry the bulb of the old inline hints
    for w in (label,) + others:
        w.setToolTip(qtanim.tip_html(text))
    shown = label.text()
    if not shown.startswith("💡"):
        first = shown.split(" ", 1)
        if len(first) == 2 and not first[0].isascii() and not first[0].isalnum():
            shown = first[1]
        label.setText("💡 " + shown)
        if hasattr(label, "updateGeometry"):
            label.updateGeometry()


class Window(QWidget):
    def __init__(self, app):
        super().__init__()
        self._app = app
        # no native frame: the title bar is drawn inside the window (qttitle)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowSystemMenuHint
        )
        qttitle.install_grips(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        qttitle.place_grips(self)

    def changeEvent(self, event):
        super().changeEvent(event)
        # coming back from the taskbar: the window appears softly (it went down softly, see qtanim.minimize_window)
        if (
            event.type() == QEvent.Type.WindowStateChange
            and bool(event.oldState() & Qt.WindowState.WindowMinimized)
            and not self.isMinimized()
        ):
            qtanim.fade_window_in(self, 170)
        if hasattr(self._app, "titlebar"):
            self._app.titlebar.sync()
            qttitle.place_grips(self)

    def closeEvent(self, event):
        self._app.on_app_close()
        event.accept()


class MH3ULauncherApp(LauncherLogic):
    def __init__(self, qapp):
        self.qapp = qapp
        self.assets_dir = get_assets_dir()
        self.config = self.load_config()
        i18n.set_language(self.language())  # before any text is made: the window is built in the chosen language
        qtanim.set_user_choice(self.config.get("animations", True))
        self.is_compiling = False
        self.is_running = False
        self.is_downloading_toolchain = False
        self.game_process = None
        self.ui_queue = queue.Queue()
        self.server_process = None

        self.window = Window(self)
        self.window.setWindowTitle(f"MH3U NativePC {APP_VERSION}")
        icon_path = os.path.join(self.assets_dir, "app_icon.ico")
        if os.path.exists(icon_path):
            self.window.setWindowIcon(QIcon(icon_path))
        self.window.resize(1180, 840)
        self.window.setMinimumSize(980, 680)
        # in the middle of the main screen (Windows would open it on the screen the mouse is on), and its dialogs over it
        qtshim.center_on_primary(self.window)
        qtshim.set_main_window(self.window)

        self.acrylic = bool(self.config.get("acrylic", False)) and winfx.acrylic_available()
        if self.acrylic:
            self.window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.backdrop = BackdropWidget(None, self.window, opacity=0.50 if self.acrylic else 1.0)
        qtglass.SEE_THROUGH = self.acrylic
        outer = QVBoxLayout(self.window)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.backdrop)
        self.build_ui()

        self.poll = QTimer()
        self.poll.timeout.connect(self._process_ui_queue)
        self.poll.start(50)
        self.refresh_status()
        if updater:
            # the backups of older updates piled up next to the launcher: only the last one stays
            threading.Thread(target=updater.prune_backups, args=(get_base_dir(),), daemon=True).start()
        if updater and self.config.get("auto_check_updates", True):
            QTimer.singleShot(4000, lambda: self.check_for_updates(silent=True))

    # ---- what the logic expects from a window -------------------------------------------------
    def after(self, ms, fn):
        if threading.current_thread() is threading.main_thread():
            QTimer.singleShot(ms, fn)
        else:
            self.ui_queue.put(("call", (ms, fn)))

    def destroy(self):
        self.poll.stop()
        self.window.hide()
        self.qapp.quit()

    def clipboard_clear(self):
        self.qapp.clipboard().clear()

    def clipboard_append(self, text):
        self.qapp.clipboard().setText(text)

    def show(self):
        self.window.show()
        # the window handle exists once it is shown
        winfx.style_window(self.window.winId(), self.acrylic)

    def sync_widgets_from_config(self):
        """The game's overlay changed settings: show them (called from the thread that launches the game or from the window)."""
        c = self.config
        scale_map = {"0.5": "0.5x", "0.75": "0.75x", "1": "1x", "1.5": "1.5x", "2": "2x", "3": "3x", "4": "4x"}
        present_map = {"mailbox": "Mailbox (Fast-Sync)", "fifo": "VSync Clásico (Fifo)", "immediate": "Desactivado (OFF)"}
        upscaler_map = {"fsr": "FSR 1.0 (EASU + RCAS)", "cas": "AMD CAS (Solo Nitidez)", "off": "Desactivado (Nativo)"}
        self.opt_scale.set(scale_map.get(str(c.get("scale", "2")), "2x"))
        self.opt_present.set(present_map.get(c.get("present_mode", "mailbox"), "Mailbox (Fast-Sync)"))
        self.opt_fps_limit.set(fps_limit_label(fps_limit_of(c)))
        self.opt_upscaler.set(upscaler_map.get(c.get("upscaler", "fsr"), "FSR 1.0 (EASU + RCAS)"))
        sharp = c.get("fsr_sharpness", 75)
        self.slider_sharpness.set(sharp)
        self.lbl_sharpness_val.configure(text=f"{sharp}%")
        if c.get("fps", False):
            self.chk_fps.select()
        else:
            self.chk_fps.deselect()
        self.seg_language.set({"es": "Español", "en": "English"}.get(c.get("ui_language", "auto"), "Automático"))
        stick = int(c.get("right_stick_sens", 100))
        self.slider_stick.set(stick)
        self.lbl_stick_val.configure(text=f"{stick}%")

    def refresh_dxc_button(self):
        """Shown only with DirectX 12 chosen and the helper not installed yet."""
        show = self.config.get("gfx_backend", "vulkan") == "dx12" and not (dxc_installer and dxc_installer.installed(get_base_dir()))
        self.btn_install_dxc.setVisible(bool(show and dxc_installer))
        self.btn_install_dxc.configure(state="normal")

    def _load_graphics_cards(self):
        """The cards are asked of Windows in the background (about a second) and then put in the list."""
        self.ui_queue.put(("gpu_list", list_graphics_cards()))

    def _fill_graphics_cards(self, cards):
        saved = str(self.config.get("gfx_adapter", "") or "")
        names = list(cards)
        if saved and saved not in names:
            names.append(saved)  # a card that is not there now stays chosen
        self.opt_adapter.blockSignals(True)
        self.opt_adapter.set_values(["Automática (la mejor)"] + names)
        self.opt_adapter.set(saved or "Automática (la mejor)")
        self.opt_adapter.blockSignals(False)

    def on_acrylic_toggled(self):
        self.config["acrylic"] = bool(self.chk_acrylic.get())
        self.save_config()
        qtshim.messagebox.showinfo("Efecto Acrylic", "El cambio se aplicará la próxima vez que abras el launcher.")

    # ---- messages from other threads -----------------------------------------------------------
    def _process_ui_queue(self):
        try:
            while not self.ui_queue.empty():
                kind, data = self.ui_queue.get_nowait()
                if kind == "log":
                    self.txt_log.insert("end", data + "\n")
                    self.txt_log.see("end")
                elif kind == "server_log":
                    self.txt_server_log.insert("end", data + "\n")
                    self.txt_server_log.see("end")
                elif kind == "server_status":
                    self.lbl_server_status.configure(**data)
                elif kind == "ping_result":
                    success, elapsed_ms, detail = data
                    self._on_ping_result(success, elapsed_ms, detail)
                elif kind == "progress":
                    self.progress_bar.set(data)
                elif kind == "btn_compile":
                    self.btn_compile_action.configure(**data)
                elif kind == "btn_download":
                    self.btn_download_toolchain.configure(**data)
                elif kind == "gpu_list":
                    self._fill_graphics_cards(data)
                elif kind == "dxc_button":
                    self.refresh_dxc_button()
                elif kind == "tab":
                    self.tabview.set(data)
                elif kind == "refresh":
                    self.refresh_status()
                elif kind == "info":
                    qtshim.messagebox.showinfo(data[0], data[1])
                elif kind == "error":
                    qtshim.messagebox.showerror(data[0], data[1])
                elif kind == "warning":
                    qtshim.messagebox.showwarning(data[0], data[1])
                elif kind == "update_state":
                    self.lbl_update_status.configure(**data)
                elif kind == "update_btn":
                    self.btn_update.configure(**data)
                elif kind == "update_prompt":
                    self._prompt_update(*data)
                elif kind == "call":
                    ms, fn = data
                    QTimer.singleShot(ms, fn)
        except Exception as e:
            print(f"UI Queue error: {e}")

    # ---- window --------------------------------------------------------------------------------
    def build_ui(self):
        root = QVBoxLayout(self.backdrop)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        icon_path = os.path.join(self.assets_dir, "app_icon.ico")
        self.titlebar = qttitle.TitleBar(
            self.window,
            f"MH3U NativePC {APP_VERSION}",
            icon_path if os.path.exists(icon_path) else None,
        )
        root.addWidget(self.titlebar)
        self._build_menu()

        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(20, 2, 20, 12)
        content_lay.setSpacing(12)
        root.addWidget(content, 1)
        self.header = self.create_header()
        content_lay.addWidget(self.header)

        self.tabview = TabView()
        content_lay.addWidget(self.tabview, 1)

        self.tabview.add(TAB_MAIN, self.setup_tab_main())
        self.tabview.add(TAB_INSTALL, self.setup_tab_install())
        self.tabview.add(TAB_SETTINGS, self.setup_tab_settings())
        self.tabview.add(TAB_CONTROLS, self.setup_tab_controls())
        self.tabview.add(TAB_ONLINE, self.setup_tab_online())
        self.tabview.add(TAB_TOOLS, self.setup_tab_tools())
        # Radmin/Tailscale/ZeroTier may have connected after the launcher opened
        self.tabview.changed.connect(lambda key: key == TAB_ONLINE.strip() and self.refresh_local_ips())
        self.tabview.changed.connect(self._on_tab_changed)
        self.tabview.animate = True  # from here on the pages fade in when they change

        self.footer = self.create_footer()
        content_lay.addWidget(self.footer)

    # ---- gear menu, page bar, animations ---------------------------------------------------------
    def _build_menu(self):
        """The gear: the options of the launcher itself, wherever they used to be. (Not the game's options: those stay in their tabs.)"""
        self.menu = qtmenu.SettingsMenu(self.window)
        gear = self.titlebar.btn_menu

        def closed():
            gear.menu_open = False
            gear.update()

        self.menu.on_hidden = closed
        self.menu.add_title("IDIOMA / LANGUAGE")
        self.seg_language = self.menu.add_choice(
            ["Automático", "Español", "English"],
            {"es": "Español", "en": "English"}.get(self.config.get("ui_language", "auto"), "Automático"),
            self.on_ui_language_changed,
        )
        self.menu.add_separator()
        self.menu.add_title("OPCIONES DEL LAUNCHER")
        self.sw_animations = self.menu.add_switch(
            "💡 Animaciones",
            bool(self.config.get("animations", True)),
            self.on_animations_toggled,
            qtanim.tip_html(
                "Suaviza los cambios de pestaña, los botones y la entrada del launcher. Se desactivan solas si Windows tiene "
                "las animaciones apagadas."
            ),
        )
        self.chk_acrylic = self.menu.add_switch(
            "💡 Efecto Acrylic de la ventana",
            bool(self.config.get("acrylic", False)),
            self.on_acrylic_toggled,
            qtanim.tip_html(
                "El escritorio se transparenta detrás de la ventana. Solo funciona en Windows 11; si usas Windows 10, déjalo "
                "desactivado. Reinicia el launcher para ver el cambio."
            ),
        )
        self.chk_discord_rpc = self.menu.add_switch(
            "💡 Estado en Discord",
            bool(self.config.get("discord_rpc", True)),
            self.save_settings_from_ui,
            qtanim.tip_html("Rich Presence: muestra en tu Discord a qué juegas y el nombre de tu cazador."),
        )
        self.sw_auto_updates = self.menu.add_switch(
            "💡 Buscar actualizaciones al abrir",
            bool(self.config.get("auto_check_updates", True)),
            self.on_auto_updates_toggled,
            qtanim.tip_html("Al abrir el launcher comprueba si hay una versión nueva y te avisa. No instala nada sin preguntarte."),
        )
        self.chk_lto = self.menu.add_switch(
            "💡 Compilación optimizada (LTO)",
            bool(self.config.get("build_lto", False)),
            self.on_lto_toggled,
            qtanim.tip_html(
                "Optimiza más el juego al compilarlo. La compilación tarda bastante más y puede dar algunos FPS extra en procesadores "
                "poco potentes (no está medido; en un PC rápido no se nota). Vale para la próxima vez que compiles el juego."
            ),
        )
        self.menu.add_separator()
        self.menu.add_action("🔄  Buscar actualizaciones ahora", self.on_update_button)
        gear.clicked.connect(self.open_menu)

    def open_menu(self):
        if self.menu.isVisible():
            self.menu.close()
            return
        self.titlebar.btn_menu.menu_open = True
        self.titlebar.btn_menu.update()
        self.menu.popup_below(self.titlebar.btn_menu)

    def on_auto_updates_toggled(self):
        self.config["auto_check_updates"] = bool(self.sw_auto_updates.get())
        self.save_config()

    def on_animations_toggled(self):
        on = bool(self.sw_animations.get())
        self.config["animations"] = on
        self.save_config()
        qtanim.set_user_choice(on)
        glow = getattr(self, "_glow", None)
        if glow:
            glow.refresh()

    def _glow_allowed(self):
        """The PLAY button breathes only while it is useful: window in front, game not running, on the main page."""
        w = self.window
        return (
            qtanim.enabled()
            and not self.is_running
            and self.btn_play.isEnabled()
            and w.isVisible()
            and w.isActiveWindow()
            and not w.isMinimized()
            and self.tabview.current() == TAB_MAIN.strip()
        )

    def create_header(self):
        header = BannerPanel(os.path.join(self.assets_dir, "banner.png"), "card", 20)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(330, 14, 18, 14)
        lay.setSpacing(16)

        text = QVBoxLayout()
        text.setSpacing(2)
        title = Label("MONSTER HUNTER 3 ULTIMATE", "#f2b94b", 24, bold=True, family="Georgia")
        sub = Label(
            f"MH3U NativePC {APP_VERSION} • Vulkan / DX12 / LTO • Puerto Tanzia", "#b9ccd2", 11
        )
        text.addWidget(title)
        text.addWidget(sub)
        lay.addLayout(text, 1)

        badge = GlassPanel("inset", 14)
        blay = QVBoxLayout(badge)
        blay.setContentsMargins(14, 8, 14, 8)
        blay.setSpacing(4)
        blay.addWidget(Label(f"🛠️ Versión {APP_VERSION}", "#eab84c", 10, bold=True), 0, Qt.AlignmentFlag.AlignHCenter)
        if updater:
            self.btn_update = Button("⟳  Buscar actualizaciones", "teal", self.on_update_button, width=200, height=30, size=10)
            self.lbl_update_status = Label("", "#9db3ba", 9.5)
            self.lbl_update_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_update_status.setWordWrap(True)
            self.lbl_update_status.setFixedWidth(200)
            blay.addWidget(self.btn_update)
            blay.addWidget(self.lbl_update_status)
        lay.addWidget(badge)
        return header

    def create_footer(self):
        """Credits line straight on the background, with no pane behind it."""
        footer = QWidget()
        lay = QHBoxLayout(footer)
        lay.setContentsMargins(6, 0, 6, 0)
        lay.addWidget(Label(f"Monster Hunter 3 Ultimate (Wii U) • MH3U NativePC | {APP_VERSION}", "#a9bec6", 9.5))
        lay.addStretch(1)
        lay.addWidget(Label("Launcher desarrollado por g30wolff99", "#e3d8bd", 9.5, bold=True))
        return footer

    # ---- tab 1 ---------------------------------------------------------------------------------
    def setup_tab_main(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(12)

        status, sg = _grid_card("card")
        sg.addWidget(Label("ESTADO DEL JUEGO:", None, 11, bold=True), 0, 0)
        self.lbl_main_status = Label("Verificando instalación...", "#eab84c", 11, bold=True)
        sg.addWidget(self.lbl_main_status, 0, 1)
        sg.addWidget(Label("MODO ONLINE:", None, 10.5, bold=True), 1, 0)
        self.lbl_main_online_status = Label("Comprobando...", "#e3d8bd", 10.5, bold=True)
        sg.addWidget(self.lbl_main_online_status, 1, 1)
        sg.setColumnStretch(1, 1)
        lay.addWidget(status)

        self.btn_play = Button("⚔️  JUGAR MONSTER HUNTER 3 ULTIMATE", "teal", self.launch_game, height=64, size=16)
        self.btn_play.setMinimumWidth(self.btn_play.fontMetrics().horizontalAdvance(self.btn_play.text()) + 150)
        lay.addWidget(self.btn_play, 0, Qt.AlignmentFlag.AlignHCenter)
        self._glow = qtanim.Glow(self.btn_play, self._glow_allowed)

        row = QHBoxLayout()
        row.setSpacing(12)
        quick, ql = _card("card")
        ql.addWidget(Label("Ajustes Rápidos Activos", "#4fc3d6", 11.5, bold=True))
        # the logic updates these labels when a setting changes; the panel below shows the same, and more
        self.lbl_quick_scale = Label("")
        self.lbl_quick_pad = Label("")
        self.lbl_quick_mods = Label("")
        self.lbl_quick_backend = Label("")
        self.lbl_quick_online = Label("Online: Comprobando...")
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(9)
        self._quick_items = [
            ("scale", "Resolución interna"), ("upscaler", "Reescalado"), ("present", "VSync"), ("backend", "API gráfica"),
            ("window", "Pantalla"), ("fps", "Contador de FPS"), ("input", "Entrada"), ("layout", "Disposición del mando"),
            ("sens", "Sensibilidad de cámara"), ("mods", "Mods"), ("audio", "Audio"), ("fpslimit", "Límite de FPS"),
            ("online", "Online"), ("discord", "Discord Rich Presence"),
        ]
        self._quick_labels = {}
        self._quick_last = {}
        for i, (key, name) in enumerate(self._quick_items):
            r, c = divmod(i, 2)
            grid.addWidget(Label(name, "#9db3ba", 10), r, c * 2)
            value = Label("", "#e3d8bd", 10, bold=True)
            value.setWordWrap(True)
            grid.addWidget(value, r, c * 2 + 1)
            self._quick_labels[key] = value
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        ql.addLayout(grid)
        ql.addStretch(1)
        row.addWidget(quick, 3)
        self.quick_timer = QTimer()
        self.quick_timer.timeout.connect(self.refresh_quick)
        self.quick_timer.start(400)
        QTimer.singleShot(0, self.refresh_quick)

        actions, al = _card("card")
        al.addWidget(Label("Acciones Frecuentes", "#4fc3d6", 11.5, bold=True))
        al.addWidget(Button("📦 Seleccionar / Cambiar Carpeta del Dump", "default", lambda: self.tabview.set(TAB_INSTALL)))
        al.addWidget(Button("🔨 Recompilar Librería del Juego", "default", self.start_build_process))
        al.addWidget(Button("📂 Abrir Carpeta de Guardado", "default", self.open_save_folder))
        al.addWidget(Label("¿Juegas con mando o teclado?"))
        self.opt_keyboard = Segmented(["Mando", "Teclado"], self.on_keyboard_changed)
        self.opt_keyboard.set("Teclado" if self.config.get("keyboard_controls", True) else "Mando")
        al.addWidget(self.opt_keyboard)
        row.addWidget(actions, 2)
        lay.addLayout(row, 1)

        tip, tl = _grid_card("inset", 14)
        tl.addWidget(Label("💡", None, 16), 0, 0)
        text = Label(
            "Consejo para Puerto Tanzia (Offline): Para jugar las misiones de la taberna (Rango Bajo, Alto y G) en solitario, "
            "habla con el marinero del barco y elige 'Puerto Tanzia -> Individual -> Marina o Taberna'. "
            "No selecciones 'Multijugador' si estás jugando sin conexión.",
            "#e3d8bd",
            10,
        )
        text.setWordWrap(True)
        tl.addWidget(text, 0, 1)
        tl.setColumnStretch(1, 1)
        lay.addWidget(tip)
        return page

    def refresh_quick(self):
        """Read-only summary of the launcher's main settings; follows the configuration as it changes."""
        c = self.config
        green, grey, gold, plain = "#7fcfa6", "#9db3ba", "#eab84c", "#e3d8bd"

        def yes(on, text_on="Sí", text_off="No"):
            return (text_on, green) if on else (text_off, grey)

        scale = {"0.5": "0.5x", "0.75": "0.75x", "1": "1x", "1.5": "1.5x", "2": "2x (1440p)", "3": "3x", "4": "4x (5K)"}.get(str(c.get("scale", "2")), "2x (1440p)")
        sharp = int(c.get("fsr_sharpness", 75))
        upscaler = {"fsr": f"FSR 1.0 · nitidez {sharp} %", "cas": f"AMD CAS · nitidez {sharp} %"}.get(c.get("upscaler", "fsr"), "Desactivado")
        present = {"mailbox": "Mailbox (Fast-Sync)", "fifo": "VSync clásico (Fifo)", "immediate": "Desactivado"}.get(c.get("present_mode", "mailbox"), "Mailbox")
        mods = []
        mods += [m["label"].split(" en pantalla")[0] for m in MODS if mod_enabled(c, m["id"])]
        audio = [n for k, n in (("audio", "Sonido"), ("audio_fx", "Efectos")) if c.get(k, True)]
        online = self.lbl_quick_online.text().replace("Online:", "").strip() or "Comprobando..."
        online_color = green if "Activ" in online and "Desactiv" not in online else grey
        values = {
            "scale": (scale, gold),
            "upscaler": (upscaler, gold if c.get("upscaler", "fsr") != "off" else grey),
            "present": (present, plain),
            "backend": ("DirectX 12" if c.get("gfx_backend") == "dx12" else "Vulkan", plain),
            "window": ("Completa sin bordes", plain) if c.get("fullscreen", True) else ("En ventana", plain),
            "fps": yes(c.get("fps", False)),
            "input": ("Teclado y ratón", plain) if c.get("keyboard_controls", True) else ("Mando", plain),
            "layout": ("Xbox (A abajo)" if c.get("pad_layout") == "xbox" else "Nintendo (B abajo)", plain),
            "sens": (str(int(round(float(c.get("mouse_sensitivity", 0.0008)) * 10000))), plain),
            "mods": (", ".join(mods), green) if mods else ("Desactivados", grey),
            "audio": (" · ".join(audio), green) if audio else ("Silenciado", grey),
            "fpslimit": (fps_limit_label(fps_limit_of(c)), gold if fps_limit_of(c) else grey),
            "online": (online, online_color),
            "discord": yes(c.get("discord_rpc", True), "Activado", "Desactivado"),
        }
        for key, (text, color) in values.items():
            if self._quick_last.get(key) != (text, color):
                self._quick_last[key] = (text, color)
                self._quick_labels[key].configure(text=text, text_color=color)

    # ---- tab 2 ---------------------------------------------------------------------------------
    def setup_tab_install(self):
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(4, 4, 8, 4)
        lay.setSpacing(12)

        folder, fl = _card("card")
        fl.addWidget(Label("Carpeta de Dumps de Monster Hunter 3 Ultimate (USA):", None, 10.5, bold=True))
        path_row = QHBoxLayout()
        self.entry_games_path = Entry("Ej: D:\\Juegos\\WiiU\\Monster Hunter 3 Ultimate Dumps")
        if self.config.get("games_dir"):
            self.entry_games_path.insert(0, self.config["games_dir"])
        path_row.addWidget(self.entry_games_path, 1)
        path_row.addWidget(Button("Examinar...", "gold", self.browse_games_folder, width=110))
        fl.addLayout(path_row)
        lay.addWidget(folder)

        badges, bl = _grid_card("card")
        self.lbl_badge_base = Label("⚪ Juego Base USA (0005000010118300): No detectado", "#e3d8bd", 10, bold=True)
        self.lbl_badge_update = Label("⚪ Actualización v32 USA (0005000e10118300): No detectada", "#e3d8bd", 10, bold=True)
        self.lbl_badge_compiler = Label("⚪ Compilador Clang: Comprobando...", "#e3d8bd", 10, bold=True)
        bl.addWidget(self.lbl_badge_base, 0, 0)
        bl.addWidget(self.lbl_badge_update, 0, 1)
        bl.addWidget(self.lbl_badge_compiler, 1, 0, 1, 2)
        lay.addWidget(badges)

        build, bx = _card("card")
        btn_row = QHBoxLayout()
        self.btn_compile_action = Button("⚡ Traducir y Compilar Port (Crear game.dll)", "ember", self.start_build_process, height=44, size=12)
        btn_row.addWidget(self.btn_compile_action, 1)
        self.btn_download_toolchain = Button("⬇️ Descargar Clang Portátil", "default", self.start_download_toolchain, width=200, height=44)
        btn_row.addWidget(self.btn_download_toolchain)
        bx.addLayout(btn_row)
        self.progress_bar = ProgressBar(10)
        bx.addWidget(self.progress_bar)
        bx.addWidget(Label("Registro del compilador en tiempo real:", None, 10))
        self.txt_log = LogBox(240)
        bx.addWidget(self.txt_log)
        lay.addWidget(build)
        lay.addStretch(1)
        return _transparent_scroll(inner)

    # ---- tab 3 ---------------------------------------------------------------------------------
    def setup_tab_settings(self):
        inner = QWidget()
        cols = QHBoxLayout(inner)
        cols.setContentsMargins(4, 4, 8, 4)
        cols.setSpacing(12)

        gfx, g = _card("card")
        g.addWidget(Label("Opciones Gráficas", "#4fc3d6", 12.5, bold=True))
        lbl_scale = Label("Escala de Resolución Interna:", None, 10.5, bold=True)
        g.addWidget(lbl_scale)
        self.opt_scale = Segmented(["0.5x", "0.75x", "1x", "1.5x", "2x", "3x", "4x"], self.on_scale_changed)
        scale_map = {
            "0.5": "0.5x", "0.75": "0.75x", "1": "1x", "1.5": "1.5x", "2": "2x", "3": "3x", "4": "4x",
            "1x (Nativo)": "1x", "2x (1440p/4K)": "2x", "3x (Super)": "3x", "4x (Ultra)": "4x",
        }
        self.opt_scale.set(scale_map.get(str(self.config.get("scale", "2")), "2x"))
        g.addWidget(self.opt_scale)
        _tip(
            lbl_scale,
            "Resolución a la que se dibuja el juego (base Wii U 1280x720 × factor); es independiente del reescalado FSR.\n"
            "0.5x y 0.75x: menos píxeles que la consola (más FPS en equipos lentos, imagen más blanda).\n1.5x (1080p): un paso intermedio.\n1x (720p): nativo, 60 FPS seguros.\n2x (1440p): 4x píxeles, nítido en monitores 1080p/1440p.\n"
            "3x (4K UHD): 9x píxeles.\n4x (5K): 16x píxeles (GPUs potentes).",
            self.opt_scale,
        )

        lbl_fps_limit = Label("Límite de FPS:", None, 10.5, bold=True)
        g.addWidget(lbl_fps_limit)
        self.opt_fps_limit = qtmenu.DropList(
            [fps_limit_label(v) for v in FPS_LIMITS] + [FPS_NO_LIMIT], self.on_fps_limit_changed, fps_limit_tips()
        )
        self.opt_fps_limit.set(fps_limit_label(fps_limit_of(self.config)))
        g.addWidget(self.opt_fps_limit)
        _tip(
            lbl_fps_limit,
            "El tope de fotogramas por segundo, en múltiplos de los 30 de la consola. Con un tope tu PC trabaja menos y, al jugar online, "
            "todos van a un ritmo parecido. Con más FPS el juego se ve más fluido, pero no va más rápido. También se cambia dentro del juego (F2).",
            self.opt_fps_limit,
        )

        self.chk_fullscreen = CheckBox("Pantalla Completa sin bordes (Borderless)", self.save_settings_from_ui)
        if self.config.get("fullscreen", True):
            self.chk_fullscreen.select()
        g.addWidget(self.chk_fullscreen)
        self.chk_fps = CheckBox("Mostrar Contador de FPS en pantalla", self.save_settings_from_ui)
        if self.config.get("fps", False):
            self.chk_fps.select()
        g.addWidget(self.chk_fps)
        self.chk_texture_dump = CheckBox("Guardar las texturas del juego (para hacer paquetes)", self.save_settings_from_ui)
        if self.config.get("texture_dump", False):
            self.chk_texture_dump.select()
        g.addWidget(self.chk_texture_dump)
        _tip(
            self.chk_texture_dump,
            "Mientras juegas, cada textura se guarda una vez como archivo DDS en la carpeta texture_dump, con el nombre que debe tener "
            "su sustituta. Para cambiar una textura, edítala y copia el DDS a la carpeta de texturas con ese mismo nombre (basta con "
            "que empiece por esas 8 cifras). Úsalo solo para preparar paquetes: escribe en disco mientras juegas.",
        )
        self.btn_textures_folder = Button("📂 Abrir carpeta de paquetes de texturas", "default", self.open_textures_folder, height=34)
        _tip(
            self.btn_textures_folder,
            "Los archivos DDS que pongas aquí (también en subcarpetas) sustituyen a las texturas del juego en la siguiente partida. "
            "Formatos: BC1, BC3, BC7 o RGBA de 32 bits.",
        )
        g.addWidget(self.btn_textures_folder, 0, Qt.AlignmentFlag.AlignLeft)
        lbl_parallel = Label("Gráficos en paralelo (más FPS):", None, 10.5, bold=True)
        g.addWidget(lbl_parallel)
        # an older config file may hold "on" (forced on): that choice is shown, but the window no longer offers it
        parallel = gpu_thread_mode(self.config)
        self.opt_gpu_thread = Segmented(
            ["Automático (recomendado)", "Apagado"] + (["Siempre activado"] if parallel == "on" else []), self.on_gpu_thread_changed
        )
        self.opt_gpu_thread.set({"on": "Siempre activado", "off": "Apagado"}.get(parallel, "Automático (recomendado)"))
        g.addWidget(self.opt_gpu_thread)
        _tip(
            lbl_parallel,
            "Reparte el trabajo gráfico entre varios núcleos del procesador para subir los FPS, sobre todo en procesadores lentos.\n"
            "Automático (recomendado): se activa solo con tarjetas NVIDIA y AMD; con Intel se queda apagado (aún sin probar).\n"
            "Apagado: úsalo si ves parpadeos o cosas que desaparecen, o si el juego se congela.",
            self.opt_gpu_thread,
        )

        lbl_backend = Label("Motor Gráfico (Backend):", None, 10.5, bold=True)
        g.addWidget(lbl_backend)
        self.opt_backend = Segmented(["Vulkan (Recomendado)", "DirectX 12 (DX12)"], self.on_backend_changed)
        self.opt_backend.set("DirectX 12 (DX12)" if self.config.get("gfx_backend", "vulkan") == "dx12" else "Vulkan (Recomendado)")
        g.addWidget(self.opt_backend)
        _tip(lbl_backend, "Usa DirectX 12 si tienes gráfica integrada Intel o notas tirones con Vulkan.", self.opt_backend)
        # only DirectX 12 gains from Microsoft's shader compiler, so its button shows up there and nowhere else
        self.btn_install_dxc = Button("⬇ Instalar ayuda de DirectX 12 (Microsoft)", "default", self.start_install_dxc, height=34)
        _tip(
            self.btn_install_dxc,
            "Descarga dos archivos de Microsoft (dxcompiler.dll y dxil.dll) para que DirectX 12 prepare los shaders en segundos en vez de "
            "decenas de segundos. Antes verás sus condiciones de licencia y tendrás que aceptarlas.",
        )
        g.addWidget(self.btn_install_dxc, 0, Qt.AlignmentFlag.AlignLeft)
        self.refresh_dxc_button()

        lbl_card = Label("Tarjeta gráfica:", None, 10.5, bold=True)
        g.addWidget(lbl_card)
        saved_card = str(self.config.get("gfx_adapter", "") or "")
        self.opt_adapter = OptionMenu(["Automática (la mejor)"] + ([saved_card] if saved_card else []))
        self.opt_adapter.set(saved_card or "Automática (la mejor)")
        self.opt_adapter.currentTextChanged.connect(lambda _text: self.on_adapter_changed(self.opt_adapter.get()))
        g.addWidget(self.opt_adapter)
        _tip(
            lbl_card,
            "Con una gráfica integrada y otra dedicada (o en portátiles) puedes elegir con cuál se dibuja el juego. "
            "Automática elige la más potente. Si la elegida no se encuentra, se usa la automática.",
            self.opt_adapter,
        )
        threading.Thread(target=self._load_graphics_cards, daemon=True).start()

        lbl_vsync = Label("Sincronización Vertical (VSync):", None, 10.5, bold=True)
        g.addWidget(lbl_vsync)
        self.opt_present = Segmented(["Mailbox (Fast-Sync)", "VSync Clásico (Fifo)", "Desactivado (OFF)"], self.on_present_changed)
        present_map = {"mailbox": "Mailbox (Fast-Sync)", "fifo": "VSync Clásico (Fifo)", "immediate": "Desactivado (OFF)"}
        self.opt_present.set(present_map.get(self.config.get("present_mode", "mailbox"), "Mailbox (Fast-Sync)"))
        g.addWidget(self.opt_present)
        _tip(lbl_vsync, "Mailbox evita tirones y reduce la latencia al mínimo sin cortes de pantalla.", self.opt_present)

        lbl_upscaler = Label("Tecnología de Reescalado & Nitidez:", None, 10.5, bold=True)
        g.addWidget(lbl_upscaler)
        self.opt_upscaler = Segmented(["FSR 1.0 (EASU + RCAS)", "AMD CAS (Solo Nitidez)", "Desactivado (Nativo)"], self.on_upscaler_changed)
        upscaler = self.config.get("upscaler", "fsr")
        self.opt_upscaler.set({"cas": "AMD CAS (Solo Nitidez)", "off": "Desactivado (Nativo)"}.get(upscaler, "FSR 1.0 (EASU + RCAS)"))
        g.addWidget(self.opt_upscaler)
        _tip(
            lbl_upscaler,
            "FSR escala la imagen solo si la resolución interna es menor que la de tu ventana (p. ej. 1x = 720p en un monitor 1080p o 1440p). "
            "Con 2x o más en un monitor 1080p ya hay de sobra y solo se aplica el afilado.",
            self.opt_upscaler,
        )

        sharp, sl = _card("inset", 12)
        head = QHBoxLayout()
        head.addWidget(Label("Nitidez de Reescalado (FSR / CAS):", None, 10, bold=True))
        head.addStretch(1)
        raw_sharp = self.config.get("fsr_sharpness", 75)
        self.lbl_sharpness_val = Label(f"{raw_sharp}%", "#4fc3d6", 10, bold=True)
        head.addWidget(self.lbl_sharpness_val)
        sl.addLayout(head)
        self.slider_sharpness = Slider(20, 100, self.on_fsr_sharpness_changed)
        self.slider_sharpness.set(raw_sharp)
        sl.addWidget(self.slider_sharpness)
        g.addWidget(sharp)

        g.addWidget(Label("Audio & Efectos", None, 10.5, bold=True))
        self.chk_audio = CheckBox("Sonido Activado (CPAL WASAPI)", self.save_settings_from_ui)
        if self.config.get("audio", True):
            self.chk_audio.select()
        g.addWidget(self.chk_audio)
        self.chk_audio_fx = CheckBox("Efectos de Reverberación y Filtros", self.save_settings_from_ui)
        if self.config.get("audio_fx", True):
            self.chk_audio_fx.select()
        g.addWidget(self.chk_audio_fx)
        g.addStretch(1)
        cols.addWidget(gfx, 1, Qt.AlignmentFlag.AlignTop)

        right, r = _card("card")
        r.addWidget(Label("Mods", "#eab84c", 12.5, bold=True))
        self.chk_overlay = CheckBox("Overlay en el juego (F1: ajustes y mover paneles; F2: ajustes)", self.save_settings_from_ui)
        if self.config.get("overlay", True):
            self.chk_overlay.select()
        r.addWidget(self.chk_overlay)
        _tip(self.chk_overlay, "💡 Con F1 (o F2, o L3 + R3 en el mando) se abre el menú del juego: ajustes, paneles y controles. Con B del mando o Esc se cierra.")

        self.chk_mod = {}
        for m in MODS:
            chk = CheckBox(m["label"], self.save_mods_from_ui)
            if mod_enabled(self.config, m["id"]):
                chk.select()
            self.chk_mod[m["id"]] = chk
            r.addWidget(chk)
            _tip(chk, m["hint"])

        r.addWidget(Label("Trucos (cheats)", "#e07a6f", 10.5, bold=True))
        warn = _hint("⚠ Pueden alterar o corromper tu partida guardada. Haz una copia antes (pestaña «Partidas & Logs») y úsalos bajo tu propia decisión.", "#eab84c")
        warn.setWordWrap(True)
        r.addWidget(warn)
        self.chk_cheats = CheckBox("Activar trucos al jugar", self.on_cheats_master_toggled)
        if self.config.get("cheats_enabled", False):
            self.chk_cheats.select()
        r.addWidget(self.chk_cheats)
        self.chk_cheat, self.entry_cheat = {}, {}
        for c in CHEATS:
            row = QHBoxLayout()
            chk = CheckBox(c["label"], self.save_cheats_from_ui)
            if self.config.get(f"cheat_{c['id']}", False):
                chk.select()
            self.chk_cheat[c["id"]] = chk
            row.addWidget(chk)
            if c.get("value"):
                row.addWidget(Label("×", None, 10.5, bold=True))
                entry = Entry(width=76)
                entry.insert(0, self.config.get(f"cheat_{c['id']}_value", c["value"]["default"]))
                entry.on_change(self.save_cheats_from_ui)
                self.entry_cheat[c["id"]] = entry
                row.addWidget(entry)
            row.addStretch(1)
            r.addLayout(row)
            _tip(chk, c["hint"])
        r.addStretch(1)
        cols.addWidget(right, 1, Qt.AlignmentFlag.AlignTop)
        return _transparent_scroll(inner)

    # ---- tab: controls -------------------------------------------------------------------------
    def setup_tab_controls(self):
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(4, 4, 8, 4)
        lay.setSpacing(12)

        info, il = _grid_card("accent")
        il.addWidget(Label("🕹️", None, 26), 0, 0, 2, 1)
        il.addWidget(Label("Remapeador de botones", "#4fc3d6", 12.5, bold=True), 0, 1)
        text = Label(
            "Asigna cualquier botón de tu mando (Xbox, PlayStation, Nintendo o genérico) a cada acción del GamePad de Wii U: "
            "elige la acción, pulsa en tu mando el botón que quieres usar y listo. Los cambios valen la próxima vez que pulses JUGAR.",
            "#e3d8bd",
            10,
        )
        text.setWordWrap(True)
        il.addWidget(text, 1, 1, 1, 2)
        il.setColumnStretch(1, 1)
        lay.addWidget(info)

        row = QHBoxLayout()
        row.setSpacing(12)

        # left: device, profile and the controller picture
        left, ll = _card("card")
        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(Label("Mando:", None, 10, bold=True))
        self.opt_map_device = OptionMenu(["Detectando mandos…"], width=210)
        head.addWidget(self.opt_map_device)
        head.addWidget(Label("Perfil:", None, 10, bold=True))
        self.opt_map_profile = OptionMenu(["Predeterminado (Xbox)", "Predeterminado (Nintendo)", "Personalizado"], width=210)
        self.opt_map_profile.currentIndexChanged.connect(lambda _i: self._on_map_profile())
        head.addWidget(self.opt_map_profile)
        head.addStretch(1)
        ll.addLayout(head)
        self.pad_diagram = qtmapping.PadDiagram()
        self.pad_diagram.picked.connect(self._on_map_pick)
        ll.addWidget(self.pad_diagram, 1)
        tools = QHBoxLayout()
        tools.setSpacing(8)
        for text, action in (("📥 Importar", self._import_map), ("📤 Exportar", self._export_map), ("↺ Restablecer", self._reset_map)):
            tools.addWidget(Button(text, "default", action, height=32, bold=False))
        tools.addStretch(1)
        ll.addLayout(tools)
        # the left column: the controller and, under it, the layout and camera options
        left_col = QWidget()
        left_lay = QVBoxLayout(left_col)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(12)
        left_lay.addWidget(left)
        row.addWidget(left_col, 5, Qt.AlignmentFlag.AlignTop)

        # right: one row per action
        right, rl = _card("card")
        rl.addWidget(Label("Asignación de botones", "#7fcfa6", 12, bold=True))
        self.map_note = Label(MAP_NOTE_IDLE, "#9db3ba", 9.5)
        self.map_note.setWordWrap(True)
        rl.addWidget(self.map_note)
        self.map_chips = {}
        for group, items in qtmapping.GROUPS:
            rl.addWidget(Label(group, "#eab84c", 10, bold=True))
            for key, name in items:
                line = QHBoxLayout()
                line.setSpacing(8)
                line.addWidget(Label(name, None, 10), 1)
                chip = Button("Sin asignar", "default", lambda k=key: self._on_map_pick(k), width=150, height=28, bold=False, size=9.5)
                clear = Button("✕", "default", lambda k=key: self._clear_map_target(k), width=34, height=28, bold=False, size=9.5)
                line.addWidget(chip)
                line.addWidget(clear)
                rl.addLayout(line)
                self.map_chips[key] = chip
        rl.addStretch(1)
        row.addWidget(right, 4)
        lay.addLayout(row)

        self.pad_map = padmap.PadMap(self.config.get("pad_map"))
        self.pad_listener = None
        self.pad_names = []  # the pads the reader has told about
        self._map_target = None  # the action waiting for a button (a name of padmap.NAMES)
        self._map_pressed = set()
        self._map_deadline = 0.0
        self._map_timer = QTimer(self.qapp)
        self._map_timer.setInterval(40)
        self._map_timer.timeout.connect(self._poll_pad)
        self._refresh_map_view()

        # what was in the graphics tab: layout and camera
        base, bl = _card("card")
        bl.addWidget(Label("Disposición y cámara", "#7fcfa6", 12, bold=True))
        bl.addWidget(Label("Disposición de Botones del Mando:"))
        self.opt_pad = Segmented(["Xbox (A abajo, B der)", "Nintendo (B abajo, A der)"], self.on_pad_changed)
        self.opt_pad.set("Xbox (A abajo, B der)" if self.config.get("pad_layout") == "xbox" else "Nintendo (B abajo, A der)")
        bl.addWidget(self.opt_pad)

        sens, sn = _card("inset", 12)
        head = QHBoxLayout()
        head.addWidget(Label("Sensibilidad de Cámara (Ratón):", None, 10, bold=True))
        head.addStretch(1)
        raw_sens = self.config.get("mouse_sensitivity", 0.0008)
        self.lbl_sens_val = Label(f"{int(round(raw_sens * 10000))}", "#4fc3d6", 10, bold=True)
        head.addWidget(self.lbl_sens_val)
        sn.addLayout(head)
        self.slider_sens = Slider(2, 30, self.on_mouse_sens_changed)
        self.slider_sens.set(int(round(raw_sens * 10000)))
        sn.addWidget(self.slider_sens)
        bl.addWidget(sens)

        stick, st = _card("inset", 12)
        head = QHBoxLayout()
        lbl_stick = Label("Sensibilidad de Cámara (Stick derecho del mando):", None, 10, bold=True)
        head.addWidget(lbl_stick)
        head.addStretch(1)
        raw_stick = int(self.config.get("right_stick_sens", 100))
        self.lbl_stick_val = Label(f"{raw_stick}%", "#4fc3d6", 10, bold=True)
        head.addWidget(self.lbl_stick_val)
        st.addLayout(head)
        self.slider_stick = Slider(25, 150, self.on_right_stick_changed)
        self.slider_stick.set(raw_stick)
        st.addWidget(self.slider_stick)
        _tip(lbl_stick, "100% es lo que reporta el mando; baja el valor si la cámara se siente demasiado rápida. También se cambia dentro del juego (F2).", self.slider_stick)
        self.chk_analog_camera = CheckBox("Cámara suave con el stick derecho", self.on_analog_camera_toggled)
        if self.config.get("analog_camera", True):
            self.chk_analog_camera.select()
        st.addWidget(self.chk_analog_camera)
        _tip(
            self.chk_analog_camera,
            "La cámara gira y sube o baja según cuánto empujes el stick: un poco para moverla despacio, a fondo para moverla rápido. "
            "Desactívalo para volver a la cámara original del juego, que se mueve a saltos como con botones.",
        )
        bl.addWidget(stick)
        left_lay.addWidget(base)
        lay.addStretch(1)
        return _transparent_scroll(inner)

    # ---- the button remapper ----------------------------------------------------------------
    def _on_tab_changed(self, key):
        """The pads are read only while the Controls tab shows (and the game is not running)."""
        if key == TAB_CONTROLS.strip() and not getattr(self, "is_running", False):
            self._start_pad_listener()
        else:
            self._stop_map_capture()
            self._stop_pad_listener()
            self._map_timer.stop()
            self._map_pressed = set()
            self.pad_diagram.set_pressed(())

    def _start_pad_listener(self):
        layout = self.config.get("pad_layout", "xbox")
        if self.pad_listener is None or self.pad_listener.layout != layout:
            self._stop_pad_listener()
            self.pad_listener = padmap.PadListener(self._tools_exe_path(), layout)
        if self.pad_listener.running or self.pad_listener.start():
            self._map_timer.start()
            QTimer.singleShot(3500, self._refresh_map_device)
            return True
        self.map_note.configure(text=MAP_NOTE_NO_ENGINE)
        return False

    def _refresh_map_device(self):
        names = self.pad_names or ["Ningún mando detectado"]
        shown = self.opt_map_device.get()
        self.opt_map_device.set_values(names)
        self.opt_map_device.set(shown)

    def _poll_pad(self):
        import time

        listener = self.pad_listener
        if listener is None:
            return
        if self._map_target and time.monotonic() > self._map_deadline:
            self._stop_map_capture()
        for kind, value in listener.poll():
            if kind == "pad":
                if value not in self.pad_names:
                    self.pad_names.append(value)
                    self._refresh_map_device()
            elif kind == "down":
                self._map_pressed.add(value)
                if self._map_target:
                    self._assign_pressed(value)
            else:
                self._map_pressed.discard(value)
        self.pad_diagram.set_pressed({padmap.ID_OF_NAME[n] for n in self._map_pressed})

    def _on_map_pick(self, key):
        """An action was picked (in the list or on the controller): the next button pressed on the pad becomes its button."""
        import time

        if not self._start_pad_listener():
            return
        self._map_target = padmap.NAME_OF_ID[key]
        self._map_deadline = time.monotonic() + 10.0
        self.pad_diagram.set_active(key)
        self.map_note.configure(text=MAP_NOTE_ARMED.format(padmap.short(self._map_target)))
        self._refresh_map_chips()

    def _assign_pressed(self, source):
        target = self._map_target
        self._map_target = None
        self.pad_map.assign(source, target)
        self._save_pad_map()
        self.pad_diagram.set_active(None)
        self.map_note.configure(text=MAP_NOTE_DONE.format(padmap.short(source), padmap.short(target)))
        self._refresh_map_view()

    def _stop_map_capture(self):
        if getattr(self, "_map_target", None):
            self._map_target = None
            self.pad_diagram.set_active(None)
            self.map_note.configure(text=MAP_NOTE_IDLE)
            self._refresh_map_chips()

    def _clear_map_target(self, key):
        self.pad_map.clear_target(padmap.NAME_OF_ID[key])
        self._map_target = None
        self.pad_diagram.set_active(None)
        self._save_pad_map()
        self.map_note.configure(text=MAP_NOTE_IDLE)
        self._refresh_map_view()

    def _reset_map(self):
        self.pad_map.reset()
        self._map_target = None
        self.pad_diagram.set_active(None)
        self._save_pad_map()
        self.map_note.configure(text=MAP_NOTE_IDLE)
        self._refresh_map_view()

    def _save_pad_map(self):
        self.config["pad_map"] = self.pad_map.to_dict()
        self.save_config()

    def _refresh_map_view(self):
        self._refresh_map_chips()
        self.opt_map_profile.blockSignals(True)
        if not self.pad_map.is_default():
            self.opt_map_profile.set("Personalizado")
        else:
            self.opt_map_profile.set("Predeterminado (Xbox)" if self.config.get("pad_layout", "xbox") == "xbox" else "Predeterminado (Nintendo)")
        self.opt_map_profile.blockSignals(False)

    def _refresh_map_chips(self):
        for key, chip in self.map_chips.items():
            name = padmap.NAME_OF_ID[key]
            if name == self._map_target:
                chip.configure(text="Pulsa un botón…", fg_color="#b8791e", hover_color="#d4922a")
                continue
            sources = self.pad_map.sources_of(name)
            changed = sources != [name]
            text = "Sin asignar" if not sources else "Botón " + " + ".join(padmap.short(s) for s in sources)
            if changed and sources:
                chip.configure(text=text, fg_color="#2f6a52", hover_color="#3b8466")
            else:
                chip.configure(text=text, fg_color="#2b4a58", hover_color="#3b6073")

    def _on_map_profile(self):
        """Default (Xbox) and default (Nintendo) set the layout and drop the changes; Custom is what the table says."""
        choice = self.opt_map_profile.get()
        if choice == "Personalizado":
            self._refresh_map_view()
            return
        layout = "xbox" if "Xbox" in choice else "nintendo"
        if not self.pad_map.is_default() and not qtshim.messagebox.askyesno(
            "Perfil", "Elegir un perfil predeterminado borra tus cambios de botones. ¿Continuar?"
        ):
            self._refresh_map_view()
            return
        self.pad_map.reset()
        self._save_pad_map()
        self.opt_pad.set("Xbox (A abajo, B der)" if layout == "xbox" else "Nintendo (B abajo, A der)")
        self.on_pad_changed("Xbox" if layout == "xbox" else "Nintendo")
        self._refresh_map_view()
        if self.pad_listener is not None and self.pad_listener.layout != layout:
            self._start_pad_listener()  # the reader tells the buttons of the new layout

    def _export_map(self):
        path = qtshim.filedialog.asksaveasfilename(title="Exportar mapa de botones", filter="Mapa de botones (*.json)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.pad_map.to_json())
        except OSError as e:
            qtshim.messagebox.showerror("Exportar", f"No se pudo guardar el archivo: {e}")

    def _import_map(self):
        path = qtshim.filedialog.askopenfilename(title="Importar mapa de botones", filter="Mapa de botones (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                imported = padmap.PadMap.from_json(f.read())
        except OSError as e:
            qtshim.messagebox.showerror("Importar", f"No se pudo leer el archivo: {e}")
            return
        if imported is None:
            qtshim.messagebox.showerror("Importar", "El archivo no es un mapa de botones de MH3U.")
            return
        self.pad_map = imported
        self._save_pad_map()
        self._refresh_map_view()

    # ---- tab 4 ---------------------------------------------------------------------------------
    def setup_tab_online(self):
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(4, 4, 8, 4)
        lay.setSpacing(12)

        info, il = _grid_card("accent")
        il.addWidget(Label("🌐", None, 28), 0, 0, 2, 1)
        il.addWidget(Label("Multijugador Online de Tanzia (Protocolo Matt-Wood-23 / mh3u-revival)", "#4fc3d6", 12, bold=True), 0, 1)
        text = Label(
            "Módulo de red con soporte P2P y servidor relay de baja latencia. Permite crear o unirte a partidas de hasta 4 cazadores. "
            "Para jugar por Internet sin abrir puertos en el router, se recomienda que tú y tus amigos usen una red virtual como "
            "Radmin VPN, ZeroTier o Tailscale.",
            "#e3d8bd",
            10,
        )
        text.setWordWrap(True)
        il.addWidget(text, 1, 1)
        il.setColumnStretch(1, 1)
        lay.addWidget(info)

        top, tl = _card("card")
        self.switch_online = Switch("Habilitar Modo Multijugador Online al iniciar el juego", self.on_online_switch_toggled)
        if self.config.get("online_enabled", False):
            self.switch_online.select()
        tl.addWidget(self.switch_online)
        tl.addWidget(Label("Selecciona tu función en la partida:", "#9db3ba", 10, bold=True))
        current_mode = self.config.get("online_mode", "client")
        init_mode = "👑 Crear mi sala (Host)" if current_mode == "host" else "🎮 Unirme a la sala de un amigo (Cliente)"
        self.seg_online_mode = Segmented(["🎮 Unirme a la sala de un amigo (Cliente)", "👑 Crear mi sala (Host)"], self.on_online_mode_changed, bold=True)
        self.seg_online_mode.set(init_mode)
        tl.addWidget(self.seg_online_mode)
        self.chk_separate_save = CheckBox("Partidas guardadas aparte (para jugar junto a Cemu en este mismo PC)", self.on_separate_save_toggled)
        if self.config.get("separate_save", False):
            self.chk_separate_save.select()
        tl.addWidget(self.chk_separate_save)
        _tip(
            self.chk_separate_save,
            "Usa una carpeta de partidas propia (partidas_aparte, junto al launcher) en vez de la normal. Así el puerto y Cemu en el mismo PC "
            "pueden tener cazadores con nombres distintos y no chocan en la sala. Empiezas con un cazador nuevo; la partida de siempre no se toca.",
        )
        lbl_relay = Label("Relay del servidor (solo si creas la sala):", "#9db3ba", 10, bold=True)
        tl.addWidget(lbl_relay)
        self.seg_relay = Segmented(["Auto", "Activado", "Desactivado"], self.on_relay_changed)
        self.seg_relay.set({"force": "Activado", "off": "Desactivado"}.get(str(self.config.get("online_relay", "auto")).lower(), "Auto"))
        tl.addWidget(self.seg_relay)
        _tip(
            lbl_relay,
            "Cómo viajan los datos entre quien crea la sala y sus invitados.\n"
            "Auto (recomendado): conexión directa, y el servidor hace de puente solo si la directa falla.\n"
            "Activado: siempre a través del servidor; pruébalo si un invitado no logra entrar o se desconecta.\n"
            "Desactivado: nunca; solo conexión directa.\n"
            "Entre invitados la conexión es siempre directa. Con Radmin VPN o parecidas no hace falta tocarlo.",
            self.seg_relay,
        )
        diag_row = QHBoxLayout()
        btn_diag = Button("🩺 Diagnóstico de Red", "default", self.run_diagnostics, width=190)
        _tip(btn_diag, "Revisa el firewall, tu IP y la conexión con tu amigo. Lo que escribas aquí se guarda solo al pulsar JUGAR.")
        diag_row.addWidget(btn_diag)
        diag_row.addStretch(1)
        tl.addLayout(diag_row)
        lay.addWidget(top)

        # client
        self.frame_client_mode, c = _grid_card("card")
        c.addWidget(Label("🎮 Conexión a la Partida de tu Amigo (Cliente)", "#7fcfa6", 11.5, bold=True), 0, 0, 1, 2)
        c.addWidget(Label("IP del Anfitrión / Amigo:"), 1, 0)
        host_row = QHBoxLayout()
        self.entry_server_host = Entry(width=230)
        self.entry_server_host.insert(0, self.config.get("online_server", "127.0.0.1"))
        host_row.addWidget(self.entry_server_host)
        self.btn_ping_host = Button("🔍 Probar Conexión", "default", self.test_host_ping, width=140)
        host_row.addWidget(self.btn_ping_host)
        host_row.addStretch(1)
        c.addLayout(host_row, 1, 1)
        self.lbl_ping_result = Label("Estado: Listo para probar conexión", "#9db3ba", 10)
        c.addWidget(self.lbl_ping_result, 2, 1)
        c.addWidget(Label("ID de Sala / Taberna:"), 3, 0)
        self.entry_room_id = Entry(width=130)
        self.entry_room_id.insert(0, self.config.get("online_room_id", "1001"))
        c.addWidget(self.entry_room_id, 3, 1)
        c.setColumnStretch(1, 1)
        lay.addWidget(self.frame_client_mode)

        # host
        self.frame_host_mode, h = _grid_card("card")
        lbl_server = Label("👑 Servidor de Salas Integrado (Crear Partida)", "#eab84c", 11.5, bold=True)
        _tip(lbl_server, "Inicia el servidor de retransmisión local para que tus amigos se conecten contigo a Puerto Tanzia.")
        h.addWidget(lbl_server, 0, 0, 1, 2)
        h.addWidget(Label("Tu IP para amigos:"), 2, 0)
        ip_row = QHBoxLayout()
        ips = get_local_ip_addresses()
        self.opt_local_ips = OptionMenu(ips, width=290)
        if ips:
            self.opt_local_ips.set(ips[0])
        ip_row.addWidget(self.opt_local_ips)
        ip_row.addWidget(Button("🔄", "default", self.refresh_local_ips, width=44))
        ip_row.addWidget(Button("📋 Copiar IP", "default", self.copy_selected_ip, width=110))
        self.lbl_copy_feedback = Label("", "#7fcfa6", 9.5)
        ip_row.addWidget(self.lbl_copy_feedback)
        ip_row.addStretch(1)
        h.addLayout(ip_row, 2, 1)
        h.addWidget(Label("ID de Sala por Defecto:"), 3, 0)
        self.entry_host_room = Entry(width=130)
        self.entry_host_room.insert(0, self.config.get("online_room_id", "1001"))
        h.addWidget(self.entry_host_room, 3, 1)
        act = QHBoxLayout()
        self.btn_toggle_server = Button("▶  Iniciar Servidor de Sala (Host)", "teal", self.toggle_host_server, height=38)
        act.addWidget(self.btn_toggle_server)
        self.lbl_server_status = Label("⚪ Servidor Inactivo", "#9db3ba", 10.5, bold=True)
        act.addWidget(self.lbl_server_status)
        act.addStretch(1)
        h.addLayout(act, 4, 0, 1, 2)
        h.addWidget(Label("Registro del Servidor en Tiempo Real:", "#4fc3d6", 10, bold=True), 5, 0, 1, 2)
        self.txt_server_log = LogBox(140)
        h.addWidget(self.txt_server_log, 6, 0, 1, 2)
        h.setColumnStretch(1, 1)
        lay.addWidget(self.frame_host_mode)

        save = Button("💾 Guardar ahora", "default", self.save_online_settings, height=38)
        lay.addWidget(save, 0, Qt.AlignmentFlag.AlignLeft)
        lay.addStretch(1)

        self.on_online_mode_changed(init_mode)
        return _transparent_scroll(inner)

    # ---- tab 5 ---------------------------------------------------------------------------------
    def setup_tab_tools(self):
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(4, 4, 8, 4)
        lay.setSpacing(12)

        card, g = _grid_card("card")
        g.addWidget(Label("Gestión de Datos y Partidas", "#4fc3d6", 12.5, bold=True), 0, 0, 1, 2)
        rows = [
            ("📂 Abrir Carpeta de Saves", "gold", self.open_save_folder, "Ubicación donde el port guarda tu progreso y personaje."),
            ("🛡️ Respaldar Partidas Ahora", "good", self.backup_save_folder, "Crea un archivo comprimido .zip con la fecha actual."),
            ("📄 Abrir Registro (Log Reciente)", "default", self.open_latest_log, "Abre 'mh3u_latest.log' para revisar errores de Vulkan o del juego."),
            ("🧹 Limpiar Caché de Shaders", "danger", self.clean_cache, "Elimina la caché de pipelines si notas artefactos gráficos."),
        ]
        for i, (text, kind, fn, desc) in enumerate(rows, start=1):
            g.addWidget(Button(text, kind, fn, width=250), i, 0)
            g.addWidget(Label(desc), i, 1)
        g.setColumnStretch(1, 1)
        lay.addWidget(card)

        credits, c = _grid_card("card")
        c.addWidget(Label("Créditos y Agradecimientos", "#4fc3d6", 12.5, bold=True), 0, 0, 1, 2)
        c.addWidget(Label("Desarrollo del Launcher:", "#eab84c", 10.5, bold=True), 1, 0)
        c.addWidget(Button("G30vamv / MH3U-NativePC ↗", "link", lambda: webbrowser.open_new_tab("https://github.com/G30vamv/MH3U-NativePC"), height=28, bold=False), 1, 1, Qt.AlignmentFlag.AlignLeft)
        links = [
            ("Port Nativo & Recompilación PC:", "glinesbdev / mh3u-port ↗", "https://github.com/glinesbdev/mh3u-port"),
            ("Lógica de Red & Servidor Online:", "Matt-Wood-23 / mh3u-revival ↗", "https://github.com/Matt-Wood-23/mh3u-revival"),
        ]
        for i, (what, text, url) in enumerate(links, start=2):
            c.addWidget(Label(what, None, 10.5, bold=True), i, 0)
            c.addWidget(Button(text, "link", lambda u=url: webbrowser.open_new_tab(u), height=28, bold=False), i, 1, Qt.AlignmentFlag.AlignLeft)
        c.addWidget(Label("Versión del Launcher:", "#4fc3d6", 10.5, bold=True), 4, 0)
        c.addWidget(Label(f"{APP_VERSION} (MH3U NativePC)", "#eab84c", 10.5, bold=True), 4, 1)
        c.setColumnStretch(1, 1)
        lay.addWidget(credits)
        lay.addStretch(1)
        return _transparent_scroll(inner)


def main():
    qapp = QApplication(sys.argv)
    qapp.setStyle(qtanim.TipStyle())
    qapp.setStyleSheet(STYLE)
    qtanim.install_tips(qapp)
    qapp.setFont(font(10.5))
    qtshim.init_threading()
    app = MH3ULauncherApp(qapp)
    qtanim.fade_window_in(app.window)
    app.show()
    QTimer.singleShot(0, lambda: qtanim.intro([app.header, app.tabview.bar, app.tabview.stack, app.footer]))
    return qapp.exec()


if __name__ == "__main__":
    sys.exit(main())
