import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "launcher"))
import core  # noqa: E402


class RotateLogTests(unittest.TestCase):
    def test_previous_log_is_kept_next_to_the_new_one(self):
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, "mh3u_latest.log")
            with open(log, "w") as f:
                f.write("long session")
            core.rotate_log(log)
            self.assertFalse(os.path.exists(log))
            with open(os.path.join(d, "mh3u_anterior.log")) as f:
                self.assertEqual(f.read(), "long session")

    def test_a_second_launch_replaces_the_kept_log(self):
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, "mh3u_latest.log")
            for text in ("first", "second"):
                with open(log, "w") as f:
                    f.write(text)
                core.rotate_log(log)
            with open(os.path.join(d, "mh3u_anterior.log")) as f:
                self.assertEqual(f.read(), "second")

    def test_nothing_to_rotate_is_fine_and_an_empty_log_does_not_wipe_the_kept_one(self):
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, "mh3u_latest.log")
            core.rotate_log(log)
            with open(os.path.join(d, "mh3u_anterior.log"), "w") as f:
                f.write("keep me")
            open(log, "w").close()
            core.rotate_log(log)
            with open(os.path.join(d, "mh3u_anterior.log")) as f:
                self.assertEqual(f.read(), "keep me")


class OwnAddressTests(unittest.TestCase):
    def logic(self, **config):
        obj = core.LauncherLogic.__new__(core.LauncherLogic)
        obj.config = config
        return obj

    def test_joining_with_the_local_address_is_flagged(self):
        o = self.logic(online_enabled=True, online_mode="client", online_server="127.0.0.1")
        self.assertEqual(o._own_address_when_joining(), "127.0.0.1")

    def test_joining_with_an_own_ip_is_flagged(self):
        o = self.logic(online_enabled=True, online_mode="client", online_server="26.1.2.3")
        with mock.patch.object(core, "get_local_ip_addresses", return_value=["26.1.2.3 (Radmin VPN)", "127.0.0.1 (Localhost / Mismo PC)"]):
            self.assertEqual(o._own_address_when_joining(), "26.1.2.3")

    def test_a_friends_address_or_host_mode_or_online_off_is_not(self):
        with mock.patch.object(core, "get_local_ip_addresses", return_value=["26.1.2.3 (Radmin VPN)"]):
            self.assertEqual(self.logic(online_enabled=True, online_mode="client", online_server="26.9.9.9")._own_address_when_joining(), "")
            self.assertEqual(self.logic(online_enabled=True, online_mode="host", online_server="127.0.0.1")._own_address_when_joining(), "")
            self.assertEqual(self.logic(online_enabled=False, online_mode="client", online_server="127.0.0.1")._own_address_when_joining(), "")


class IpLabelTests(unittest.TestCase):
    def test_lan_addresses_say_they_only_work_on_the_same_network(self):
        out = '[{"IPAddress":"192.168.1.5","InterfaceAlias":"Wi-Fi"},{"IPAddress":"26.1.2.3","InterfaceAlias":"Radmin VPN"}]'
        with mock.patch.object(core.subprocess, "check_output", return_value=out):
            ips = core.get_local_ip_addresses()
        self.assertTrue(ips[0].startswith("26.1.2.3") and "Radmin" in ips[0])
        self.assertIn("solo misma red local", ips[1])
        self.assertTrue(ips[-1].startswith("127.0.0.1"))


if __name__ == "__main__":
    unittest.main()
