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

    def test_a_page_reveal_takes_its_effect_off_and_leaves_the_widget_in_place(self):
        import qtanim

        qtanim._windows_allows = True
        qtanim.set_user_choice(True)
        host = QWidget()
        host.resize(300, 200)
        w = QWidget(host)
        w.setGeometry(10, 20, 100, 50)
        host.show()
        qtanim.reveal(w, 60, 18)
        self.assertIsNotNone(w.graphicsEffect())
        wait(300)
        self.assertIsNone(w.graphicsEffect())  # an effect left on would make every repaint slower
        self.assertEqual((w.x(), w.y()), (10, 20))

    def test_nothing_runs_when_animations_are_off(self):
        import qtanim

        qtanim.set_user_choice(False)
        w = QWidget()
        w.show()
        qtanim.reveal(w, 60, 18)
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

    def test_tabs_show_their_name_without_the_icon_and_the_pill_follows_the_page(self):
        import qtshim
        from qtshim import TabView

        self.assertEqual(qtshim.plain("  🎮 Principal  "), "Principal")
        self.assertEqual(qtshim.plain("  🛠️ Configuración Gráfica  "), "Configuración Gráfica")
        self.assertEqual(qtshim.plain("Sin icono"), "Sin icono")
        tv = TabView()
        a, b = QWidget(), QWidget()
        tv.add("  🎮 Uno  ", a)
        tv.add("  ⚙️ Dos  ", b)
        tv.resize(600, 300)
        tv.show()
        wait(50)
        self.assertTrue(tv.bar.isVisible())
        self.assertEqual(tv._buttons["🎮 Uno"].text(), "Uno")
        self.assertEqual(tv.current(), "🎮 Uno")
        first = tv.bar.pill.left()
        tv.animate = True
        tv.set("  ⚙️ Dos  ")
        self.assertEqual(tv.current(), "⚙️ Dos")
        wait(450)  # the pill has slid to the second tab
        self.assertGreater(tv.bar.pill.left(), first)
        self.assertAlmostEqual(tv.bar.pill.left(), tv._buttons["⚙️ Dos"].geometry().left(), delta=1)

    def test_the_menu_holds_switches_that_stay_open_and_actions_that_close_it(self):
        import qtmenu

        host = QWidget()
        host.show()
        menu = qtmenu.SettingsMenu(host)
        seen = []
        menu.add_title("OPCIONES")
        sw = menu.add_switch("Animaciones", True, lambda: seen.append("sw"), "tip")
        menu.add_separator()
        menu.add_action("Buscar", lambda: seen.append("act"))
        closed = []
        menu.on_hidden = lambda: closed.append(1)
        self.assertEqual(sw.get(), 1)
        self.assertEqual(sw.toolTip(), "tip")
        menu.popup_below(host)
        self.assertTrue(menu.isVisible())
        sw.click()
        self.assertTrue(menu.isVisible())  # a switch does not close the menu
        self.assertEqual(sw.get(), 0)
        menu.findChildren(qtmenu._Row)[0].click()
        wait(80)
        self.assertEqual(seen, ["sw", "act"])
        self.assertFalse(menu.isVisible())
        self.assertTrue(closed)

    def test_a_switch_knob_slides_when_animations_are_on_and_jumps_when_off(self):
        import qtanim
        from qtshim import Switch

        host = QWidget()
        sw = Switch("x")
        sw.setParent(host)
        host.show()
        qtanim._windows_allows = True
        qtanim.set_user_choice(True)
        sw.click()
        wait(40)
        self.assertTrue(0.0 < sw._knob <= 1.2)  # on its way (it may overshoot a little)
        wait(400)
        self.assertAlmostEqual(sw._knob, 1.0, delta=0.02)
        qtanim.set_user_choice(False)
        sw.click()
        self.assertEqual(sw._knob, 0.0)
        qtanim.set_user_choice(True)

    def test_the_title_bar_has_the_gear(self):
        import qttitle

        host = QWidget()
        bar = qttitle.TitleBar(host, "MH3U NativePC")
        self.assertEqual(bar.btn_menu.kind, "gear")
        bar.resize(600, 38)
        self.assertFalse(bar.btn_menu.grab().isNull())


