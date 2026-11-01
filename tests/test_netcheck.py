import os
import socket
import struct
import sys
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "launcher"))
import netcheck  # noqa: E402

TOOLS = r"C:\MH3U Port\mh3u-tools.exe"
SERVER = r"C:\MH3U Port\server.exe"


def rule(program, action="Allow", profile="Private, Public", proto="UDP", enabled="True", name="x"):
    return {"Name": name, "Dir": "Inbound", "Action": action, "Enabled": enabled, "Profile": profile, "Program": program, "Proto": proto}


class AnalyzeTests(unittest.TestCase):
    def test_allowed_on_private_and_public_is_fine(self):
        rules = [rule(TOOLS), rule(SERVER, profile="Any", proto="Any")]
        self.assertEqual(netcheck.analyze_rules(rules, [TOOLS, SERVER]), [])

    def test_path_is_compared_without_case(self):
        self.assertEqual(netcheck.analyze_rules([rule(TOOLS.lower())], [TOOLS]), [])

    def test_block_rule_beats_allow(self):
        rules = [rule(TOOLS), rule(TOOLS, action="Block", profile="Public")]
        self.assertEqual(netcheck.analyze_rules(rules, [TOOLS]), [(TOOLS, "block", "Public")])

    def test_disabled_block_is_ignored(self):
        rules = [rule(TOOLS), rule(TOOLS, action="Block", enabled="False")]
        self.assertEqual(netcheck.analyze_rules(rules, [TOOLS]), [])

    def test_only_private_leaves_radmin_out(self):
        problems = netcheck.analyze_rules([rule(TOOLS, profile="Private")], [TOOLS])
        self.assertEqual(problems[0][:2], (TOOLS, "missing"))

    def test_two_rules_that_together_cover_both_profiles(self):
        rules = [rule(TOOLS, profile="Private"), rule(TOOLS, profile="Public")]
        self.assertEqual(netcheck.analyze_rules(rules, [TOOLS]), [])

    def test_rule_of_another_folder_does_not_count(self):
        self.assertEqual(netcheck.analyze_rules([rule(r"D:\old\mh3u-tools.exe")], [TOOLS])[0][1], "missing")

    def test_tcp_only_rule_does_not_cover_udp(self):
        self.assertEqual(netcheck.analyze_rules([rule(TOOLS, proto="TCP")], [TOOLS])[0][1], "missing")


class FixLinesTests(unittest.TestCase):
    def setUp(self):
        self.lines = netcheck.fix_lines("MH3U Online", [TOOLS, SERVER])

    def test_no_group_argument_anywhere(self):
        # netsh's "add rule" and "delete rule" have no group argument: those lines failed (hidden by >nul) and no rule was ever made
        self.assertFalse([ln for ln in self.lines if "group=" in ln])

    def test_every_add_has_only_arguments_netsh_knows(self):
        import re

        known = {"name", "dir", "action", "program", "service", "description", "enable", "profile", "localip", "remoteip",
                 "localport", "remoteport", "protocol", "interfacetype"}
        for ln in self.lines:
            if " add rule" in ln:
                self.assertLessEqual(set(re.findall(r"(\w+)=", ln)), known, ln)

    def test_netsh_answers_go_to_the_result_file(self):
        lines = netcheck.fix_lines("MH3U Online", [TOOLS], r"C:\Temp\r.txt")
        self.assertTrue(all("r.txt" in ln for ln in lines if " add rule" in ln))

    def test_enable_lines_use_the_names(self):
        lines = netcheck.enable_lines("MH3U Online", [TOOLS], False)
        self.assertIn('netsh advfirewall firewall set rule name="MH3U Online mh3u-tools.exe" new enable=no >nul 2>&1', lines)
        self.assertFalse([ln for ln in lines if "group=" in ln])

    def test_deletes_the_rules_windows_made_for_the_programs(self):
        self.assertIn(f'netsh advfirewall firewall delete rule name=all dir=in program="{TOOLS}" >nul 2>&1', self.lines)

    def test_ports_and_all_profiles(self):
        text = "\n".join(self.lines)
        for port in (1223, 1224, 10025, 33335):
            self.assertIn(f"localport={port} profile=any", text)
        self.assertNotIn("profile=private", text)

    def test_deletes_come_before_adds(self):
        kinds = ["d" if " delete rule" in ln else "a" for ln in self.lines]
        self.assertEqual(kinds, sorted(kinds, key=lambda k: k != "d"))


