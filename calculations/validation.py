"""
validation.py - Input validation utilities for engineering calculations.

Ensures:
    - Values are real numbers (rejects None, NaN, inf, bool, strings).
    - Ranges are valid (positive area, percentages in [0, 100], etc.).
    - Clear, descriptive ValueError messages are produced.
"""

import math
from typing import Union


def validate_number(value: Union[int, float], field_name: str) -> float:
    """Validate that a value is a finite number (int or float).

    Rejects bool, None, NaN, inf, and strings.
    """
    if value is None:
        raise ValueError(f"'{field_name}' cannot be None.")
    if isinstance(value, bool):
        raise ValueError(f"'{field_name}' must be numeric, got boolean {value}.")
    if not isinstance(value, (int, float)):
        raise ValueError(f"'{field_name}' must be a numeric value, got {type(value).__name__}.")
    if math.isnan(value):
        raise ValueError(f"'{field_name}' cannot be NaN.")
    if math.isinf(value):
        raise ValueError(f"'{field_name}' cannot be infinite.")
    return float(value)


def validate_strictly_positive(value: Union[int, float], field_name: str) -> float:
    """Validate that a value is strictly greater than zero (> 0)."""
    num = validate_number(value, field_name)
    if num <= 0:
        raise ValueError(f"'{field_name}' must be strictly greater than 0, got {num}.")
    return num


def validate_non_negative(value: Union[int, float], field_name: str) -> float:
    """Validate that a value is greater than or equal to zero (>= 0)."""
    num = validate_number(value, field_name)
    if num < 0:
        raise ValueError(f"'{field_name}' cannot be negative, got {num}.")
    return num


def validate_percentage(value: Union[int, float], field_name: str) -> float:
    """Validate that a percentage is between 0 and 100 inclusive [0, 100]."""
    num = validate_number(value, field_name)
    if not (0.0 <= num <= 100.0):
        raise ValueError(f"'{field_name}' must be between 0 and 100, got {num}.")
    return num


def validate_runoff_coefficient(value: Union[int, float], field_name: str = "runoff_coefficient") -> float:
    """Validate runoff coefficient is strictly positive and <= 1.0 (0 < c <= 1)."""
    num = validate_number(value, field_name)
    if not (0.0 < num <= 1.0):
        raise ValueError(f"'{field_name}' must satisfy 0 < runoff_coefficient <= 1, got {num}.")
    return num
