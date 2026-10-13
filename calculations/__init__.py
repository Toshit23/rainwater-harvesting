"""
calculations - Engineering Calculation Backend for Rainwater Harvesting Estimator.

Complete flow:
    Rooftop % (OpenCV) + Image Area (User)
            |
            v
    Rooftop Area (m2)
            |
            +-- Rainfall (Weather API) + Runoff Coeff
            |
            v
    Harvested Water (Litres / kL)
            |
            +-- Construction Inputs (Concrete, Plaster, Curing)
            |
            v
    Water Demand (Litres / kL)
            |
            v
    SURPLUS / SHORTFALL / BALANCED
"""

from typing import Union, Dict

from .rooftop_area import calculate_rooftop_area
from .rainwater_yield import (
    calculate_rainwater_yield,
    DEFAULT_RUNOFF_COEFFICIENT,
)
from .water_demand import (
    calculate_water_demand,
    DEFAULT_CONCRETE_WATER_L_PER_M3,
    DEFAULT_PLASTER_WATER_L_PER_M3,
    DEFAULT_CURING_WATER_L_PER_M3_PER_DAY,
)
from .comparison import compare_supply_demand


def calculate_project_result(
    image_area_m2: Union[int, float],
    rooftop_percentage: Union[int, float],
    rainfall_mm: Union[int, float],
    runoff_coefficient: Union[int, float] = DEFAULT_RUNOFF_COEFFICIENT,
    concrete_volume_m3: Union[int, float] = 0.0,
    plaster_volume_m3: Union[int, float] = 0.0,
    curing_days: Union[int, float] = 0.0,
    concrete_water_requirement_l_per_m3: Union[int, float] = DEFAULT_CONCRETE_WATER_L_PER_M3,
    plaster_water_requirement_l_per_m3: Union[int, float] = DEFAULT_PLASTER_WATER_L_PER_M3,
    curing_water_requirement_l_per_m3_per_day: Union[int, float] = DEFAULT_CURING_WATER_L_PER_M3_PER_DAY,
) -> Dict[str, Union[float, str, dict]]:
    """Master high-level function combining all calculation steps.

    Execution Sequence:
        1. Validate inputs (enforced by sub-modules)
        2. Calculate physical rooftop area
        3. Calculate rainwater harvesting potential
        4. Calculate construction water demand
        5. Compare supply vs demand
        6. Return unified, structured dictionary for Streamlit

    Returns
    -------
    dict
        {
            "image_area_m2": float,
            "rooftop_percentage": float,
            "rooftop_area_m2": float,
            "rainfall_mm": float,
            "runoff_coefficient": float,
            "harvested_water_litres": float,
            "harvested_water_kl": float,
            "construction_water_demand_litres": float,
            "construction_water_demand_kl": float,
            "difference_litres": float,
            "difference_kl": float,
            "status": "SURPLUS" | "SHORTFALL" | "BALANCED",
            "surplus_litres": float,
            "shortfall_litres": float,
            "demand_breakdown": dict
        }
    """
    # Step 1 & 2: Rooftop Area
    rooftop_area_m2 = calculate_rooftop_area(image_area_m2, rooftop_percentage)

    # Step 3: Rainwater Yield
    yield_data = calculate_rainwater_yield(rooftop_area_m2, rainfall_mm, runoff_coefficient)

    # Step 4: Construction Water Demand
    demand_data = calculate_water_demand(
        concrete_volume_m3=concrete_volume_m3,
        plaster_volume_m3=plaster_volume_m3,
        curing_days=curing_days,
        concrete_water_requirement_l_per_m3=concrete_water_requirement_l_per_m3,
        plaster_water_requirement_l_per_m3=plaster_water_requirement_l_per_m3,
        curing_water_requirement_l_per_m3_per_day=curing_water_requirement_l_per_m3_per_day,
    )

    # Step 5: Compare Supply and Demand
    comparison = compare_supply_demand(
        harvested_water_litres=yield_data["harvested_water_litres"],
        water_demand_litres=demand_data["total_water_demand_litres"],
    )

    # Step 6: Return structured result
    return {
        "image_area_m2": float(image_area_m2),
        "rooftop_percentage": float(rooftop_percentage),
        "rooftop_area_m2": rooftop_area_m2,

        "rainfall_mm": float(rainfall_mm),
        "runoff_coefficient": float(runoff_coefficient),

        "harvested_water_litres": yield_data["harvested_water_litres"],
        "harvested_water_kl": yield_data["harvested_water_kl"],

        "construction_water_demand_litres": demand_data["total_water_demand_litres"],
        "construction_water_demand_kl": demand_data["total_water_demand_kl"],

        "difference_litres": comparison["difference_litres"],
        "difference_kl": comparison["difference_litres"] / 1000.0,
        "status": comparison["status"],

        "surplus_litres": comparison["surplus_litres"],
        "shortfall_litres": comparison["shortfall_litres"],

        "demand_breakdown": demand_data,
    }


__all__ = [
    "calculate_rooftop_area",
    "calculate_rainwater_yield",
    "calculate_water_demand",
    "compare_supply_demand",
    "calculate_project_result",
    "DEFAULT_RUNOFF_COEFFICIENT",
    "DEFAULT_CONCRETE_WATER_L_PER_M3",
    "DEFAULT_PLASTER_WATER_L_PER_M3",
    "DEFAULT_CURING_WATER_L_PER_M3_PER_DAY",
]
