"""
rooftop_area.py - Physical Rooftop / Catchment Area Calculation.

Converts the coverage percentage detected by the OpenCV module and the
user-supplied total physical area into an actual rooftop area in m2.

Formula:
    rooftop_area_m2 = image_area_m2 * (rooftop_percentage / 100.0)
"""

from typing import Union
from .validation import validate_strictly_positive, validate_percentage


def calculate_rooftop_area(
    image_area_m2: Union[int, float],
    rooftop_percentage: Union[int, float],
) -> float:
    """Calculate the physical rooftop/catchment area in square meters.

    Parameters
    ----------
    image_area_m2 : float
        Total physical area represented by the entire image in m2 (> 0).
    rooftop_percentage : float
        Rooftop coverage percentage detected by OpenCV (0 to 100).

    Returns
    -------
    float
        Rooftop/catchment area in square meters (m2).

    Raises
    ------
    ValueError
        If image_area_m2 <= 0 or rooftop_percentage is outside [0, 100].
    """
    valid_image_area = validate_strictly_positive(image_area_m2, "image_area_m2")
    valid_percentage = validate_percentage(rooftop_percentage, "rooftop_percentage")

    # Full precision calculation (no intermediate rounding)
    return valid_image_area * (valid_percentage / 100.0)
