# SPDX-License-Identifier: AGPL-3.0-only
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
LAUNCHER = os.path.join(os.path.dirname(__file__), "..", "launcher")
sys.path.insert(0, LAUNCHER)

import core  # noqa: E402
import i18n  # noqa: E402
import i18n_en  # noqa: E402


class TranslationTests(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("es")

    def test_spanish_shows_the_text_as_it_is(self):
        i18n.set_language("es")
        self.assertEqual(i18n.t("Guardar ahora"), "Guardar ahora")
        self.assertEqual(i18n.t("💾 Guardar ahora"), "💾 Guardar ahora")

    def test_english_exact_texts_templates_and_the_spaces_around_them(self):
        i18n.set_language("en")
        self.assertEqual(i18n.t("💾 Guardar ahora"), "💾 Save now")
        self.assertEqual(i18n.t("  🎮 Principal  "), "  🎮 Main  ")
        self.assertEqual(i18n.t("Resolución: 2x (1440p 2K)"), "Resolution: 2x (1440p 2K)")
        self.assertEqual(i18n.t("¡Copiado: 26.1.2.3!"), "Copied: 26.1.2.3!")

    def test_a_tooltip_is_its_hint_without_the_bulb_and_a_bulb_label_follows_its_text(self):
        i18n.set_language("en")
        self.assertEqual(i18n.t("El filo del arma no baja nunca."), "Your weapon's sharpness never goes down.")
        self.assertEqual(i18n.t("💡 Escala de Resolución Interna:"), "💡 Internal Resolution Scale:")
        # the bulb replaces the icon a label had
        self.assertTrue(i18n.t("💡 Limpiar Caché de Shaders").startswith("💡 Clear Shader Cache"))

    def test_a_text_of_several_lines_is_translated_line_by_line(self):
        i18n.set_language("en")
        out = i18n.t("[Launcher] Deteniendo servidor...\n[Launcher] Firewall listo para jugar online.\n")
        self.assertEqual(out, "[Launcher] Stopping server...\n[Launcher] Firewall ready for online play.\n")

    def test_the_directx_12_question_and_its_two_buttons_are_translated(self):
        import ast

        tree = ast.parse(open(os.path.join(LAUNCHER, "core.py"), encoding="utf-8").read())
        texts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        question = next(t for t in texts if t.startswith("DirectX 12 funciona mejor"))
        i18n.set_language("en")
        self.assertTrue(i18n.t(question).startswith("DirectX 12 works better"))
        self.assertIn("Play anyway", i18n.t(question))
        self.assertEqual(i18n.t("Instalar ahora"), "Install now")
        self.assertEqual(i18n.t("Jugar así (puede verse negro)"), "Play anyway (it may look black)")

    def test_what_has_no_english_yet_is_shown_as_it_is(self):
        i18n.set_language("en")
        self.assertEqual(i18n.t("Una frase que nadie tradujo todavía"), "Una frase que nadie tradujo todavía")
        self.assertEqual(i18n.t("127.0.0.1"), "127.0.0.1")
        self.assertEqual(i18n.t(""), "")

    def test_every_template_keeps_its_values_in_the_english_text(self):
        for es, en in i18n_en.TEMPLATES:
            self.assertEqual(es.count("{}"), en.count("{}"), es)

    def test_the_english_texts_are_not_spanish(self):
        accents = re.compile(r"[áéíóúñ¿¡]")
        names = {"Español", "partidas_aparte"}
        for es, en in list(i18n_en.EXACT.items()) + list(i18n_en.TEMPLATES):
            if en in names or "partidas_aparte" in en:
                continue
            self.assertFalse(accents.search(en), f"{es!r} -> {en!r}")


class LanguageChoiceTests(unittest.TestCase):
    def test_automatic_follows_windows_and_anything_but_spanish_is_english(self):
        with mock.patch.object(core, "system_ui_language", return_value="en"):
            self.assertEqual(core.resolve_language("auto"), "en")
        with mock.patch.object(core, "system_ui_language", return_value="es"):
            self.assertEqual(core.resolve_language("auto"), "es")
        self.assertEqual(core.resolve_language("es"), "es")
        self.assertEqual(core.resolve_language("fr"), core.system_ui_language())

    def test_windows_language_ids(self):
        import ctypes

        class Kernel:
            def __init__(self, lang):
                self.lang = lang

            def GetUserDefaultUILanguage(self):
                return self.lang

        class Win:
            def __init__(self, lang):
                self.kernel32 = Kernel(lang)

        for lang_id, expected in ((0x0C0A, "es"), (0x040A, "es"), (0x080A, "es"), (0x0409, "en"), (0x040C, "en"), (0x0411, "en")):
            with mock.patch.object(ctypes, "windll", Win(lang_id), create=True):
                self.assertEqual(core.system_ui_language(), expected, hex(lang_id))


class WindowInEnglishTests(unittest.TestCase):
    """The whole window, built in English: nothing is left in Spanish and the logic still reads the original texts."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication

        cls.tmp = tempfile.mkdtemp()
        shutil.copytree(os.path.join(LAUNCHER, "assets"), os.path.join(cls.tmp, "assets"))
        with open(os.path.join(cls.tmp, "launcher_config.json"), "w") as f:
            json.dump({"ui_language": "en"}, f)
        cls._base = core.get_base_dir
        core.get_base_dir = lambda: cls.tmp
        import mh3u_launcher_qt as m

        cls.m = m
        m.get_base_dir = lambda: cls.tmp
        cls.app = QApplication.instance() or QApplication([])
        cls.win = m.MH3ULauncherApp(cls.app)
        cls.win.window.show()
        cls.app.processEvents()

    @classmethod
    def tearDownClass(cls):
        cls.win.window.close()
        core.get_base_dir = cls._base
        i18n.set_language("es")
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_it_is_built_in_english(self):
        self.assertEqual(i18n.language(), "en")

    def test_no_shown_text_is_left_in_spanish(self):
        from PySide6.QtWidgets import QAbstractButton, QComboBox, QLabel, QLineEdit

        spanish = re.compile(r"[áéíóúñ¿¡]|\b(el|la|los|las|del|que|para|con|una|tus|pulsa|juego|partida|servidor|sala|carpeta|archivo)\b")
        left = []
        from PySide6.QtWidgets import QWidget

        for w in self.win.window.findChildren(QWidget) + self.win.menu.findChildren(QWidget):  # this window only (others may exist)
            shown = []
            if isinstance(w, QLabel):
                shown.append(QLabel.text(w))
            elif isinstance(w, QAbstractButton):
                shown.append(w.text())
            elif isinstance(w, QLineEdit):
                shown.append(w.placeholderText())
            elif isinstance(w, QComboBox):
                shown += [w.itemText(i) for i in range(w.count())]
            shown.append(w.toolTip())
            for text in shown:
                if text and text not in ("Español",) and spanish.search(re.sub(r"<[^>]+>", " ", text)):
                    left.append(text[:90])
        self.assertEqual(left, [])

    def test_the_logic_still_reads_the_original_texts(self):
        w = self.win
        self.assertEqual(w.opt_adapter.get(), "Automática (la mejor)")  # what the logic knows
        self.assertIn("Automatic", w.opt_adapter.itemText(0))  # what the player sees
        self.assertEqual(w.lbl_quick_online.text().split(":")[0], "Online")
        w.opt_backend.set("DirectX 12 (DX12)")
        self.assertEqual(w.opt_backend.get(), "DirectX 12 (DX12)")

    def test_the_language_selector_is_in_the_gear_menu_and_not_in_the_graphics_tab(self):
        self.assertTrue(hasattr(self.win, "seg_language"))
        self.assertFalse(hasattr(self.win, "opt_ui_language"))
        self.assertEqual(self.win.seg_language.get(), "English")


if __name__ == "__main__":
    unittest.main()
