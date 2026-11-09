# SPDX-License-Identifier: AGPL-3.0-only
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
LAUNCHER = os.path.join(os.path.dirname(__file__), "..", "launcher")
sys.path.insert(0, LAUNCHER)

import core  # noqa: E402
import i18n  # noqa: E402
import padmap  # noqa: E402


class TableTests(unittest.TestCase):
    def test_nothing_changed_gives_no_environment_variable(self):
        m = padmap.PadMap()
        self.assertTrue(m.is_default())
        self.assertEqual(m.to_env(), "")
        self.assertEqual(m.to_dict(), {})
        self.assertEqual(m.sources_of("A"), ["A"])

    def test_giving_a_button_to_an_action_takes_it_from_the_old_one_and_a_swap_takes_two_steps(self):
        m = padmap.PadMap()
        m.assign("B", "A")  # the button taken as B now does A
        self.assertEqual(m.sources_of("A"), ["B"])
        self.assertEqual(m.sources_of("B"), [], "nothing does B until the player says so")
        self.assertEqual(m.targets_of("A"), set(), "A's own button no longer does A: it was given to B")
        m.assign("A", "B")
        self.assertEqual((m.sources_of("A"), m.sources_of("B")), (["B"], ["A"]))
        self.assertEqual(m.to_env(), "A>B,B>A")
        self.assertFalse(m.is_default())

    def test_a_button_does_one_thing_and_clearing_an_action_leaves_it_with_no_button(self):
        m = padmap.PadMap()
        m.assign("X", "ZL")
        self.assertEqual(m.targets_of("X"), {"ZL"})
        m.clear_target("ZL")
        self.assertEqual(m.sources_of("ZL"), [])
        self.assertEqual(m.to_env(), "X>,ZL>")
        m.reset()
        self.assertTrue(m.is_default())

    def test_the_config_round_trips_and_a_bad_one_is_cleaned(self):
        m = padmap.PadMap()
        m.assign("B", "A")
        m.assign("A", "B")
        m.clear_target("ZR")
        again = padmap.PadMap(json.loads(json.dumps(m.to_dict())))
        self.assertEqual(again.to_env(), m.to_env())
        bad = padmap.PadMap({"B": ["A", "Z"], "Q": ["A"], "X": "Y", "l3": ["r3"]})
        self.assertEqual(bad.targets_of("B"), {"A"}, "unknown names are left out")
        self.assertEqual(bad.targets_of("L3"), {"R3"}, "names are read in any case")
        self.assertEqual(bad.targets_of("X"), {"X"}, "something that is not a list is not used")
        self.assertTrue(padmap.PadMap("nonsense").is_default())

    def test_the_exported_file_is_read_back_and_other_files_are_refused(self):
        m = padmap.PadMap()
        m.assign("L", "ZL")
        back = padmap.PadMap.from_json(m.to_json())
        self.assertEqual(back.to_env(), m.to_env())
        self.assertIsNone(padmap.PadMap.from_json("not json"))
        self.assertIsNone(padmap.PadMap.from_json(json.dumps({"map": {"A": ["B"]}})))
        self.assertIsNone(padmap.PadMap.from_json("[1, 2]"))

    def test_the_engine_reads_what_the_launcher_writes(self):
        m = padmap.PadMap()
        m.assign("PLUS", "MINUS")
        m.assign("MINUS", "PLUS")
        m.assign("L3", "R3")
        env = m.to_env()
        self.assertEqual(env, "PLUS>MINUS,MINUS>PLUS,L3>R3,R3>")
        for pair in env.split(","):
            source, _, targets = pair.partition(">")
            self.assertIn(source, padmap.NAMES)
            for t in filter(None, targets.split("+")):
                self.assertIn(t, padmap.NAMES)

    def test_the_game_gets_the_variable_only_when_something_changed(self):
        m = padmap.PadMap({"B": ["A"]})
        self.assertEqual(padmap.PadMap(m.to_dict()).to_env(), "B>A")


