"""
api_utils.py - Shared utilities for the Rainwater Harvesting API module.

Provides:
    - Custom exception hierarchy for clean error handling.
    - A reusable HTTP GET helper with timeout, status-code, and JSON-parse
      validation so that individual API modules don't repeat boilerplate.

All exceptions inherit from APIError, so callers (Streamlit, CLI, tests) can
catch APIError to handle any API-layer failure in one place.
"""

import requests


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class APIError(Exception):
    """Base exception for all API-related errors in this module."""
    pass


class GeocodingError(APIError):
    """Raised when the OpenStreetMap Nominatim geocoding request fails.

    Possible causes:
        - Address not found (no search results).
        - Network timeout or connection error.
        - Unexpected / malformed API response.
        - Rate-limiting by Nominatim.
    """
    pass


class WeatherAPIError(APIError):
    """Raised when the Open-Meteo historical weather request fails.

    Possible causes:
        - Invalid coordinates or date range.
        - Network timeout or connection error.
        - Unexpected / malformed API response.
        - No precipitation data available for the requested period.
    """
    pass


# ---------------------------------------------------------------------------
# Shared HTTP helper
# ---------------------------------------------------------------------------

# Default User-Agent compliant with Nominatim usage policy:
# https://operations.osmfoundation.org/policies/nominatim/
DEFAULT_USER_AGENT = "RainwaterHarvestingEstimator/1.0 (student-project)"

# Reasonable default timeouts (seconds).
DEFAULT_TIMEOUT = 10   # for geocoding
WEATHER_TIMEOUT = 15   # weather payloads can be larger


def make_api_request(
    url: str,
    params: dict,
    timeout: int,
    service_name: str,
    error_class: type = APIError,
) -> dict:
    """Send an HTTP GET request and return the parsed JSON response.

    This helper centralises:
        1. Connection / timeout error handling.
        2. HTTP status-code validation.
        3. JSON parsing with a fallback error message.

    Parameters
    ----------
    url : str
        The API endpoint URL.
    params : dict
        Query-string parameters.
    timeout : int
        Request timeout in seconds.
    service_name : str
        Human-readable name of the service (used in error messages).
    error_class : type, optional
        The exception class to raise on failure (default: `APIError`).

    Returns
    -------
    dict or list
        The parsed JSON response body.

    Raises
    ------
    error_class
        On any network, HTTP, or parsing failure.
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        raise error_class(
            f"{service_name} request timed out after {timeout} seconds. "
            "Please try again."
        )
    except requests.exceptions.ConnectionError:
        raise error_class(
            f"Could not connect to {service_name}. "
            "Please check your internet connection."
        )
    except requests.exceptions.RequestException as exc:
        raise error_class(
            f"{service_name} request failed: {exc}"
        )

    # --- HTTP status ---
    if response.status_code != 200:
        raise error_class(
            f"{service_name} returned HTTP {response.status_code}. "
            "Please try again later."
        )

    # --- JSON parsing ---
    try:
        data = response.json()
    except ValueError:
        raise error_class(
            f"{service_name} returned an invalid response (not valid JSON)."
        )

    return data
