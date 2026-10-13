"""
calculations.py - Rainwater Harvesting Calculation Engine.

Purpose:
    Performs deterministic calculations for rooftop area and harvestable rainwater.
    This module has NO dependencies on APIs (OpenStreetMap, Nominatim, Open-Meteo),
    NO OpenCV dependencies, and NO Streamlit UI code.

Formulas:
    Rooftop Area (m2) = Total Site Area (m2) * (Rooftop Percentage / 100)
    Harvestable Water (L) = Rooftop Area (m2) * Rainfall (mm) * Runoff Coefficient
    (Note: 1 mm rainfall on 1 m2 area = 1 Liter of water)
    Harvestable Water (kL) = Harvestable Water (L) / 1000
"""

from typing import Union, List, Dict


DEFAULT_RUNOFF_COEFFICIENT = 0.8


def _validate_numeric(value: Union[int, float], name: str) -> float:
    """Ensure value is a real number (int/float) and return as float."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a numeric value, got {type(value).__name__}.")
    return float(value)


def calculate_rooftop_area(
    total_site_area_m2: Union[int, float],
    rooftop_percentage: Union[int, float],
) -> float:
    """Calculate the estimated rooftop area from total site area and coverage percentage.

    Parameters
    ----------
    total_site_area_m2 : float
        Total construction site area in square meters (must be > 0).
    rooftop_percentage : float
        Percentage of site covered by rooftop (0 to 100).

    Returns
    -------
    float
        Estimated rooftop area in square meters.
    """
    area = _validate_numeric(total_site_area_m2, "Total site area")
    percentage = _validate_numeric(rooftop_percentage, "Rooftop percentage")

    if area <= 0:
        raise ValueError(f"Total site area must be strictly greater than 0, got {area}.")
    if not (0.0 <= percentage <= 100.0):
        raise ValueError(f"Rooftop percentage must be between 0 and 100, got {percentage}.")

    return round(area * (percentage / 100.0), 2)


def calculate_harvestable_water(
    rooftop_area_m2: Union[int, float],
    rainfall_mm: Union[int, float],
    runoff_coefficient: Union[int, float] = DEFAULT_RUNOFF_COEFFICIENT,
) -> float:
    """Calculate estimated harvestable rainwater in Litres.

    Uses the standard relationship: 1 mm rainfall * 1 m2 area = 1 Litre.

    Parameters
    ----------
    rooftop_area_m2 : float
        Rooftop area in square meters (must be >= 0).
    rainfall_mm : float
        Rainfall depth in millimeters (must be >= 0).
    runoff_coefficient : float, optional
        Runoff efficiency coefficient (0.0 to 1.0, default 0.8).

    Returns
    -------
    float
        Harvestable rainwater volume in Litres (L).
    """
    area = _validate_numeric(rooftop_area_m2, "Rooftop area")
    rain = _validate_numeric(rainfall_mm, "Rainfall")
    coeff = _validate_numeric(runoff_coefficient, "Runoff coefficient")

    if area < 0:
        raise ValueError(f"Rooftop area cannot be negative, got {area}.")
    if rain < 0:
        raise ValueError(f"Rainfall cannot be negative, got {rain}.")
    if not (0.0 <= coeff <= 1.0):
        raise ValueError(f"Runoff coefficient must be between 0 and 1, got {coeff}.")

    return round(area * rain * coeff, 2)


def liters_to_kiloliters(liters: Union[int, float]) -> float:
    """Convert volume from Litres (L) to Kilolitres (kL).

    Parameters
    ----------
    liters : float
        Volume in Litres (must be >= 0).

    Returns
    -------
    float
        Volume in Kilolitres (1 kL = 1,000 L).
    """
    l_val = _validate_numeric(liters, "Liters")
    if l_val < 0:
        raise ValueError(f"Volume in liters cannot be negative, got {l_val}.")
    return round(l_val / 1000.0, 3)


def calculate_all_results(
    total_site_area_m2: Union[int, float],
    rooftop_percentage: Union[int, float],
    rainfall_mm: Union[int, float],
    runoff_coefficient: Union[int, float] = DEFAULT_RUNOFF_COEFFICIENT,
) -> Dict[str, Union[float, int]]:
    """High-level calculation function returning a structured summary.

    Parameters
    ----------
    total_site_area_m2 : float
        Total site area in m2 (user input).
    rooftop_percentage : float
        Rooftop coverage percentage (OpenCV output).
    rainfall_mm : float
        Rainfall depth in mm (API output).
    runoff_coefficient : float, optional
        Runoff efficiency (0.0 to 1.0, default 0.8).

    Returns
    -------
    dict
        {
            "total_site_area_m2": float,
            "rooftop_percentage": float,
            "rooftop_area_m2": float,
            "rainfall_mm": float,
            "runoff_coefficient": float,
            "harvestable_water_liters": float,
            "harvestable_water_kl": float
        }
    """
    rooftop_area = calculate_rooftop_area(total_site_area_m2, rooftop_percentage)
    harvestable_l = calculate_harvestable_water(rooftop_area, rainfall_mm, runoff_coefficient)
    harvestable_kl = liters_to_kiloliters(harvestable_l)

    return {
        "total_site_area_m2": float(total_site_area_m2),
        "rooftop_percentage": float(rooftop_percentage),
        "rooftop_area_m2": rooftop_area,
        "rainfall_mm": float(rainfall_mm),
        "runoff_coefficient": float(runoff_coefficient),
        "harvestable_water_liters": harvestable_l,
        "harvestable_water_kl": harvestable_kl,
    }


def calculate_scenario(
    rooftop_area_m2: Union[int, float],
    rainfall_mm: Union[int, float],
    runoff_coefficient: Union[int, float],
) -> Dict[str, float]:
    """Calculate harvestable rainwater for a specific scenario/runoff coefficient.

    Parameters
    ----------
    rooftop_area_m2 : float
        Rooftop area in m2.
    rainfall_mm : float
        Rainfall depth in mm.
    runoff_coefficient : float
        Hypothetical runoff coefficient (0 to 1).

    Returns
    -------
    dict
        {"runoff_coefficient": float, "harvestable_water_liters": float, "harvestable_water_kl": float}
    """
    liters = calculate_harvestable_water(rooftop_area_m2, rainfall_mm, runoff_coefficient)
    return {
        "runoff_coefficient": float(runoff_coefficient),
        "harvestable_water_liters": liters,
        "harvestable_water_kl": liters_to_kiloliters(liters),
    }


def calculate_runoff_scenarios(
    rooftop_area_m2: Union[int, float],
    rainfall_mm: Union[int, float],
    scenarios: Dict[str, float] = None,
) -> Dict[str, Dict[str, float]]:
    """Compare multiple runoff coefficient scenarios (e.g. Conservative, Expected, Optimistic).

    Parameters
    ----------
    rooftop_area_m2 : float
        Rooftop area in m2.
    rainfall_mm : float
        Rainfall depth in mm.
    scenarios : dict, optional
        Mapping of scenario name to coefficient.
        Default: {"Conservative": 0.7, "Expected": 0.8, "Optimistic": 0.9}

    Returns
    -------
    dict
        Mapping of scenario names to calculated results.
    """
    if scenarios is None:
        scenarios = {
            "Conservative": 0.70,
            "Expected": 0.80,
            "Optimistic": 0.90,
        }

    results = {}
    for name, coeff in scenarios.items():
        results[name] = calculate_scenario(rooftop_area_m2, rainfall_mm, coeff)
    return results


def calculate_monthly_harvestable_water(
    rooftop_area_m2: Union[int, float],
    monthly_rainfall_mm: List[Union[int, float]],
    runoff_coefficient: Union[int, float] = DEFAULT_RUNOFF_COEFFICIENT,
) -> List[Dict[str, float]]:
    """Calculate harvestable water for each month when a monthly rainfall list is provided.

    Parameters
    ----------
    rooftop_area_m2 : float
        Rooftop area in m2.
    monthly_rainfall_mm : list of float
        Monthly rainfall figures in mm.
    runoff_coefficient : float, optional
        Runoff coefficient.

    Returns
    -------
    list of dict
        Each element contains {"month_index": int, "rainfall_mm": float, "harvestable_water_liters": float, "harvestable_water_kl": float}
    """
    results = []
    for idx, rain in enumerate(monthly_rainfall_mm, start=1):
        l_val = calculate_harvestable_water(rooftop_area_m2, rain, runoff_coefficient)
        results.append({
            "month_index": idx,
            "rainfall_mm": float(rain),
            "harvestable_water_liters": l_val,
            "harvestable_water_kl": liters_to_kiloliters(l_val),
        })
    return results
