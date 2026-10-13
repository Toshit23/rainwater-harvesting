"""
location.py - OpenStreetMap Nominatim geocoding.

Purpose:
    Convert a human-readable site address (e.g. "Powai, Mumbai, Maharashtra")
    into latitude + longitude coordinates using the free OpenStreetMap
    Nominatim geocoding API.

These coordinates are **internal intermediate values** - the end user never
enters or sees them.  They are passed automatically to the Open-Meteo weather
module to fetch historical rainfall.

Nominatim docs: https://nominatim.org/release-docs/develop/api/Search/

Usage:
    >>> from api.location import geocode_location
    >>> geocode_location("K J Somaiya Institute of Technology, Mumbai")
    {
        "latitude": 19.0...,
        "longitude": 72.8...,
        "display_name": "..."
    }
"""

from .api_utils import (
    GeocodingError,
    make_api_request,
    DEFAULT_TIMEOUT,
)

# Nominatim search endpoint (free, no API key required).
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode_location(address: str) -> dict:
    """Convert a site address into geographic coordinates via Nominatim.

    Parameters
    ----------
    address : str
        A human-readable address or place name.
        Examples:
            - "K J Somaiya Institute of Technology, Mumbai"
            - "Powai, Mumbai, Maharashtra"
            - "Mumbai, Maharashtra, India"

    Returns
    -------
    dict
        {
            "latitude": float,      # e.g. 19.0760
            "longitude": float,     # e.g. 72.8777
            "display_name": str     # e.g. "Mumbai, Maharashtra, India"
        }

    Raises
    ------
    ValueError
        If *address* is empty or contains only whitespace.
    GeocodingError
        If the location cannot be found, or the API request fails for any
        reason (network, timeout, HTTP error, malformed response).
    """

    # ---- 1. Validate input ----
    if not address or not address.strip():
        raise ValueError(
            "Address cannot be empty. Please enter a valid site address."
        )

    address = address.strip()

    # ---- 2. Build request parameters ----
    params = {
        "q": address,
        "format": "jsonv2",
        "limit": 1,   # we only need the best match
    }

    # ---- 3. Call Nominatim ----
    data = make_api_request(
        url=NOMINATIM_URL,
        params=params,
        timeout=DEFAULT_TIMEOUT,
        service_name="OpenStreetMap Nominatim",
        error_class=GeocodingError,
    )

    # ---- 4. Validate results ----
    if not isinstance(data, list) or len(data) == 0:
        raise GeocodingError(
            f'Location could not be found for: "{address}". '
            "Please enter a more specific address."
        )

    result = data[0]

    # ---- 5. Extract coordinates ----
    try:
        latitude = float(result["lat"])
        longitude = float(result["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise GeocodingError(
            f"OpenStreetMap returned an unexpected response format: {exc}"
        )

    display_name = result.get("display_name", address)

    # ---- 6. Return structured data ----
    return {
        "latitude": latitude,
        "longitude": longitude,
        "display_name": display_name,
    }
