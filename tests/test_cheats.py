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

    def test_the_mods_go_to_the_engine_on_their_own_and_after_the_cheats(self):
        # the cheats' master switch does not hold them back: they only read
        self.assertEqual(core.build_cheats_env({"mod_monsterhp": True}), "monsterhp")
        self.assertEqual(core.build_cheats_env({"mod_dmgmeter": True, "mod_monsterhp": True}), "monsterhp,dmgmeter")
        config = {"cheats_enabled": True, "cheat_sharp": True, "mod_dmgmeter": True}
        self.assertEqual(core.build_cheats_env(config), "sharp,dmgmeter")
        # off with the cheats off, and each one apart from the other
        self.assertEqual(core.build_cheats_env({"cheats_enabled": False, "cheat_sharp": True, "mod_monsterhp": True}), "monsterhp")

    def test_a_configuration_from_when_the_mods_were_cheats_keeps_them_on(self):
        self.assertTrue(core.mod_enabled({"cheat_monsterhp": True}, "monsterhp"))
        self.assertFalse(core.mod_enabled({"cheat_monsterhp": True, "mod_monsterhp": False}, "monsterhp"))
        self.assertFalse(core.mod_enabled({}, "dmgmeter"))

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


class StaleBuildTests(unittest.TestCase):
    """A hooks list that changed (new cheats) must make the C code again, or the new hooks never get into game.dll."""

    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "out")
        os.makedirs(self.out)
        self.hooks = os.path.join(self.tmp.name, "hooks.txt")
        self._saved = core.hooks_list_path
        core.hooks_list_path = lambda: self.hooks

    def tearDown(self):
        core.hooks_list_path = self._saved
        self.tmp.cleanup()

    def write(self, name, text):
        with open(os.path.join(self.out, name) if name != "hooks" else self.hooks, "w", encoding="utf-8") as f:
            f.write(text)

    def built(self):
        """An output folder as a finished build leaves it."""
        self.write("hooks", "0x02129ef4 hit_resolve  # a comment\n")
        self.write("game.h", "")
        self.write("game.dll.rev", core.TRANSLATOR_REV)
        self.write("game.dll.hooks", core.hooks_fingerprint(self.hooks))

    def test_the_fingerprint_ignores_comments_blank_lines_and_spacing_but_not_entries(self):
        self.write("hooks", "0x1000 a\n0x2000   b # x\n")
        base = core.hooks_fingerprint(self.hooks)
        self.write("hooks", "# top\n\n0x1000 a   \n  0x2000 b\n")
        self.assertEqual(core.hooks_fingerprint(self.hooks), base)
        self.write("hooks", "0x1000 a\n0x2000 b\n0x3000 c\n")
        self.assertNotEqual(core.hooks_fingerprint(self.hooks), base)

    def test_a_finished_build_is_current_and_is_not_translated_again(self):
        self.built()
        self.assertTrue(core.game_dll_is_current(self.out))
        self.assertFalse(core.needs_translation(self.out))

    def test_a_new_hook_makes_the_build_stale_and_the_code_is_made_again(self):
        self.built()
        self.write("hooks", "0x02129ef4 hit_resolve\n0x0285f530 sharp_change\n")
        self.assertFalse(core.game_dll_is_current(self.out))
        self.assertTrue(core.needs_translation(self.out))

    def test_an_older_translator_is_stale_and_is_translated_again(self):
        self.built()
        self.write("game.dll.rev", "1")
        self.assertTrue(core.needs_translation(self.out))

    def test_a_build_from_before_the_stamp_is_current_while_the_translator_revision_matches(self):
        self.built()
        os.remove(os.path.join(self.out, "game.dll.hooks"))
        self.assertTrue(core.game_dll_is_current(self.out))

    def test_nothing_made_yet_is_translated(self):
        self.assertTrue(core.needs_translation(self.out))


class CheatHooksInTheBuildTests(unittest.TestCase):
    """The cheats do nothing when the build was translated without their hooks: that is looked at when playing."""

    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.out = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def build_hooks(self, text):
        with open(os.path.join(self.out, "hooks.txt"), "w", encoding="utf-8") as f:
            f.write(text)

    def all_on(self):
        config = {"cheats_enabled": True}
        config.update({f"cheat_{c['id']}": True for c in core.CHEATS})
        config.update({f"mod_{m['id']}": True for m in core.MODS})
        return config

    def test_the_hooks_of_a_build_are_read_by_name(self):
        self.build_hooks("0x02129ef4 hit_resolve\n0x0219c720 money_add\n")
        self.assertEqual(core.build_hook_names(self.out), {"hit_resolve", "money_add"})
        self.assertEqual(core.build_hook_names(os.path.join(self.out, "nothing")), set())

    def test_a_build_without_hooks_lacks_every_hook_the_cheats_need(self):
        self.build_hooks("")
        self.assertEqual(core.missing_cheat_hooks(self.all_on(), self.out), ["hit_resolve", "item_to_pouch", "money_add", "monster_init", "sharp_change"])

    def test_the_mods_need_their_hooks_even_with_the_cheats_off(self):
        self.build_hooks("")
        self.assertEqual(core.missing_cheat_hooks({"cheats_enabled": False, "mod_monsterhp": True}, self.out), ["monster_init"])
        self.assertEqual(core.missing_cheat_hooks({"mod_dmgmeter": True}, self.out), ["hit_resolve", "monster_init"])

    def test_only_the_hooks_of_the_cheats_that_are_on_are_needed(self):
        self.build_hooks("0x0219c720 money_add\n")
        self.assertEqual(core.missing_cheat_hooks({"cheats_enabled": True, "cheat_money": True}, self.out), [])
        self.assertEqual(core.missing_cheat_hooks({"cheats_enabled": True, "cheat_sharp": True}, self.out), ["sharp_change"])
        self.assertEqual(core.missing_cheat_hooks({"cheats_enabled": False, "cheat_sharp": True}, self.out), [])

    def test_every_cheat_has_its_hooks_named_and_they_are_in_the_package_list(self):
        self.assertEqual(set(core.CHEAT_HOOKS), {c["id"] for c in core.CHEATS} | {m["id"] for m in core.MODS})
        here = os.path.dirname(__file__)
        with open(os.path.join(here, "..", "package", "mods", "hooks.txt"), encoding="utf-8") as f:
            names = {line.split("#")[0].split()[-1] for line in f if line.split("#")[0].strip()}
        for hooks in core.CHEAT_HOOKS.values():
            self.assertTrue(set(hooks) <= names)

    def test_a_build_marked_stale_is_made_again(self):
        for name, text in (("game.h", ""), ("game.dll.rev", core.TRANSLATOR_REV)):
            with open(os.path.join(self.out, name), "w", encoding="utf-8") as f:
                f.write(text)
        self.assertTrue(core.game_dll_is_current(self.out))
        core.mark_build_stale(self.out)
        self.assertFalse(core.game_dll_is_current(self.out))
        self.assertTrue(core.needs_translation(self.out))


if __name__ == "__main__":
    unittest.main()
