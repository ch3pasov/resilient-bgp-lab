"""Exercise route selection with synthetic command output; never invoke Docker."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "test_link_failure.py"
spec = importlib.util.spec_from_file_location("link_failure", SOURCE)
link_failure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(link_failure)


class NextHopTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(
            link_failure, "run_command", side_effect=AssertionError("Docker must not run")
        ))
        self.sleep = self.enterContext(patch.object(link_failure.time, "sleep"))

    def test_address_prefix_is_not_the_expected_next_hop(self):
        with patch.object(link_failure, "get_route", return_value=
                          "192.168.0.2 via 10.0.1.10 dev eth1"), \
             patch.object(link_failure.time, "monotonic", side_effect=[0, 0, 16]):
            self.assertFalse(link_failure.wait_for_next_hop("10.0.1.1"))

    def test_polling_continues_until_the_exact_next_hop_arrives(self):
        with patch.object(link_failure, "get_route", side_effect=[
            "192.168.0.2 via 10.0.1.10 dev eth1",
            "192.168.0.2 via 10.0.1.1 dev eth1",
        ]) as route, patch.object(link_failure.time, "monotonic", side_effect=[0, 0, 1]):
            self.assertTrue(link_failure.wait_for_next_hop("10.0.1.1"))
        self.assertEqual(route.call_count, 2)
        self.sleep.assert_called_once_with(link_failure.POLL_INTERVAL_SECONDS)

    def test_exact_gateway_is_found_in_normal_and_multiline_routes(self):
        for output in [
            "192.168.0.2 via 10.0.1.1 dev eth1 proto bgp",
            "192.168.0.2 proto bgp\n  nexthop via 10.0.1.1 dev eth1 weight 1",
        ]:
            with self.subTest(output=output), \
                 patch.object(link_failure, "get_route", return_value=output), \
                 patch.object(link_failure.time, "monotonic", side_effect=[0, 0]):
                self.assertTrue(link_failure.wait_for_next_hop("10.0.1.1"))
        self.sleep.assert_not_called()

    def test_connected_or_absent_route_does_not_supply_a_gateway(self):
        for output in ["", "192.168.0.2 dev eth1 src 10.0.1.1"]:
            with self.subTest(output=output), \
                 patch.object(link_failure, "get_route", return_value=output), \
                 patch.object(link_failure.time, "monotonic", side_effect=[0, 0, 16]):
                self.assertFalse(link_failure.wait_for_next_hop("10.0.1.1"))


if __name__ == "__main__":
    unittest.main()
