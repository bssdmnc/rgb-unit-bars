import unittest
from types import SimpleNamespace
from unittest.mock import patch

from openrgb.utils import ModeColors, ZoneType

from rgbunitbars.devices.openrgb_sdk import OpenRGBKeyboard


def make_device(name, led_count, matrix_led_count, direct=True):
    modes = [SimpleNamespace(name="Direct", color_mode=ModeColors.PER_LED)] if direct else []
    leds = [SimpleNamespace(id=index) for index in range(led_count)]
    zones = []
    if matrix_led_count:
        zones.append(
            SimpleNamespace(
                type=ZoneType.MATRIX,
                matrix_map=[list(range(matrix_led_count))],
                leds=leds[:matrix_led_count],
            )
        )
    return SimpleNamespace(name=name, leds=leds, zones=zones, modes=modes, active_mode=None)


class OpenRGBSelectionTests(unittest.TestCase):
    @patch("rgbunitbars.devices.openrgb_sdk.OpenRGBClient")
    def test_prepare_prefers_larger_per_key_keyboard_over_similarly_sized_peripheral(self, openrgb_client):
        mouse = make_device("Razer Pro Click", 110, 110)
        keyboard = make_device("Razer Blackwidow", 114, 114)
        openrgb_client.return_value.get_devices_by_type.return_value = [mouse, keyboard]

        driver = OpenRGBKeyboard()
        driver.prepare()

        self.assertIs(driver.device, keyboard)
        self.assertEqual(driver.name, "Razer Blackwidow (OpenRGB)")
        self.assertEqual(len(driver.leds), 114)

    @patch("rgbunitbars.devices.openrgb_sdk.OpenRGBClient")
    def test_prepare_prefers_device_with_per_key_direct_mode(self, openrgb_client):
        unusable = make_device("Large device", 180, 180, direct=False)
        usable = make_device("Keyboard", 80, 80, direct=True)
        openrgb_client.return_value.get_devices_by_type.return_value = [unusable, usable]

        driver = OpenRGBKeyboard()
        driver.prepare()

        self.assertIs(driver.device, usable)

    def test_single_zone_keyboard_remains_a_candidate(self):
        keyboard = make_device("Single-zone keyboard", 80, 0)

        self.assertEqual(OpenRGBKeyboard._selection_score(keyboard), (True, 0, 80))

    @patch("rgbunitbars.devices.openrgb_sdk.OpenRGBClient")
    def test_name_match_still_limits_keyboard_selection(self, openrgb_client):
        mouse = make_device("Blackwidow clone", 120, 120)
        keyboard = make_device("Blackwidow keyboard", 80, 80)
        openrgb_client.return_value.get_devices_by_type.return_value = [mouse, keyboard]

        driver = OpenRGBKeyboard(match="keyboard")
        driver.prepare()

        self.assertIs(driver.device, keyboard)


if __name__ == "__main__":
    unittest.main()