class SelectorAndTipTests(unittest.TestCase):
    def test_a_selector_has_the_sliding_pill_of_the_tabs(self):
        import qtanim
        from qtshim import Segmented

        qtanim._windows_allows = True
        qtanim.set_user_choice(True)
        picked = []
        seg = Segmented(["Uno", "Dos", "Tres"], picked.append)
        seg.resize(420, 40)
        seg.set("Uno")
        seg.show()
        wait(60)
        first = seg.pill.left()
        seg._buttons["Tres"].click()
        wait(450)
        self.assertEqual(seg.get(), "Tres")
        self.assertEqual(picked, ["Tres"])
        self.assertGreater(seg.pill.left(), first)
        self.assertAlmostEqual(seg.pill.left(), seg._buttons["Tres"].geometry().left(), delta=1)

    def test_a_tooltip_appears_in_the_launchers_own_popup_and_goes_when_the_mouse_leaves(self):
        import qtanim
        from PySide6.QtCore import QEvent, QPoint
        from PySide6.QtGui import QHelpEvent

        qtanim._windows_allows = True
        manager = qtanim.TipManager()
        w = QWidget()
        w.setToolTip("Explicación de la opción")
        w.show()
        ev = QHelpEvent(QEvent.Type.ToolTip, QPoint(5, 5), w.mapToGlobal(QPoint(5, 5)))
        self.assertTrue(manager.eventFilter(w, ev))  # taken over: Qt's own tooltip does not show
        self.assertTrue(manager.popup.isVisible())
        self.assertIn("Explicación", manager.popup.label.text())
        manager.eventFilter(w, QEvent(QEvent.Type.Leave))
        self.assertFalse(manager.popup.isVisible())
        # a widget without an explanation is left to its parent
        plain = QWidget()
        self.assertFalse(manager.eventFilter(plain, QHelpEvent(QEvent.Type.ToolTip, QPoint(1, 1), QPoint(1, 1))))

    def test_the_hunter_name_boxes_are_gone(self):
        base = os.path.join(os.path.dirname(__file__), "..", "launcher")
        window = open(os.path.join(base, "mh3u_launcher_qt.py"), encoding="utf-8").read()
        logic = open(os.path.join(base, "core.py"), encoding="utf-8").read()
        self.assertNotIn("entry_hunter_name", window)
        self.assertNotIn("entry_hunter_name", logic)
        self.assertNotIn("MH3U_SWKBD_TEXT", logic)  # a new hunter types the name in the game's own keyboard

    def test_a_panel_unfolds_and_folds_away_instead_of_jumping(self):
        import qtanim
        import qtglass
        from PySide6.QtWidgets import QVBoxLayout

        qtanim._windows_allows = True
        qtanim.set_user_choice(True)
        host = QWidget()
        lay = QVBoxLayout(host)
        a = qtglass.GlassPanel("card", 16)
        b = qtglass.GlassPanel("card", 16)
        for panel in (a, b):
            inner = QVBoxLayout(panel)
            inner.addWidget(QWidget())
            panel.setMinimumHeight(60)
            lay.addWidget(panel)
        b.hide()
        host.resize(300, 400)
        host.show()
        wait(40)
        a.grid_remove()
        b.grid()
        wait(60)
        self.assertTrue(b.isVisible())
        self.assertLess(b.maximumHeight(), 16777215)  # still unfolding
        wait(450)
        self.assertFalse(a.isVisible())
        self.assertTrue(b.isVisible())
        self.assertEqual(b.maximumHeight(), 16777215)  # normal size limits are back
        self.assertEqual(a.maximumHeight(), 16777215)
        self.assertIsNone(b.graphicsEffect())
        qtanim.set_user_choice(False)
        b.grid_remove()
        self.assertFalse(b.isVisible())  # with animations off it is immediate
        qtanim.set_user_choice(True)

    def test_a_resize_in_the_middle_of_a_pill_slide_does_not_cut_it_short(self):
        import qtanim
        from PySide6.QtCore import QRectF
        from qtshim import Segmented

        qtanim._windows_allows = True
        qtanim.set_user_choice(True)
        seg = Segmented(["Uno", "Dos"], None)
        seg.resize(400, 40)
        seg.set("Uno")
        seg.show()
        wait(60)
        seg._buttons["Dos"].click()
        wait(60)
        seg.move_pill(QRectF(300, 4, 90, 32), False)  # what a layout change does while the pill is moving
        wait(450)
        self.assertAlmostEqual(seg.pill.left(), 300, delta=1)


if __name__ == "__main__":
    unittest.main()
