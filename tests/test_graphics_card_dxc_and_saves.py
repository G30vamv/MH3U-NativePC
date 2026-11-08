# SPDX-License-Identifier: AGPL-3.0-only
import hashlib
import os
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "launcher"))
import core  # noqa: E402
import dxc_installer  # noqa: E402


def _sha(data):
    return hashlib.sha256(data).hexdigest()


class GraphicsCardListTests(unittest.TestCase):
    def test_real_cards_are_listed_once_and_virtual_ones_are_left_out(self):
        out = "NVIDIA GeForce RTX 4070\r\nAMD Radeon(TM) Graphics\r\nMicrosoft Basic Render Driver\r\nParsec Virtual Display Adapter\r\nNVIDIA GeForce RTX 4070\r\n\r\n"
        with mock.patch.object(core.sys, "platform", "win32"), mock.patch.object(core.subprocess, "run") as run:
            run.return_value = mock.Mock(stdout=out)
            self.assertEqual(core.list_graphics_cards(), ["NVIDIA GeForce RTX 4070", "AMD Radeon(TM) Graphics"])

    def test_a_failure_to_ask_windows_gives_an_empty_list(self):
        with mock.patch.object(core.sys, "platform", "win32"), mock.patch.object(core.subprocess, "run", side_effect=OSError("no powershell")):
            self.assertEqual(core.list_graphics_cards(), [])


class DxcInstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.members = {"bin/x64/dxcompiler.dll": b"COMPILER", "bin/x64/dxil.dll": b"SIGNER", "LICENSE-MS.txt": b"TERMS"}
        self.zip = os.path.join(self.dir, "dxc.zip")
        with zipfile.ZipFile(self.zip, "w") as z:
            for name, data in self.members.items():
                z.writestr(name, data)
        self.files = {
            "bin/x64/dxcompiler.dll": ("dxcompiler.dll", _sha(b"COMPILER")),
            "bin/x64/dxil.dll": ("dxil.dll", _sha(b"SIGNER")),
            "LICENSE-MS.txt": ("dxc_LICENSE-MS.txt", _sha(b"TERMS")),
        }
        self.dest = os.path.join(self.dir, "launcher")
        os.makedirs(self.dest)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_two_dlls_and_the_license_are_installed_beside_the_exe(self):
        self.assertFalse(dxc_installer.installed(self.dest))
        steps = []
        dxc_installer.install(self.dest, progress=steps.append, source=self.zip, files=self.files)
        self.assertTrue(dxc_installer.installed(self.dest))
        with open(os.path.join(self.dest, "dxil.dll"), "rb") as f:
            self.assertEqual(f.read(), b"SIGNER")
        self.assertTrue(os.path.isfile(os.path.join(self.dest, "dxc_LICENSE-MS.txt")))
        self.assertAlmostEqual(steps[-1], 1.0)

    def test_a_file_that_does_not_match_its_sha256_is_not_installed(self):
        files = dict(self.files)
        files["bin/x64/dxil.dll"] = ("dxil.dll", "0" * 64)
        with self.assertRaises(dxc_installer.DxcError):
            dxc_installer.install(self.dest, source=self.zip, files=files)
        self.assertFalse(os.path.exists(os.path.join(self.dest, "dxil.dll")))
        self.assertFalse([n for n in os.listdir(self.dest) if n.endswith(".part")])

    def test_the_pinned_files_are_the_ones_of_the_official_release(self):
        self.assertIn("microsoft/DirectXShaderCompiler/releases/download/", dxc_installer.URL)
        self.assertEqual({v[0] for v in dxc_installer.FILES.values()}, {"dxcompiler.dll", "dxil.dll", "dxc_LICENSE-MS.txt"})
        for _, digest in dxc_installer.FILES.values():
            self.assertEqual(len(digest), 64)

    def test_the_terms_the_player_reads_ship_with_the_launcher(self):
        assets = os.path.join(os.path.dirname(__file__), "..", "launcher", "assets")
        text = dxc_installer.license_text(assets)
        self.assertIn("MICROSOFT SOFTWARE LICENSE TERMS", text)
        with open(os.path.join(assets, dxc_installer.LICENSE_ASSET), "rb") as f:
            self.assertEqual(_sha(f.read()), dxc_installer.FILES["LICENSE-MS.txt"][1])


