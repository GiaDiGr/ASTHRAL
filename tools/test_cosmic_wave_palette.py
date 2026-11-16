"""Small deterministic regression tests for the multi-tab cosmic color wave."""
import unittest

from tools.cosmic_wave_palette import (
    SCENE_COUNT,
    WAVE_PERIOD_TABS,
    generate,
    palette_for_scene,
    wave_position,
)


class CosmicWavePaletteTests(unittest.TestCase):
    def test_period_spans_ten_tabs(self):
        self.assertEqual(WAVE_PERIOD_TABS, 10)
        self.assertEqual(wave_position(0), wave_position(10))
        self.assertEqual(wave_position(5), wave_position(15))
        self.assertAlmostEqual(wave_position(0), 0)
        self.assertAlmostEqual(wave_position(5), 1)
        self.assertAlmostEqual(wave_position(10), 0)

    def test_wave_moves_to_violet_then_returns_to_blue(self):
        first_rise = [wave_position(index) for index in range(6)]
        first_fall = [wave_position(index) for index in range(5, 11)]
        self.assertEqual(first_rise, sorted(first_rise))
        self.assertEqual(first_fall, sorted(first_fall, reverse=True))
        self.assertEqual(palette_for_scene(0), palette_for_scene(10))
        self.assertEqual(palette_for_scene(5), palette_for_scene(15))
        self.assertNotEqual(palette_for_scene(0), palette_for_scene(5))

    def test_all_unique_starfield_assets_have_current_wave_palette(self):
        self.assertEqual(len(generate(check=True)), 0)
        self.assertEqual(SCENE_COUNT, 24)


if __name__ == "__main__":
    unittest.main()
