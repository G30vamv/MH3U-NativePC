import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "launcher"))

from PySide6.QtCore import QEventLoop, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

_APP = QApplication.instance() or QApplication([])


def wait(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


class AnimationSwitchTests(unittest.TestCase):
    def tearDown(self):
        import qtanim

        qtanim.set_user_choice(True)

    def test_animations_follow_the_users_choice_and_windows(self):
        import qtanim

        qtanim._windows_allows = True
        qtanim.set_user_choice(True)
        self.assertTrue(qtanim.enabled())
        qtanim.set_user_choice(False)
        self.assertFalse(qtanim.enabled())
        qtanim.set_user_choice(True)
        qtanim._windows_allows = False  # "reduce animations" in Windows
        self.assertFalse(qtanim.enabled())
        qtanim._windows_allows = True

    def test_a_page_fade_takes_its_effect_off_when_it_ends(self):
        import qtanim

        qtanim._windows_allows = True
        qtanim.set_user_choice(True)
        w = QWidget()
        w.show()
        qtanim.fade_in(w, 60)
        self.assertIsNotNone(w.graphicsEffect())
        wait(250)
        self.assertIsNone(w.graphicsEffect())  # an effect left on would make every repaint slower

    def test_nothing_runs_when_animations_are_off(self):
        import qtanim

        qtanim.set_user_choice(False)
        w = QWidget()
        w.show()
        qtanim.fade_in(w, 60)
        self.assertIsNone(w.graphicsEffect())

    def test_colour_mix_ends(self):
        import qtanim
        from PySide6.QtGui import QColor

        a, b = QColor(0, 0, 0, 0), QColor(200, 100, 50, 255)
        self.assertEqual(qtanim.mix(a, b, 0).getRgb(), a.getRgb())
        self.assertEqual(qtanim.mix(a, b, 1).getRgb(), b.getRgb())

    def test_the_glow_runs_only_while_allowed_and_rests_when_not(self):
        import qtanim

        target = QWidget()
        target.glow = 0.0
        state = {"ok": True}
        glow = qtanim.Glow(target, lambda: state["ok"])
        glow.refresh()
        self.assertTrue(glow._timer.isActive())
        wait(120)
        self.assertGreater(target.glow, 0.0)
        state["ok"] = False
        glow.refresh()
        self.assertFalse(glow._timer.isActive())
        self.assertEqual(target.glow, 0.0)


class TooltipTests(unittest.TestCase):
    def test_tooltip_text_is_escaped_and_laid_out_as_a_block(self):
        import qtanim

        html = qtanim.tip_html("a < b\nsecond line")
        self.assertIn("a &lt; b<br>second line", html)
        self.assertIn("<table", html)

    def test_an_option_with_an_explanation_starts_with_the_bulb(self):
        import mh3u_launcher_qt as ui
        from qtshim import Button, Label

        label = Label("Motor Gráfico:")
        other = Label("x")
        ui._tip(label, "💡 Usa DirectX 12", other)
        self.assertEqual(label.text(), "💡 Motor Gráfico:")
        self.assertIn("Usa DirectX 12", label.toolTip())
        self.assertNotIn("💡", label.toolTip())  # the bulb is on the option, not repeated in the text
        self.assertEqual(label.toolTip(), other.toolTip())
        # a leading icon is replaced by the bulb, not doubled
        button = Button("🩺 Diagnóstico de Red")
        ui._tip(button, "Revisa el firewall")
        self.assertEqual(button.text(), "💡 Diagnóstico de Red")
        # asking twice does not add a second bulb
        ui._tip(button, "Otra vez")
        self.assertEqual(button.text(), "💡 Diagnóstico de Red")


class WidgetTests(unittest.TestCase):
    def test_a_button_paints_in_every_state_and_keeps_a_usable_size(self):
        from qtshim import Button

        b = Button("Guardar ahora", "teal", None, width=120, height=34)
        b.resize(b.sizeHint())
        self.assertGreaterEqual(b.sizeHint().width(), 120)
        self.assertGreaterEqual(b.sizeHint().height(), 34)
        for state in ("normal", "disabled"):
            b.configure(state=state)
            self.assertFalse(b.grab().isNull())
        b._hover = 1.0
        b.glow = 1.0
        self.assertFalse(b.grab().isNull())

    def test_pages_can_be_hidden_from_a_tab_bar_and_the_current_one_is_known(self):
        from qtshim import TabView

        tv = TabView(show_bar=False)
        a, b = QWidget(), QWidget()
        tv.add("  uno  ", a)
        tv.add("  dos  ", b)
        tv.show()
        self.assertFalse(tv.bar.isVisible())
        self.assertEqual(tv.current(), "uno")
        tv.set("  dos  ")
        self.assertEqual(tv.current(), "dos")

    def test_the_menu_marks_the_page_showing_and_tells_when_it_closes(self):
        import qtmenu

        host = QWidget()
        host.show()
        menu = qtmenu.SettingsMenu(host)
        seen = []
        menu.add_page("uno", "Uno", lambda: seen.append("uno"))
        menu.add_page("dos", "Dos", lambda: seen.append("dos"))
        menu.add_separator()
        menu.add_switch("Animaciones", True, lambda: seen.append("sw"))
        menu.set_current("dos")
        self.assertFalse(menu._pages["uno"].current)
        self.assertTrue(menu._pages["dos"].current)
        closed = []
        menu.on_hidden = lambda: closed.append(1)
        menu.popup_below(host)
        self.assertTrue(menu.isVisible())
        menu._pages["uno"].click()
        wait(60)
        self.assertEqual(seen, ["uno"])
        self.assertFalse(menu.isVisible())
        self.assertTrue(closed)

    def test_the_title_bar_has_the_gear(self):
        import qttitle

        host = QWidget()
        bar = qttitle.TitleBar(host, "MH3U NativePC")
        self.assertEqual(bar.btn_menu.kind, "gear")
        bar.resize(600, 38)
        self.assertFalse(bar.btn_menu.grab().isNull())


if __name__ == "__main__":
    unittest.main()
