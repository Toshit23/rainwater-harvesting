"""
water_demand.py - Construction Site Water Demand Estimation.

Estimates the water required for civil construction activities:
    1. Concrete production and batching
    2. Plastering operations
    3. Curing activities over specified curing duration

All engineering coefficients are explicit, configurable, and transparently documented.
No hidden magic numbers are used.
"""

from typing import Union, Dict
from .validation import validate_non_negative

# Documented Engineering Assumptions (Configurable):
# - Concrete mixing: ~180 L per m3 of concrete (IS 456 typical concrete mix)
# - Plaster mixing: ~160 L per m3 of plaster mortar
# - Curing allowance: ~20 L per m3 of element per curing day
DEFAULT_CONCRETE_WATER_L_PER_M3 = 180.0
DEFAULT_PLASTER_WATER_L_PER_M3 = 160.0
DEFAULT_CURING_WATER_L_PER_M3_PER_DAY = 20.0
DEFAULT_CURING_DAYS = 13.0


def calculate_water_demand(
    concrete_volume_m3: Union[int, float] = 0.0,
    plaster_volume_m3: Union[int, float] = 0.0,
    curing_days: Union[int, float] = DEFAULT_CURING_DAYS,
    concrete_water_requirement_l_per_m3: Union[int, float] = DEFAULT_CONCRETE_WATER_L_PER_M3,
    plaster_water_requirement_l_per_m3: Union[int, float] = DEFAULT_PLASTER_WATER_L_PER_M3,
    curing_water_requirement_l_per_m3_per_day: Union[int, float] = DEFAULT_CURING_WATER_L_PER_M3_PER_DAY,
) -> Dict[str, float]:
    """Calculate the estimated water demand for construction operations.

    Formulas:
        concrete_mixing_water = concrete_volume_m3 * concrete_water_requirement_l_per_m3
        plaster_mixing_water  = plaster_volume_m3 * plaster_water_requirement_l_per_m3
        curing_water          = (concrete_volume_m3 + plaster_volume_m3) * curing_water_requirement_l_per_m3_per_day * curing_days
        total_water_demand    = concrete_mixing_water + plaster_mixing_water + curing_water

    Parameters
    ----------
    concrete_volume_m3 : float
        Total volume of concrete to be placed (m3, >= 0).
    plaster_volume_m3 : float
        Total volume of plaster work (m3, >= 0).
    curing_days : float
        Number of days elements are subjected to water curing (>= 0).
    concrete_water_requirement_l_per_m3 : float, optional
        Water required per m3 of concrete (L/m3).
    plaster_water_requirement_l_per_m3 : float, optional
        Water required per m3 of plaster (L/m3).
    curing_water_requirement_l_per_m3_per_day : float, optional
        Water required per m3 of material per day of curing (L/m3/day).

    Returns
    -------
    dict
        {
            "concrete_volume_m3": float,
            "plaster_volume_m3": float,
            "curing_days": float,
            "concrete_water_litres": float,
            "plaster_water_litres": float,
            "curing_water_litres": float,
            "total_water_demand_litres": float,
            "total_water_demand_kl": float
        }

    Raises
    ------
    ValueError
        If any quantity or coefficient is negative or invalid.
    """
    c_vol = validate_non_negative(concrete_volume_m3, "concrete_volume_m3")
    p_vol = validate_non_negative(plaster_volume_m3, "plaster_volume_m3")
    days = validate_non_negative(curing_days, "curing_days")

    c_coeff = validate_non_negative(concrete_water_requirement_l_per_m3, "concrete_water_requirement_l_per_m3")
    p_coeff = validate_non_negative(plaster_water_requirement_l_per_m3, "plaster_water_requirement_l_per_m3")
    curing_coeff = validate_non_negative(curing_water_requirement_l_per_m3_per_day, "curing_water_requirement_l_per_m3_per_day")

    concrete_water = c_vol * c_coeff
    plaster_water = p_vol * p_coeff
    curing_water = (c_vol + p_vol) * curing_coeff * days

    total_litres = concrete_water + plaster_water + curing_water
    total_kl = total_litres / 1000.0

    return {
        "concrete_volume_m3": c_vol,
        "plaster_volume_m3": p_vol,
        "curing_days": days,
        "concrete_water_litres": concrete_water,
        "plaster_water_litres": plaster_water,
        "curing_water_litres": curing_water,
        "total_water_demand_litres": total_litres,
        "total_water_demand_kl": total_kl,
    }