class SeparateSaveTests(unittest.TestCase):
    def test_the_saved_games_folder_follows_the_option(self):
        cfg = {"out_dir": os.path.join("C:\\", "mh3u", "c"), "separate_save": False}
        self.assertEqual(core.save_dir_for(cfg), os.path.join(cfg["out_dir"], "save"))
        cfg["separate_save"] = True
        self.assertEqual(core.save_dir_for(cfg, base_dir="L"), os.path.join("L", core.SEPARATE_SAVE_DIR))

    def test_the_hunter_name_is_read_from_the_folder_in_use(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(core, "read_hunter_name_from_file", side_effect=lambda p: "Aparte"):
            other = os.path.join(d, "partidas_aparte")
            os.makedirs(other)
            open(os.path.join(other, "user1"), "wb").close()
            self.assertIsNone(core.get_hunter_name_from_save(d))  # the usual folder has none
            self.assertEqual(core.get_hunter_name_from_save(d, other), "Aparte")


class JoiningStopsOwnServerTests(unittest.TestCase):
    def _logic(self, running):
        logic = core.LauncherLogic.__new__(core.LauncherLogic)
        logic.server_process = mock.Mock() if running else None
        logic._stop_server_process = mock.Mock(side_effect=lambda: setattr(logic, "server_process", None))
        logic._find_server_exe = mock.Mock(return_value="server.exe")
        logic._log = mock.Mock()
        logic.btn_toggle_server = mock.Mock()
        logic.lbl_server_status = mock.Mock()
        return logic

    def test_a_server_left_running_is_stopped_and_shown_as_off(self):
        logic = self._logic(True)
        logic._stop_own_server_for_client()
        logic._stop_server_process.assert_called_once()
        self.assertIn("Inactivo", logic.lbl_server_status.configure.call_args.kwargs["text"])
        logic._log.assert_called()

    def test_an_orphan_of_an_old_session_is_also_cleared(self):
        logic = self._logic(False)
        logic._stop_own_server_for_client()
        logic._stop_server_process.assert_called_once()  # it also kills a stale server.exe of this folder

    def test_the_remote_client_branch_calls_it(self):
        src = open(os.path.join(os.path.dirname(__file__), "..", "launcher", "core.py"), encoding="utf-8").read()
        branch = src.split('env["MH3U_ONLINE_MODE"] = "client"')[0][-400:]
        self.assertIn("_stop_own_server_for_client()", branch)


class DxcWarningTests(unittest.TestCase):
    def _logic(self, **cfg):
        logic = core.LauncherLogic.__new__(core.LauncherLogic)
        logic.config = {"gfx_backend": "dx12", **cfg}
        logic.save_config = mock.Mock()
        logic.start_install_dxc = mock.Mock()
        return logic

    def _run(self, logic, installed=False, answer=False):
        with mock.patch.object(core.dxc_installer, "installed", return_value=installed), mock.patch.object(
            core.messagebox, "askyesno", return_value=answer
        ) as ask:
            return logic._dxc_ok_to_play(), ask

    def test_vulkan_or_installed_helper_never_asks(self):
        ok, ask = self._run(self._logic(gfx_backend="vulkan"))
        self.assertTrue(ok)
        ask.assert_not_called()
        ok, ask = self._run(self._logic(), installed=True)
        self.assertTrue(ok)
        ask.assert_not_called()

    def test_yes_installs_and_does_not_start_the_game(self):
        logic = self._logic()
        ok, _ = self._run(logic, answer=True)
        self.assertFalse(ok)
        logic.start_install_dxc.assert_called_once()

    def test_no_starts_the_game_and_is_remembered(self):
        logic = self._logic()
        ok, _ = self._run(logic, answer=False)
        self.assertTrue(ok)
        self.assertTrue(logic.config["dxc_declined"])
        self.assertEqual(logic.config["gfx_backend"], "dx12")  # no fallback to Vulkan: it stays on DirectX 12 until they choose again
        ok, ask = self._run(logic)  # the next time it is not asked
        self.assertTrue(ok)
        ask.assert_not_called()

    def test_choosing_directx_12_again_asks_again(self):
        logic = self._logic(dxc_declined=True)
        logic.config["gfx_backend"] = "vulkan"
        logic.save_config = mock.Mock()
        logic.lbl_quick_backend = mock.Mock()
        logic.on_backend_changed("DirectX 12 (DX12)")
        self.assertFalse(logic.config["dxc_declined"])
        self.assertEqual(logic.config["gfx_backend"], "dx12")

    def test_play_checks_it_before_anything_else_starts(self):
        src = open(os.path.join(os.path.dirname(__file__), "..", "launcher", "core.py"), encoding="utf-8").read()
        lines = [l.strip() for l in src.splitlines()]
        self.assertLess(lines.index("if not self._dxc_ok_to_play():"), lines.index("self._offer_hidhide_access()"))


if __name__ == "__main__":
    unittest.main()
