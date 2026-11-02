import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "launcher"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import core  # noqa: E402


class CheatsEnvTests(unittest.TestCase):
    def test_nothing_when_the_section_is_off(self):
        self.assertEqual(core.build_cheats_env({"cheat_onehit": True, "cheat_sharp": True}), "")
        self.assertEqual(core.build_cheats_env({"cheats_enabled": False, "cheat_sharp": True}), "")

    def test_nothing_when_no_cheat_is_chosen(self):
        self.assertEqual(core.build_cheats_env({"cheats_enabled": True}), "")

    def test_the_chosen_ones_in_the_order_of_the_table_with_their_multipliers(self):
        config = {"cheats_enabled": True, "cheat_money": True, "cheat_money_value": 5, "cheat_onehit": True, "cheat_sharp": True}
        self.assertEqual(core.build_cheats_env(config), "onehit=1000,sharp,money=5")

    def test_a_multiplier_that_is_not_a_number_or_out_of_range_is_put_back_in_range(self):
        c = next(c for c in core.CHEATS if c["id"] == "onehit")
        self.assertEqual(core.cheat_value({"cheat_onehit_value": "abc"}, c), 1000)
        self.assertEqual(core.cheat_value({"cheat_onehit_value": "1"}, c), 2)
        self.assertEqual(core.cheat_value({"cheat_onehit_value": "999999999"}, c), 100000)
        self.assertEqual(core.cheat_value({"cheat_onehit_value": " 250 "}, c), 250)

    def test_every_cheat_has_what_the_window_and_the_engine_need(self):
        ids = [c["id"] for c in core.CHEATS]
        self.assertEqual(len(ids), len(set(ids)), "ids are unique")
        for c in core.CHEATS:
            self.assertTrue(c["id"].isalpha() and c["id"].islower(), "the engine reads the id from MH3U_CHEATS")
            self.assertTrue(c["label"] and c["hint"])
            if c.get("value"):
                self.assertLess(c["value"]["min"], c["value"]["max"])
                self.assertTrue(c["value"]["min"] <= c["value"]["default"] <= c["value"]["max"])

    def test_the_package_hooks_have_the_hooks_the_cheats_need(self):
        here = os.path.dirname(__file__)
        with open(os.path.join(here, "..", "package", "mods", "hooks.txt"), encoding="utf-8") as f:
            names = {line.split("#")[0].split()[-1] for line in f if line.split("#")[0].strip()}
        for hook in ("hit_resolve", "sharp_change", "money_add", "item_to_pouch"):
            self.assertIn(hook, names)


if __name__ == "__main__":
    unittest.main()
