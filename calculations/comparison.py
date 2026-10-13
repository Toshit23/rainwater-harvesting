"""
comparison.py - Supply vs Demand Comparison.

Compares total rainwater yield (supply) against construction site water demand.
Evaluates whether the site achieves a water SURPLUS, SHORTFALL, or is BALANCED.
"""

from typing import Union, Dict
from .validation import validate_non_negative


def compare_supply_demand(
    harvested_water_litres: Union[int, float],
    water_demand_litres: Union[int, float],
) -> Dict[str, Union[float, str]]:
    """Compare rainwater harvested with construction water requirement.

    Parameters
    ----------
    harvested_water_litres : float
        Total volume of rainwater harvested in litres (>= 0).
    water_demand_litres : float
        Total volume of water demanded by construction in litres (>= 0).

    Returns
    -------
    dict
        {
            "harvested_water_litres": float,
            "water_demand_litres": float,
            "difference_litres": float,
            "status": "SURPLUS" | "SHORTFALL" | "BALANCED",
            "surplus_litres": float,
            "shortfall_litres": float
        }

    Raises
    ------
    ValueError
        If inputs are negative or non-numeric.
    """
    supply = validate_non_negative(harvested_water_litres, "harvested_water_litres")
    demand = validate_non_negative(water_demand_litres, "water_demand_litres")

    difference = supply - demand

    if difference > 0:
        status = "SURPLUS"
        surplus = difference
        shortfall = 0.0
    elif difference < 0:
        status = "SHORTFALL"
        surplus = 0.0
        shortfall = abs(difference)
    else:
        status = "BALANCED"
        surplus = 0.0
        shortfall = 0.0

    return {
        "harvested_water_litres": supply,
        "water_demand_litres": demand,
        "difference_litres": difference,
        "status": status,
        "surplus_litres": surplus,
        "shortfall_litres": shortfall,
    }
