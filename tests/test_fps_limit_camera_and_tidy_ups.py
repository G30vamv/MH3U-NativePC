# SPDX-License-Identifier: AGPL-3.0-only
"""v0.9.16: the frame limit and its drop-down list, the smooth camera's switch, the relay choice, LTO in the gear's menu, windows
in the middle of the screen and the update backups that no longer pile up."""
import os
import sys
import tempfile
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.join(os.path.dirname(__file__), "..")
LAUNCHER = os.path.join(ROOT, "launcher")
sys.path.insert(0, LAUNCHER)

from PySide6.QtCore import QEvent, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402
from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

_APP = QApplication.instance() or QApplication([])

import core  # noqa: E402
import i18n  # noqa: E402
import qtmenu  # noqa: E402
import qtshim  # noqa: E402
import updater  # noqa: E402


def source(name):
    with open(os.path.join(LAUNCHER, name), encoding="utf-8") as f:
        return f.read()


class FrameLimitTests(unittest.TestCase):
    def test_the_limits_are_multiples_of_thirty_and_anything_else_is_no_limit(self):
        self.assertTrue(all(v % 30 == 0 for v in core.FPS_LIMITS))
        self.assertEqual(core.fps_limit_of({"fps_limit": 60}), 60)
        self.assertEqual(core.fps_limit_of({"fps_limit": "120"}), 120)
        for bad in (0, 75, -30, None, "x", 300):
            self.assertEqual(core.fps_limit_of({"fps_limit": bad}), 0)
        self.assertEqual(core.fps_limit_of({}), 0)

    def test_a_list_entry_and_its_limit_go_both_ways(self):
        for v in core.FPS_LIMITS:
            self.assertEqual(core.fps_limit_from_label(core.fps_limit_label(v)), v)
        self.assertEqual(core.fps_limit_label(0), core.FPS_NO_LIMIT)
        self.assertEqual(core.fps_limit_from_label(core.FPS_NO_LIMIT), 0)
        self.assertEqual(core.fps_limit_from_label(""), 0)

    def test_every_entry_of_the_list_has_its_explanation(self):
        tips = core.fps_limit_tips()
        for v in list(core.FPS_LIMITS) + [0]:
            self.assertTrue(tips.get(core.fps_limit_label(v)))

    def test_the_limit_chosen_in_the_game_comes_back_to_the_launcher(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "ingame_settings.txt")
            for text, want in (("fps_limit=90\n", 90), ("fps_limit=0\n", 0)):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                self.assertEqual(core.read_ingame_settings(path).get("fps_limit"), want)
            with open(path, "w", encoding="utf-8") as f:
                f.write("fps_limit=75\n")
            self.assertNotIn("fps_limit", core.read_ingame_settings(path))

    def test_the_game_gets_the_limit_and_the_camera_switch(self):
        src = source("core.py")
        self.assertIn('env["MH3U_FPS_LIMIT"] = str(limit)', src)
        self.assertIn('env["MH3U_ANALOG_CAMERA"] = "off"', src)
        self.assertIn('"fps_limit": 0', src)
        self.assertIn('"analog_camera": True', src)

    def test_the_selector_is_under_the_resolution_in_the_graphics_tab(self):
        src = source("mh3u_launcher_qt.py")
        scale, limit, full = (src.index(s) for s in ("self.opt_scale = Segmented", "self.opt_fps_limit = qtmenu.DropList", "self.chk_fullscreen = CheckBox"))
        self.assertTrue(scale < limit < full)


