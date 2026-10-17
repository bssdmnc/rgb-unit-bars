import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from rgbunitbars.openrgb_server import OpenRGBServer


class OpenRGBServerTests(unittest.TestCase):
    @patch("rgbunitbars.openrgb_server.time.sleep")
    @patch("rgbunitbars.openrgb_server.server_running", side_effect=[False, False, True])
    @patch("rgbunitbars.openrgb_server.time.monotonic", side_effect=[0, 0, 0, 0])
    def test_ensure_waits_for_starting_server(self, monotonic, server_running, sleep):
        server = OpenRGBServer()
        server.process = SimpleNamespace(poll=lambda: None)

        self.assertTrue(server.ensure())
        self.assertEqual(server_running.call_count, 3)
        sleep.assert_called_once_with(0.25)

    @patch("rgbunitbars.openrgb_server.time.sleep")
    @patch("rgbunitbars.openrgb_server.server_running", return_value=False)
    @patch("rgbunitbars.openrgb_server.time.monotonic", return_value=0)
    def test_ensure_stops_waiting_if_server_process_exits(self, monotonic, server_running, sleep):
        server = OpenRGBServer()
        server.process = SimpleNamespace(poll=Mock(side_effect=[None, 1]))

        self.assertFalse(server.ensure())
        self.assertEqual(server_running.call_count, 2)
        sleep.assert_not_called()

    @patch("rgbunitbars.openrgb_server.server_running", return_value=True)
    def test_ensure_returns_immediately_when_server_is_already_running(self, server_running):
        server = OpenRGBServer()

        self.assertTrue(server.ensure())
        server_running.assert_called_once_with("127.0.0.1", 6742)


if __name__ == "__main__":
    unittest.main()