class ListenerLineTests(unittest.TestCase):
    def test_lines_of_the_reader(self):
        p = padmap.parse_listener_line
        self.assertEqual(p("down A\n"), ("down", "A"))
        self.assertEqual(p("up zl"), ("up", "ZL"))
        self.assertIsNone(p("down Q"))
        self.assertEqual(p("gamepad: Xbox Controller"), ("pad", "Xbox Controller"))
        self.assertEqual(p("gamepad connected: Wireless Controller"), ("pad", "Wireless Controller"))
        self.assertEqual(
            p("[hid] gamepad read from the device: DualSense Wireless Controller (054c:0ce6, USB)"),
            ("pad", "DualSense Wireless Controller"),
        )
        self.assertIsNone(p("[gamepad] window in the background: reading the pad with XInput"))
        self.assertIsNone(p(""))

    def test_the_listener_reports_a_programs_lines_and_stops(self):
        tmp = tempfile.mkdtemp()
        try:
            exe = os.path.join(tmp, "fake.cmd")
            with open(exe, "w") as f:
                f.write("@echo off\r\necho gamepad: Test Pad 1>&2\r\necho down B\r\necho up B\r\nping -n 4 127.0.0.1 >nul\r\n")
            listener = padmap.PadListener(exe, "xbox")
            self.assertFalse(padmap.PadListener(os.path.join(tmp, "missing.exe")).start())
            self.assertTrue(listener.start())
            seen = []
            end = time.monotonic() + 8
            while len(seen) < 3 and time.monotonic() < end:
                seen += listener.poll()
                time.sleep(0.05)
            self.assertIn(("pad", "Test Pad"), seen)
            self.assertIn(("down", "B"), seen)
            self.assertIn(("up", "B"), seen)
            self.assertTrue(listener.running)
            listener.stop()
            self.assertFalse(listener.running)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class WindowTests(unittest.TestCase):
    """The Controls tab: pick an action, press a button on the pad, and the table, the config and the labels follow."""

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

        m.get_base_dir = lambda: cls.tmp
        cls.app = QApplication.instance() or QApplication([])
        cls.win = m.MH3ULauncherApp(cls.app)
        cls.win.window.show()
        cls.app.processEvents()
        # a reader that stays alive and says nothing: the test puts its events in the queue
        cls.fake = os.path.join(cls.tmp, "fake_tools.cmd")
        with open(cls.fake, "w") as f:
            f.write("@echo off\r\nping -n 30 127.0.0.1 >nul\r\n")
        cls.win.pad_listener = padmap.PadListener(cls.fake, "xbox")
        cls.win.pad_listener.start()

    @classmethod
    def tearDownClass(cls):
        cls.win.pad_listener.stop()
        cls.win._map_timer.stop()
        cls.win.window.close()
        core.get_base_dir = cls._base
        i18n.set_language("es")
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.win._reset_map()
        self.win.pad_listener.poll()

    def press(self, name):
        self.win.pad_listener.events.put(("down", name))
        self.win.pad_listener.events.put(("up", name))
        self.win._poll_pad()

    def test_picking_an_action_and_pressing_a_button_maps_it(self):
        w = self.win
        w._on_map_pick("A")
        self.assertEqual(w._map_target, "A")
        self.assertIn("Press a button", w.map_chips["A"].text())
        self.press("B")
        self.assertIsNone(w._map_target)
        self.assertEqual(w.pad_map.sources_of("A"), ["B"])
        self.assertEqual(w.map_chips["A"].text(), "Button B")
        self.assertEqual(w.config["pad_map"], {"A": [], "B": ["A"]})
        self.assertEqual(w.opt_map_profile.get(), "Personalizado")
        with open(os.path.join(self.tmp, "launcher_config.json")) as f:
            self.assertEqual(json.load(f)["pad_map"], {"A": [], "B": ["A"]})

    def test_a_button_pressed_with_no_action_picked_only_lights_the_picture(self):
        w = self.win
        w.pad_listener.events.put(("down", "ZL"))
        w._poll_pad()
        self.assertTrue(w.pad_map.is_default())
        self.assertIn("ZL", w.pad_diagram.pressed)
        w.pad_listener.events.put(("up", "ZL"))
        w._poll_pad()
        self.assertEqual(w.pad_diagram.pressed, set())

    def test_clearing_resetting_and_the_default_profile(self):
        w = self.win
        w._on_map_pick("ZR")
        self.press("R")
        self.assertEqual(w.pad_map.sources_of("ZR"), ["R"])
        w._clear_map_target("ZR")
        self.assertEqual(w.map_chips["ZR"].text(), "Unassigned")
        w._reset_map()
        self.assertTrue(w.pad_map.is_default())
        self.assertEqual(w.config["pad_map"], {})
        self.assertEqual(w.map_chips["ZR"].text(), "Button ZR")
        self.assertEqual(w.opt_map_profile.get(), "Predeterminado (Xbox)")

    def test_a_pick_that_gets_no_button_in_time_is_given_up(self):
        w = self.win
        w._on_map_pick("X")
        w._map_deadline = time.monotonic() - 1
        w._poll_pad()
        self.assertIsNone(w._map_target)
        self.assertTrue(w.pad_map.is_default())

    def test_the_game_is_started_with_the_map(self):
        w = self.win
        w._on_map_pick("A")
        self.press("B")
        self.assertEqual(padmap.PadMap(w.config["pad_map"]).to_env(), "A>,B>A")

    def test_the_pads_the_reader_names_are_listed(self):
        w = self.win
        w.pad_listener.events.put(("pad", "Test Pad"))
        w._poll_pad()
        self.assertIn("Test Pad", [w.opt_map_device.itemText(i) for i in range(w.opt_map_device.count())])


if __name__ == "__main__":
    unittest.main()