class DropListTests(unittest.TestCase):
    def setUp(self):
        self.host = QWidget()
        self.host.resize(400, 300)
        self.picked = []
        values = [core.fps_limit_label(v) for v in core.FPS_LIMITS] + [core.FPS_NO_LIMIT]
        self.drop = qtmenu.DropList(values, self.picked.append, core.fps_limit_tips(), parent=self.host)
        self.host.show()

    def tearDown(self):
        if self.drop.is_open():
            self.drop._popup.close()
        self.host.close()
        i18n.set_language("es")

    def test_it_shows_one_choice_and_unrolls_all_of_them(self):
        self.drop.set("60 FPS")
        self.assertEqual(self.drop.get(), "60 FPS")
        self.assertFalse(self.drop.is_open())
        self.drop.toggle_list()
        self.assertTrue(self.drop.is_open())
        self.assertEqual(len(self.drop.rows), len(core.FPS_LIMITS) + 1)
        self.assertEqual([r.text() for r in self.drop.rows if r.chosen], ["60 FPS"])
        self.assertTrue(all(r.toolTip() for r in self.drop.rows))
        self.drop.toggle_list()
        self.assertFalse(self.drop.is_open())

    def test_a_press_that_closes_the_list_does_not_open_it_again(self):
        # a popup takes the press that closes it and the click that follows reaches the button: that click must not reopen the list
        self.drop.toggle_list()
        self.assertTrue(self.drop.is_open())
        self.drop._popup.close()
        _APP.processEvents()
        self.assertFalse(self.drop.is_open())
        self.drop.toggle_list()
        self.assertFalse(self.drop.is_open(), "right after closing, the click is the same press")
        self.drop._closed_at -= 1.0
        self.drop.toggle_list()
        self.assertTrue(self.drop.is_open(), "a later click opens it")

    def test_the_gear_does_not_reopen_its_menu_with_the_press_that_closed_it(self):
        src = open(os.path.join(os.path.dirname(__file__), "..", "launcher", "mh3u_launcher_qt.py"), encoding="utf-8").read()
        body = src[src.index("    def open_menu"):src.index("    def on_auto_updates_toggled")]
        self.assertIn("qtanim.popup_just_closed()", body)
        self.assertLess(body.index("self.menu.close()"), body.index("qtanim.popup_just_closed()"))
        self.assertLess(body.index("qtanim.popup_just_closed()"), body.index("popup_below"))

    def test_the_press_that_closes_a_popup_does_not_start_a_window_move_or_resize(self):
        import qtanim
        import qttitle

        class Handle:
            moves = resizes = 0

            def startSystemMove(self):
                Handle.moves += 1

            def startSystemResize(self, edges):
                Handle.resizes += 1

        class Win(QWidget):
            def isMaximized(self):
                return False

            def windowHandle(self):
                return Handle()

        win = Win()
        grip = qttitle._Grip(win, Qt.Edge.LeftEdge, Qt.CursorShape.SizeHorCursor)
        press = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(1, 1), QPointF(1, 1), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        qtanim.note_popup_closed()
        grip.mousePressEvent(press)
        self.assertEqual(Handle.resizes, 0)
        qtanim._POPUP_CLOSED -= 1.0
        grip.mousePressEvent(press)
        self.assertEqual(Handle.resizes, 1)

    def test_picking_an_entry_closes_the_list_and_tells_the_logic(self):
        self.drop.set("60 FPS")
        self.drop.toggle_list()
        row = next(r for r in self.drop.rows if r.text() == "120 FPS")
        row.click()
        _APP.processEvents()
        _APP.processEvents()
        self.assertFalse(self.drop.is_open())
        self.assertEqual(self.picked, ["120 FPS"])
        self.assertEqual(self.drop.get(), "120 FPS")

    def test_setting_it_from_the_logic_does_not_call_back_and_ignores_unknown_entries(self):
        self.drop.set("90 FPS")
        self.drop.set("75 FPS")
        self.assertEqual(self.drop.get(), "90 FPS")
        self.assertEqual(self.picked, [])

    def test_the_list_is_shown_in_english_and_read_back_as_written(self):
        i18n.set_language("en")
        self.drop.set(core.FPS_NO_LIMIT)
        self.drop.toggle_list()
        self.assertIn("No limit", [r.text() for r in self.drop.rows])
        self.assertEqual(self.drop.get(), core.FPS_NO_LIMIT)


