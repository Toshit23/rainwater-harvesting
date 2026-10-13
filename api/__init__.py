"""
api - Location + Weather API integration for Rainwater Harvesting Estimator.

This package converts a site address into historical rainfall data using:
    1. OpenStreetMap Nominatim  -> geocoding (address -> coordinates)
    2. Open-Meteo Archive API   -> historical daily precipitation

The user only provides a site address. Latitude and longitude are obtained
automatically and are never required as user input.

Public API
----------
get_rainfall_for_location(address, start_date, end_date)
    The **primary function** for the rest of the project.
    One call: address in -> rainfall data out.

geocode_location(address)
    Lower-level: address -> {"latitude", "longitude", "display_name"}.

get_historical_rainfall(latitude, longitude, start_date, end_date)
    Lower-level: coordinates + dates -> rainfall data.

Exceptions
----------
APIError            Base class for all API errors.
GeocodingError      Location lookup failed.
WeatherAPIError     Rainfall retrieval failed.

Example
-------
>>> from api import get_rainfall_for_location
>>> result = get_rainfall_for_location(
...     "K J Somaiya Institute of Technology, Mumbai",
...     "2025-01-01",
...     "2025-12-31",
... )
>>> print(result["total_rainfall_mm"])
"""

from .location import geocode_location
from .weather import get_historical_rainfall
from .api_utils import APIError, GeocodingError, WeatherAPIError


def get_rainfall_for_location(
    address: str,
    start_date: str,
    end_date: str,
) -> dict:
    """Complete address -> rainfall pipeline in a single call.

    This is the **primary public function** that the rest of the project
    should use.  It chains geocoding and weather retrieval internally so
    that no other module needs to know about Nominatim or Open-Meteo.

    Parameters
    ----------
    address : str
        A human-readable site address.
        Example: "Powai, Mumbai, Maharashtra"
    start_date : str
        Start of the historical period (`YYYY-MM-DD`).
    end_date : str
        End of the historical period (`YYYY-MM-DD`).

    Returns
    -------
    dict
        {
            "address": str,            # original user input
            "location_name": str,      # display name from Nominatim
            "latitude": float,         # internal - for logging/debug
            "longitude": float,        # internal - for logging/debug
            "start_date": str,
            "end_date": str,
            "total_rainfall_mm": float,
            "daily_rainfall": list[float],
        }

    Raises
    ------
    ValueError
        If *address* is empty or dates are invalid.
    GeocodingError
        If the location cannot be found.
    WeatherAPIError
        If rainfall data cannot be retrieved.
    """

    # Step 1: Address -> coordinates (internal)
    location = geocode_location(address)

    # Step 2: Coordinates -> rainfall
    rainfall = get_historical_rainfall(
        latitude=location["latitude"],
        longitude=location["longitude"],
        start_date=start_date,
        end_date=end_date,
    )

    # Step 3: Merge into a single clean result
    return {
        "address": address,
        "location_name": location["display_name"],
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "start_date": rainfall["start_date"],
        "end_date": rainfall["end_date"],
        "total_rainfall_mm": rainfall["total_rainfall_mm"],
        "daily_rainfall": rainfall["daily_rainfall"],
    }


__all__ = [
    "get_rainfall_for_location",
    "geocode_location",
    "get_historical_rainfall",
    "APIError",
    "GeocodingError",
    "WeatherAPIError",
]
