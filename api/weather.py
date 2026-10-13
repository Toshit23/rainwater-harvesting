"""
weather.py - Open-Meteo historical rainfall retrieval.

Purpose:
    Fetch historical daily precipitation (rainfall) data from the Open-Meteo
    Archive API for a given latitude/longitude and date range.

    The module returns clean, structured data - the calling code (calculation
    module) only needs `result["total_rainfall_mm"]`.

Open-Meteo Archive API docs:
    https://open-meteo.com/en/docs/historical-weather-api

Rainfall is returned in **millimetres (mm)**.

Usage:
    >>> from api.weather import get_historical_rainfall
    >>> get_historical_rainfall(19.076, 72.877, "2025-01-01", "2025-12-31")
    {
        "latitude": 19.076,
        "longitude": 72.877,
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "total_rainfall_mm": 842.5,
        "daily_rainfall": [0.0, 0.0, 1.2, ...]
    }
"""

from datetime import datetime, date

from .api_utils import (
    WeatherAPIError,
    make_api_request,
    WEATHER_TIMEOUT,
)

# Open-Meteo *archive* endpoint - serves only past dates.
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def _parse_date(value: str, label: str) -> date:
    """Parse an ISO-format date string (YYYY-MM-DD) and return a date object.

    Raises ValueError with a user-friendly message on failure.
    """
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(
            f'Invalid {label}: "{value}". '
            "Please use YYYY-MM-DD format (e.g. 2025-01-01)."
        )


def get_historical_rainfall(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> dict:
    """Fetch historical daily precipitation from Open-Meteo.

    Parameters
    ----------
    latitude : float
        Latitude of the location (-90 to 90).  Obtained internally from
        `geocode_location()`; the user never enters this.
    longitude : float
        Longitude of the location (-180 to 180).  Obtained internally.
    start_date : str
        Start of the historical period in `YYYY-MM-DD` format.
    end_date : str
        End of the historical period in `YYYY-MM-DD` format.
        Must not be in the future (the archive API only has past data).

    Returns
    -------
    dict
        {
            "latitude": float,
            "longitude": float,
            "start_date": str,
            "end_date": str,
            "total_rainfall_mm": float,   # sum of daily precipitation
            "daily_rainfall": list[float]  # one value per day, in mm
        }

    Raises
    ------
    ValueError
        If coordinates or dates are invalid.
    WeatherAPIError
        If the API request fails or returns no usable data.
    """

    # ---- 1. Validate coordinates ----
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        raise ValueError(
            "Latitude and longitude must be numeric values."
        )

    if not (-90 <= latitude <= 90):
        raise ValueError(
            f"Latitude {latitude} is out of range (must be -90 to 90)."
        )
    if not (-180 <= longitude <= 180):
        raise ValueError(
            f"Longitude {longitude} is out of range (must be -180 to 180)."
        )

    # ---- 2. Validate dates ----
    sd = _parse_date(start_date, "start_date")
    ed = _parse_date(end_date, "end_date")

    if sd > ed:
        raise ValueError(
            f"start_date ({start_date}) must be on or before "
            f"end_date ({end_date})."
        )

    today = date.today()
    if ed >= today:
        raise ValueError(
            f"end_date ({end_date}) must be in the past. "
            f"The Open-Meteo archive only contains historical data "
            f"(today is {today.isoformat()})."
        )

    # ---- 3. Build request ----
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "precipitation_sum",
        "timezone": "auto",
    }

    data = make_api_request(
        url=OPEN_METEO_ARCHIVE_URL,
        params=params,
        timeout=WEATHER_TIMEOUT,
        service_name="Open-Meteo Historical Weather",
        error_class=WeatherAPIError,
    )

    # ---- 4. Check for API-level errors ----
    if "error" in data and data["error"]:
        reason = data.get("reason", "Unknown error")
        raise WeatherAPIError(
            f"Open-Meteo returned an error: {reason}"
        )

    # ---- 5. Extract daily precipitation ----
    try:
        daily_data = data["daily"]["precipitation_sum"]
    except (KeyError, TypeError):
        raise WeatherAPIError(
            "Open-Meteo response is missing daily precipitation data. "
            "The requested location or date range may not have coverage."
        )

    if not isinstance(daily_data, list) or len(daily_data) == 0:
        raise WeatherAPIError(
            "Open-Meteo returned no precipitation data for the "
            "requested location and date range."
        )

    # ---- 6. Clean data: replace None values with 0.0 ----
    daily_rainfall = [
        round(float(v), 2) if v is not None else 0.0
        for v in daily_data
    ]

    total_rainfall_mm = round(sum(daily_rainfall), 2)

    # ---- 7. Return structured result ----
    return {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "total_rainfall_mm": total_rainfall_mm,
        "daily_rainfall": daily_rainfall,
    }