class TextsTests(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("es")

    def test_every_new_text_has_its_english(self):
        i18n.set_language("en")
        texts = [
            "Límite de FPS:", "💡 Límite de FPS:", "Límite de FPS", core.FPS_NO_LIMIT, "💡 Compilación optimizada (LTO)",
            "Cámara suave con el stick derecho", "💡 Cámara suave con el stick derecho", "Relay del servidor (solo si creas la sala):",
            "Auto", "Activado", "Desactivado",
        ] + list(core.fps_limit_tips().values())
        import ast

        for name in ("mh3u_launcher_qt.py",):
            for node in ast.walk(ast.parse(source(name))):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and any(
                    node.value.startswith(s) for s in ("El tope de fotogramas", "Optimiza más el juego", "La cámara gira y sube", "Cómo viajan los datos")
                ):
                    texts.append(node.value)
        self.assertGreaterEqual(len(texts), 20)
        before = set(i18n.missing())
        for t in texts:
            out = i18n.t(t)
            if t not in ("Auto",):
                self.assertNotEqual(out, t, t)
        self.assertEqual(set(i18n.missing()) - before, set())
        self.assertEqual(i18n.t("Para pantallas de 120 Hz."), "For 120 Hz screens.")


class RelayLtoAndCameraTests(unittest.TestCase):
    def test_the_relay_choice_is_kept_as_the_server_reads_it(self):
        class Logic:
            config = {}
            saved = 0

            def save_config(self):
                self.saved += 1

        logic = Logic()
        for shown, kept in (("Auto", "auto"), ("Activado", "force"), ("Desactivado", "off")):
            core.LauncherLogic.on_relay_changed(logic, shown)
            self.assertEqual(logic.config["online_relay"], kept)
        self.assertEqual(logic.saved, 3)

    def test_lto_lives_in_the_gears_menu_and_is_off_unless_chosen(self):
        src = source("mh3u_launcher_qt.py")
        menu = src[src.index("def _build_menu"):src.index("def open_menu")]
        self.assertIn("self.chk_lto = self.menu.add_switch(", menu)
        install = src[src.index("def setup_tab_install"):src.index("def setup_tab_settings")]
        self.assertNotIn("chk_lto", install)
        self.assertIn('"build_lto": False', source("core.py"))

    def test_the_camera_hooks_are_in_the_list_the_game_is_built_with(self):
        with open(os.path.join(ROOT, "package", "mods", "hooks.txt"), encoding="utf-8") as f:
            hooks = f.read()
        self.assertIn("0x02286f18 camera_turn", hooks)
        self.assertIn("0x02286890 camera_pitch", hooks)


class CentredWindowsTests(unittest.TestCase):
    def tearDown(self):
        qtshim.set_main_window(None)

    def test_the_middle_of_an_area(self):
        self.assertEqual(qtshim.centered_origin((1180, 840), (0, 0, 1920, 1040)), (370, 100))
        self.assertEqual(qtshim.centered_origin((1180, 840), (1920, 0, 2560, 1400)), (2610, 280))
        # bigger than the area: its top left corner stays in sight
        self.assertEqual(qtshim.centered_origin((2000, 1200), (0, 0, 1920, 1040)), (0, 0))

    def test_the_launcher_opens_in_the_middle_of_the_main_screen(self):
        w = QWidget()
        w.resize(400, 300)
        qtshim.center_on_primary(w)
        area = _APP.primaryScreen().availableGeometry()
        self.assertEqual((w.x(), w.y()), (area.x() + (area.width() - 400) // 2, area.y() + (area.height() - 300) // 2))
        self.assertIn("qtshim.center_on_primary(self.window)", source("mh3u_launcher_qt.py"))

    def test_a_dialog_opens_over_the_launcher_or_in_the_middle_of_the_screen(self):
        area = _APP.primaryScreen().availableGeometry()
        dlg = QWidget()
        dlg.setFixedSize(200, 100)
        qtshim.set_main_window(None)
        qtshim.center_dialog(dlg)
        self.assertEqual((dlg.x(), dlg.y()), (area.x() + (area.width() - 200) // 2, area.y() + (area.height() - 100) // 2))
        main = QWidget()
        main.setGeometry(area.x() + 40, area.y() + 60, 500, 400)
        main.show()
        qtshim.set_main_window(main)
        qtshim.center_dialog(dlg)
        g = main.frameGeometry()
        self.assertEqual((dlg.x(), dlg.y()), (g.x() + (g.width() - 200) // 2, g.y() + (g.height() - 100) // 2))
        main.hide()  # a hidden launcher: the screen again
        qtshim.center_dialog(dlg)
        self.assertEqual(dlg.x(), area.x() + (area.width() - 200) // 2)
        main.close()

    def test_every_dialog_of_the_launcher_is_placed(self):
        src = source("qtshim.py")
        self.assertIn("center_dialog(box)", src)
        self.assertIn("center_dialog(dlg, fit=False)", src)
        self.assertEqual(src.count("QFileDialog.get"), src.count("(_dialog_parent(), title"))


class UpdateBackupsTests(unittest.TestCase):
    def test_only_the_newest_backup_stays(self):
        with tempfile.TemporaryDirectory() as base:
            root = os.path.join(base, updater.BACKUP_DIR)
            now = time.time()
            for k, version in enumerate(("v0.9.12", "v0.9.13", "v0.9.15", "v0.9.14")):
                folder = os.path.join(root, version)
                os.makedirs(folder)
                with open(os.path.join(folder, "mh3u-tools.exe"), "w") as f:
                    f.write("x")
                stamp = now - 1000 + k * 100
                os.utime(folder, (stamp, stamp))
            self.assertEqual(sorted(updater.prune_backups(base)), ["v0.9.12", "v0.9.13", "v0.9.15"])
            self.assertEqual(os.listdir(root), ["v0.9.14"])  # the one made last
            self.assertEqual(updater.prune_backups(base), [])

    def test_nothing_to_tidy_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as base:
            self.assertEqual(updater.prune_backups(base), [])

    def test_an_update_keeps_only_its_own_backup(self):
        with tempfile.TemporaryDirectory() as base:
            script = updater.write_apply_script([{"rel": "MH3U.exe"}], base, "v9.9.9")
            with open(script, encoding="utf-8") as f:
                text = f.read()
            backups = os.path.join(base, updater.BACKUP_DIR)
            wipe = f'if exist "{backups}" rmdir /S /Q "{backups}"'
            make = f'mkdir "{os.path.join(backups, "v9.9.9")}"'
            self.assertIn(wipe, text)
            self.assertLess(text.index(wipe), text.index(make))

    def test_the_launcher_tidies_up_when_it_opens(self):
        self.assertIn("updater.prune_backups", source("mh3u_launcher_qt.py"))


if __name__ == "__main__":
    unittest.main()
