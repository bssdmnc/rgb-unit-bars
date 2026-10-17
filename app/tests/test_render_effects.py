import unittest

from rgbunitbars.render import LEVEL_UP_COLOR, LEVEL_UP_EFFECT_SECONDS, KeyboardGeometry, level_up_colors, render
from rgbunitbars.wow_link import Settings, UnitState


class RenderEffectTests(unittest.TestCase):
    def setUp(self):
        points = [(x, y) for y in range(5) for x in range(5)]
        self.geometry = KeyboardGeometry(points, row_tolerance=0)
        self.settings = Settings()

    def test_death_remains_unlit(self):
        colors = render(UnitState(1, 1, 0, 0, dead=True), self.settings, self.geometry, 0)

        self.assertEqual(colors, [(0, 0, 0)] * len(self.geometry.keys))

    def test_spirit_wave_uses_neutral_gray_white_palette(self):
        colors = render(UnitState(1, 1, 0, 0, ghost=True), self.settings, self.geometry, 0)

        self.assertTrue(all(max(color) - min(color) <= 13 for color in colors))
        self.assertGreater(len(set(colors)), 1)

    def test_level_up_filled_disk_expands_and_keeps_its_interior_lit(self):
        self.assertEqual(LEVEL_UP_EFFECT_SECONDS, 2.4)

        def brightness_at(progress, x, y):
            colors = level_up_colors(self.geometry, progress, 0)
            return colors[y * 5 + x][0]

        center = brightness_at(0.02, 2, 2)
        quarter = brightness_at(0.25, 2, 3)
        mid_center = brightness_at(0.30, 2, 2)
        passed_interior = brightness_at(0.30, 2, 3)
        mid_horizontal = brightness_at(0.25, 3, 2)
        mid_vertical = brightness_at(0.25, 2, 3)
        corners = [brightness_at(0.49, x, y) for x, y in ((0, 0), (4, 0), (0, 4), (4, 4))]

        self.assertGreater(center, 0)
        self.assertGreater(quarter, 0)
        self.assertGreater(passed_interior, 0)
        self.assertAlmostEqual(mid_horizontal, mid_vertical, delta=15)
        self.assertGreater(mid_center, 0)
        self.assertGreater(min(corners), 0)

    def test_return_phase_has_a_narrowing_vertical_band_and_fading_sparks(self):
        wide = level_up_colors(self.geometry, 0.55, 0)
        narrow = level_up_colors(self.geometry, 0.9, 0)
        end = level_up_colors(self.geometry, 0.99, 0)

        self.assertGreater(wide[2 * 5 + 2][0], wide[2 * 5 + 1][0])
        self.assertGreater(narrow[2 * 5 + 2][0], narrow[2 * 5 + 1][0])
        self.assertGreater(sum(wide[2 * 5 + 2]), sum(end[2 * 5 + 2]))

    def test_level_up_uses_one_hot_orange_hue_without_a_color_gradient(self):
        colors = level_up_colors(self.geometry, 0.02, 0.1)
        lit = [color for color in colors if color[0] > 20]

        self.assertGreater(len(lit), 0)
        for red, green, blue in lit:
            self.assertAlmostEqual(green / red, LEVEL_UP_COLOR[1], delta=0.02)
            self.assertEqual(blue, 0)
        self.assertGreater(max(color[0] for color in lit), 230)


if __name__ == "__main__":
    unittest.main()
