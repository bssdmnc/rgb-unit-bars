import unittest
from unittest.mock import patch

from rgbunitbars.engine import Engine


class FakeDevice:
    row_tolerance = 0
    leds = [(0, 0)]
    name = "Test keyboard"

    def __init__(self, clock):
        self.clock = clock
        self.sent = []
        self.idle_at = []

    def prepare(self):
        pass

    def send(self, colors):
        self.sent.append(colors)

    def idle(self):
        self.idle_at.append(self.clock())

    def close(self):
        pass


class FakeLink:
    def __init__(self):
        self.read_count = 0

    def read(self):
        if self.read_count == 0:
            self.read_count += 1
            return (object(), object()), "ok"
        return None, "no-addon"

    def close(self):
        pass


class EngineIdleTests(unittest.TestCase):
    @patch("rgbunitbars.engine.OpenRGBServer")
    @patch("rgbunitbars.engine.render", return_value=[(1, 2, 3)])
    @patch("rgbunitbars.engine.WowLink", FakeLink)
    def test_keeps_last_frame_during_temporary_addon_detection_loss(self, _render, _server):
        now = [0.0]
        device = FakeDevice(lambda: now[0])
        engine = Engine()
        engine.open_device = lambda: device
        waits = [0]

        def wait(_seconds):
            now[0] += 1
            waits[0] += 1
            if waits[0] == 7:
                engine.stop_event.set()
            return False

        engine.wait = wait
        with patch("rgbunitbars.engine.time.monotonic", side_effect=lambda: now[0]):
            engine.loop()

        self.assertEqual(device.idle_at, [6.0])
        self.assertGreaterEqual(len(device.sent), 5)


if __name__ == "__main__":
    unittest.main()
