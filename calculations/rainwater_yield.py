"""
rainwater_yield.py - Rainwater Harvesting Yield Calculation.

Uses the physical relationship:
    1 mm of rainfall over 1 m2 catchment area = 1 Litre of water

Formula:
    harvested_water_litres = rooftop_area_m2 * rainfall_mm * runoff_coefficient
    harvested_water_kl = harvested_water_litres / 1000.0
"""

from typing import Union, Dict
from .validation import (
    validate_non_negative,
    validate_runoff_coefficient,
)

# Configurable standard engineering default for impermeable rooftops (e.g. concrete/metal/tile)
DEFAULT_RUNOFF_COEFFICIENT = 0.80


def calculate_rainwater_yield(
    rooftop_area_m2: Union[int, float],
    rainfall_mm: Union[int, float],
    runoff_coefficient: Union[int, float] = DEFAULT_RUNOFF_COEFFICIENT,
) -> Dict[str, float]:
    """Calculate the estimated rainwater harvesting yield in Litres and Kilolitres.

    Parameters
    ----------
    rooftop_area_m2 : float
        Rooftop or catchment surface area in m2 (>= 0).
    rainfall_mm : float
        Precipitation depth in millimeters (>= 0, 0 is valid).
    runoff_coefficient : float, optional
        Fraction of rainfall that actually runs off the catchment (0 < c <= 1).
        Default is 0.80.

    Returns
    -------
    dict
        {
            "rooftop_area_m2": float,
            "rainfall_mm": float,
            "runoff_coefficient": float,
            "harvested_water_litres": float,
            "harvested_water_kl": float
        }

    Raises
    ------
    ValueError
        If inputs are negative, invalid, or runoff_coefficient is out of (0, 1].
    """
    valid_rooftop_area = validate_non_negative(rooftop_area_m2, "rooftop_area_m2")
    valid_rainfall = validate_non_negative(rainfall_mm, "rainfall_mm")
    valid_coeff = validate_runoff_coefficient(runoff_coefficient, "runoff_coefficient")

    # 1 mm * 1 m2 = 1 L
    harvested_water_litres = valid_rooftop_area * valid_rainfall * valid_coeff
    harvested_water_kl = harvested_water_litres / 1000.0

    return {
        "rooftop_area_m2": valid_rooftop_area,
        "rainfall_mm": valid_rainfall,
        "runoff_coefficient": valid_coeff,
        "harvested_water_litres": harvested_water_litres,
        "harvested_water_kl": harvested_water_kl,
    }
