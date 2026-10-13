"""
test_calculations.py - Unit tests for the calculation backend.

Tests all required formulas, edge cases, and validation rules.
Run with:
    python -m pytest test_calculations.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from backend.calculations import (
    calculate_rooftop_area,
    calculate_harvestable_water,
    liters_to_kiloliters,
    calculate_all_results,
    calculate_scenario,
    calculate_runoff_scenarios,
    calculate_monthly_harvestable_water,
)


class TestRainwaterCalculations(unittest.TestCase):

    # -----------------------------------------------------------------------
    # Required Tests from Specification
    # -----------------------------------------------------------------------

    def test_1_rooftop_area(self):
        """Test 1 - Rooftop Area: 10,000 m2 at 40% -> 4,000 m2."""
        result = calculate_rooftop_area(total_site_area_m2=10000, rooftop_percentage=40)
        self.assertEqual(result, 4000.0)

    def test_2_harvestable_water(self):
        """Test 2 - Harvestable Water: 4,000 m2, 2,000 mm rain, 0.8 coeff -> 6,400,000 L."""
        result = calculate_harvestable_water(
            rooftop_area_m2=4000,
            rainfall_mm=2000,
            runoff_coefficient=0.8,
        )
        self.assertEqual(result, 6400000.0)

    def test_3_kiloliter_conversion(self):
        """Test 3 - Kilolitre Conversion: 6,400,000 L -> 6,400 kL."""
        result = liters_to_kiloliters(6400000)
        self.assertEqual(result, 6400.0)

    def test_4_rooftop_percentage_zero(self):
        """Test 4 - Rooftop percentage = 0 -> Rooftop area = 0."""
        result = calculate_rooftop_area(total_site_area_m2=5000, rooftop_percentage=0)
        self.assertEqual(result, 0.0)

    def test_5_rooftop_percentage_over_100(self):
        """Test 5 - Rooftop percentage > 100 raises ValueError."""
        with self.assertRaises(ValueError):
            calculate_rooftop_area(total_site_area_m2=5000, rooftop_percentage=105)

    def test_6_negative_site_area(self):
        """Test 6 - Negative or zero site area raises ValueError."""
        with self.assertRaises(ValueError):
            calculate_rooftop_area(total_site_area_m2=-1000, rooftop_percentage=40)
        with self.assertRaises(ValueError):
            calculate_rooftop_area(total_site_area_m2=0, rooftop_percentage=40)

    def test_7_negative_rainfall(self):
        """Test 7 - Negative rainfall raises ValueError."""
        with self.assertRaises(ValueError):
            calculate_harvestable_water(rooftop_area_m2=4000, rainfall_mm=-100, runoff_coefficient=0.8)

    def test_8_runoff_coefficient_out_of_bounds(self):
        """Test 8 - Runoff coefficient > 1 or < 0 raises ValueError."""
        with self.assertRaises(ValueError):
            calculate_harvestable_water(rooftop_area_m2=4000, rainfall_mm=1000, runoff_coefficient=1.2)
        with self.assertRaises(ValueError):
            calculate_harvestable_water(rooftop_area_m2=4000, rainfall_mm=1000, runoff_coefficient=-0.1)

    # -----------------------------------------------------------------------
    # Additional High-Level and Scenario Tests
    # -----------------------------------------------------------------------

    def test_calculate_all_results(self):
        """Verify high-level calculate_all_results returns all required keys and correct values."""
        res = calculate_all_results(
            total_site_area_m2=10000,
            rooftop_percentage=40,
            rainfall_mm=2000,
            runoff_coefficient=0.8,
        )
        self.assertEqual(res["total_site_area_m2"], 10000.0)
        self.assertEqual(res["rooftop_percentage"], 40.0)
        self.assertEqual(res["rooftop_area_m2"], 4000.0)
        self.assertEqual(res["rainfall_mm"], 2000.0)
        self.assertEqual(res["runoff_coefficient"], 0.8)
        self.assertEqual(res["harvestable_water_liters"], 6400000.0)
        self.assertEqual(res["harvestable_water_kl"], 6400.0)

    def test_calculate_scenario(self):
        """Verify single scenario calculation."""
        res = calculate_scenario(rooftop_area_m2=1000, rainfall_mm=1000, runoff_coefficient=0.7)
        self.assertEqual(res["harvestable_water_liters"], 700000.0)
        self.assertEqual(res["harvestable_water_kl"], 700.0)

    def test_calculate_runoff_scenarios(self):
        """Verify multi-scenario comparison (conservative, expected, optimistic)."""
        scenarios = calculate_runoff_scenarios(rooftop_area_m2=1000, rainfall_mm=1000)
        self.assertIn("Conservative", scenarios)
        self.assertIn("Expected", scenarios)
        self.assertIn("Optimistic", scenarios)
        self.assertEqual(scenarios["Conservative"]["harvestable_water_kl"], 700.0)
        self.assertEqual(scenarios["Expected"]["harvestable_water_kl"], 800.0)
        self.assertEqual(scenarios["Optimistic"]["harvestable_water_kl"], 900.0)

    def test_monthly_harvestable_water(self):
        """Verify monthly calculation handler."""
        monthly_rains = [100.0, 200.0, 0.0]
        res = calculate_monthly_harvestable_water(
            rooftop_area_m2=1000,
            monthly_rainfall_mm=monthly_rains,
            runoff_coefficient=0.8,
        )
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0]["harvestable_water_liters"], 80000.0)
        self.assertEqual(res[1]["harvestable_water_liters"], 160000.0)
        self.assertEqual(res[2]["harvestable_water_liters"], 0.0)

    def test_non_numeric_validation(self):
        """Verify non-numeric inputs raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_rooftop_area("ten_thousand", 40)
        with self.assertRaises(ValueError):
            calculate_harvestable_water(4000, "two_thousand", 0.8)


if __name__ == "__main__":
    unittest.main()
