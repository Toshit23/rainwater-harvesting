"""
test_area_detection.py - Unit tests for area_detection (OpenCV rooftop detection).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from area_detection import detect_building_area_percentage


class TestAreaDetection(unittest.TestCase):

    def test_sample_image_detection(self):
        """Verify building detection runs on sample_site.png and returns valid percentage."""
        sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_site.png")
        if not os.path.isfile(sample_path):
            self.skipTest("sample_site.png not found")

        result = detect_building_area_percentage(sample_path)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertGreater(result["rooftop_percentage"], 0.0)
        self.assertLessEqual(result["rooftop_percentage"], 100.0)
        self.assertGreater(result["building_count"], 0)

    def test_nonexistent_image_raises_error(self):
        """Verify invalid image path raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            detect_building_area_percentage("non_existent_image_12345.png")


if __name__ == "__main__":
    unittest.main()
