"""
backend - Backwards-compatibility wrapper for calculations package.
"""

from calculations import (
    calculate_rooftop_area,
    calculate_rainwater_yield,
    calculate_water_demand,
    compare_supply_demand,
    calculate_project_result,
    DEFAULT_RUNOFF_COEFFICIENT,
)

__all__ = [
    "calculate_rooftop_area",
    "calculate_rainwater_yield",
    "calculate_water_demand",
    "compare_supply_demand",
    "calculate_project_result",
    "DEFAULT_RUNOFF_COEFFICIENT",
]
