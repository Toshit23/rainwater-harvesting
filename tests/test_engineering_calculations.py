"""
test_engineering_calculations.py - Full test suite for the calculations module.

Tests all requirements:
    TEST 1: image_area_m2 = 10,000, rooftop_percentage = 40 -> rooftop_area_m2 = 4,000
    TEST 2: rooftop_area_m2 = 4,000, rainfall_mm = 100, runoff_coeff = 0.8 -> 320,000 litres
    TEST 3: rainfall_mm = 0 -> harvested_water_litres = 0
    TEST 4: harvested water > demand -> status = 'SURPLUS'
    TEST 5: harvested water < demand -> status = 'SHORTFALL'
    TEST 6: harvested water = demand -> status = 'BALANCED'
    TEST 7: Invalid inputs -> clear validation errors (ValueError)
"""

import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from calculations import (
    calculate_rooftop_area,
    calculate_rainwater_yield,
    calculate_water_demand,
    compare_supply_demand,
    calculate_project_result,
)


class TestEngineeringCalculations(unittest.TestCase):

    # -----------------------------------------------------------------------
    # TEST 1: Rooftop Area Calculation
    # -----------------------------------------------------------------------
    def test_1_rooftop_area(self):
        """TEST 1: image_area_m2 = 10,000, rooftop_percentage = 40 -> 4,000 m2."""
        area = calculate_rooftop_area(image_area_m2=10000, rooftop_percentage=40)
        self.assertEqual(area, 4000.0)

    # -----------------------------------------------------------------------
    # TEST 2: Rainwater Yield Calculation
    # -----------------------------------------------------------------------
    def test_2_rainwater_yield(self):
        """TEST 2: rooftop_area = 4,000 m2, rainfall = 100 mm, runoff = 0.8 -> 320,000 litres."""
        result = calculate_rainwater_yield(
            rooftop_area_m2=4000,
            rainfall_mm=100,
            runoff_coefficient=0.8,
        )
        self.assertEqual(result["harvested_water_litres"], 320000.0)
        self.assertEqual(result["harvested_water_kl"], 320.0)

    # -----------------------------------------------------------------------
    # TEST 3: Zero Rainfall
    # -----------------------------------------------------------------------
    def test_3_zero_rainfall(self):
        """TEST 3: rainfall_mm = 0 -> harvested_water_litres = 0."""
        result = calculate_rainwater_yield(
            rooftop_area_m2=4000,
            rainfall_mm=0,
            runoff_coefficient=0.8,
        )
        self.assertEqual(result["harvested_water_litres"], 0.0)
        self.assertEqual(result["harvested_water_kl"], 0.0)

    # -----------------------------------------------------------------------
    # TEST 4: Supply > Demand (SURPLUS)
    # -----------------------------------------------------------------------
    def test_4_surplus(self):
        """TEST 4: harvested water > demand -> status = 'SURPLUS'."""
        result = compare_supply_demand(
            harvested_water_litres=500000,
            water_demand_litres=300000,
        )
        self.assertEqual(result["status"], "SURPLUS")
        self.assertEqual(result["difference_litres"], 200000.0)
        self.assertEqual(result["surplus_litres"], 200000.0)
        self.assertEqual(result["shortfall_litres"], 0.0)

    # -----------------------------------------------------------------------
    # TEST 5: Supply < Demand (SHORTFALL)
    # -----------------------------------------------------------------------
    def test_5_shortfall(self):
        """TEST 5: harvested water < demand -> status = 'SHORTFALL'."""
        result = compare_supply_demand(
            harvested_water_litres=200000,
            water_demand_litres=350000,
        )
        self.assertEqual(result["status"], "SHORTFALL")
        self.assertEqual(result["difference_litres"], -150000.0)
        self.assertEqual(result["surplus_litres"], 0.0)
        self.assertEqual(result["shortfall_litres"], 150000.0)

    # -----------------------------------------------------------------------
    # TEST 6: Supply == Demand (BALANCED)
    # -----------------------------------------------------------------------
    def test_6_balanced(self):
        """TEST 6: harvested water = demand -> status = 'BALANCED'."""
        result = compare_supply_demand(
            harvested_water_litres=400000,
            water_demand_litres=400000,
        )
        self.assertEqual(result["status"], "BALANCED")
        self.assertEqual(result["difference_litres"], 0.0)
        self.assertEqual(result["surplus_litres"], 0.0)
        self.assertEqual(result["shortfall_litres"], 0.0)

    # -----------------------------------------------------------------------
    # TEST 7: Invalid Inputs Validation
    # -----------------------------------------------------------------------
    def test_7_invalid_inputs(self):
        """TEST 7: Verify clear validation errors for all bad inputs."""
        # 1. Negative image area
        with self.assertRaises(ValueError) as ctx:
            calculate_rooftop_area(-1000, 40)
        self.assertIn("image_area_m2", str(ctx.exception))

        # 2. Zero image area (must be strictly > 0)
        with self.assertRaises(ValueError):
            calculate_rooftop_area(0, 40)

        # 3. Rooftop percentage < 0 or > 100
        with self.assertRaises(ValueError):
            calculate_rooftop_area(1000, -5)
        with self.assertRaises(ValueError):
            calculate_rooftop_area(1000, 105)

        # 4. Negative rainfall
        with self.assertRaises(ValueError):
            calculate_rainwater_yield(1000, -10, 0.8)

        # 5. Runoff coefficient <= 0 or > 1
        with self.assertRaises(ValueError):
            calculate_rainwater_yield(1000, 100, 0.0)
        with self.assertRaises(ValueError):
            calculate_rainwater_yield(1000, 100, 1.2)

        # 6. Negative construction quantities
        with self.assertRaises(ValueError):
            calculate_water_demand(concrete_volume_m3=-10)
        with self.assertRaises(ValueError):
            calculate_water_demand(plaster_volume_m3=-5)
        with self.assertRaises(ValueError):
            calculate_water_demand(curing_days=-7)

        # 7. None / NaN values
        with self.assertRaises(ValueError):
            calculate_rooftop_area(None, 40)
        with self.assertRaises(ValueError):
            calculate_rainwater_yield(1000, float("nan"), 0.8)

    # -----------------------------------------------------------------------
    # TEST 8: Full High-Level calculate_project_result
    # -----------------------------------------------------------------------
    def test_8_full_project_result(self):
        """Verify the complete pipeline returns correct keys, unrounded calculations, and proper status."""
        result = calculate_project_result(
            image_area_m2=10000,
            rooftop_percentage=42.0,
            rainfall_mm=842.5,
            runoff_coefficient=0.8,
            concrete_volume_m3=100.0,
            plaster_volume_m3=50.0,
            curing_days=14,
        )

        # Rooftop area: 10000 * 0.42 = 4200.0 m2
        self.assertEqual(result["rooftop_area_m2"], 4200.0)

        # Harvested water: 4200 * 842.5 * 0.8 = 2,830,800.0 L
        self.assertEqual(result["harvested_water_litres"], 2830800.0)
        self.assertEqual(result["harvested_water_kl"], 2830.8)

        # Demand:
        # Concrete = 100 * 180 = 18,000 L
        # Plaster = 50 * 160 = 8,000 L
        # Curing = 150 * 20 * 14 = 42,000 L
        # Total demand = 68,000 L
        self.assertEqual(result["construction_water_demand_litres"], 68000.0)
        self.assertEqual(result["construction_water_demand_kl"], 68.0)

        # Difference: 2,830,800 - 68,000 = 2,762,800 L
        self.assertEqual(result["status"], "SURPLUS")
        self.assertEqual(result["surplus_litres"], 2762800.0)
        self.assertEqual(result["shortfall_litres"], 0.0)


if __name__ == "__main__":
    unittest.main()