class ProbeTests(unittest.TestCase):
    def _server(self, answer=True):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("127.0.0.1", 0))
        sock.settimeout(3)

        def run():
            try:
                data, addr = sock.recvfrom(64)
                if answer:
                    t = struct.unpack(">IIII", data)[0]
                    sock.sendto(struct.pack(">IIII", t, addr[1], 0, 0), addr)
            except OSError:
                pass

        threading.Thread(target=run, daemon=True).start()
        return sock

    def test_answers_to_the_natcheck_request(self):
        sock = self._server()
        ok, ms = netcheck.udp_probe("127.0.0.1", sock.getsockname()[1], timeout=1.0, tries=1)
        sock.close()
        self.assertTrue(ok)
        self.assertGreaterEqual(ms, 1)

    def test_silence_is_a_failure(self):
        sock = self._server(answer=False)
        ok, _ = netcheck.udp_probe("127.0.0.1", sock.getsockname()[1], timeout=0.3, tries=1)
        sock.close()
        self.assertFalse(ok)

    def test_nothing_listening_is_a_failure(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        self.assertFalse(netcheck.udp_probe("127.0.0.1", port, timeout=0.3, tries=1)[0])


class FlowTests(unittest.TestCase):
    """The launcher's firewall step, with the firewall and the elevation replaced."""

    def make(self, states, answer=True):
        import queue
        from unittest import mock

        import core

        class L(core.LauncherLogic):
            pass

        o = L()
        o.ui_queue = queue.Queue()
        o.config = {}
        o.logs = []
        o.elevated = []
        o._fw_programs = lambda: [TOOLS, SERVER]
        o._queue_server_log = o.logs.append
        o._run_elevated_batch = lambda lines: o.elevated.append(lines) or True
        seq = iter(states)
        patches = [
            mock.patch.object(netcheck, "inspect_rules", lambda progs: next(seq)),
            mock.patch.object(core.messagebox, "askyesno", lambda *a, **k: answer),
        ]
        for pt in patches:
            pt.start()
            self.addCleanup(pt.stop)
        return o

    def test_fine_firewall_asks_nothing(self):
        o = self.make([[rule(TOOLS), rule(SERVER)]])
        self.assertTrue(o._ensure_firewall(ask=True))
        self.assertEqual(o.elevated, [])

    def test_block_rule_is_repaired_with_one_elevation(self):
        o = self.make([[rule(TOOLS, action="Block"), rule(SERVER)], [rule(TOOLS), rule(SERVER)]])
        self.assertTrue(o._ensure_firewall(ask=True))
        self.assertEqual(len(o.elevated), 1)

    def test_declining_leaves_it_alone(self):
        o = self.make([[rule(TOOLS, action="Block"), rule(SERVER)]], answer=False)
        self.assertFalse(o._ensure_firewall(ask=True))
        self.assertEqual(o.elevated, [])

    def test_still_wrong_after_the_repair_is_reported(self):
        bad = [rule(TOOLS, action="Block"), rule(SERVER)]
        o = self.make([bad, bad])
        self.assertFalse(o._ensure_firewall(ask=False))
        self.assertTrue(any("sigue mal" in m for m in o.logs))

    def test_unreadable_firewall_does_not_block_playing(self):
        o = self.make([None])
        self.assertIsNone(o._ensure_firewall(ask=True))

    def test_check_then_continues_the_launch(self):
        o = self.make([[rule(TOOLS), rule(SERVER)]])
        called = []
        o._check_firewall_then(lambda: called.append(1))
        kind, (_ms, fn) = o.ui_queue.get(timeout=5)
        self.assertEqual(kind, "call")
        fn()
        self.assertEqual(called, [1])
        self.assertTrue(o._fw_session_ok)


if __name__ == "__main__":
    unittest.main()
