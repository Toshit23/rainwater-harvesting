"""
test_weather.py - Unit tests for api.weather (Open-Meteo rainfall).

All tests use unittest.mock to avoid hitting the real Open-Meteo API.

Run with:
    python -m pytest test_weather.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from unittest.mock import patch
from datetime import date, timedelta

from api.weather import get_historical_rainfall
from api.api_utils import WeatherAPIError


class TestGetHistoricalRainfall(unittest.TestCase):
    """Tests for get_historical_rainfall()."""

    # ----- Test 1: Valid rainfall request -----

    @patch("api.weather.make_api_request")
    def test_valid_request_returns_rainfall(self, mock_request):
        """A valid request should return total and daily rainfall in mm."""
        mock_request.return_value = {
            "daily": {
                "precipitation_sum": [0.0, 1.5, 3.2, 0.0, 5.0]
            }
        }

        result = get_historical_rainfall(
            19.076, 72.877, "2025-01-01", "2025-01-05"
        )

        self.assertAlmostEqual(result["total_rainfall_mm"], 9.7, places=1)
        self.assertEqual(len(result["daily_rainfall"]), 5)
        self.assertEqual(result["start_date"], "2025-01-01")
        self.assertEqual(result["end_date"], "2025-01-05")

    # ----- Test 2: Invalid coordinates -----

    def test_latitude_out_of_range_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_historical_rainfall(999, 72.0, "2025-01-01", "2025-01-31")

    def test_longitude_out_of_range_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_historical_rainfall(19.0, 999, "2025-01-01", "2025-01-31")

    def test_non_numeric_latitude_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_historical_rainfall("abc", 72.0, "2025-01-01", "2025-01-31")

    # ----- Test 3: Invalid dates -----

    def test_bad_date_format_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_historical_rainfall(19.0, 72.0, "not-a-date", "2025-01-31")

    def test_start_after_end_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_historical_rainfall(19.0, 72.0, "2025-12-31", "2025-01-01")

    def test_future_end_date_raises_value_error(self):
        future = (date.today() + timedelta(days=30)).isoformat()
        with self.assertRaises(ValueError):
            get_historical_rainfall(19.0, 72.0, "2025-01-01", future)

    # ----- Test 4: API failure -----

    @patch("api.weather.make_api_request")
    def test_api_error_response_raises_weather_error(self, mock_request):
        """If Open-Meteo returns an error payload, raise WeatherAPIError."""
        mock_request.return_value = {
            "error": True,
            "reason": "Invalid coordinates"
        }

        with self.assertRaises(WeatherAPIError):
            get_historical_rainfall(19.0, 72.0, "2025-01-01", "2025-01-31")

    @patch("api.weather.make_api_request")
    def test_missing_daily_data_raises_weather_error(self, mock_request):
        """If the response has no daily.precipitation_sum, raise error."""
        mock_request.return_value = {"hourly": {}}

        with self.assertRaises(WeatherAPIError):
            get_historical_rainfall(19.0, 72.0, "2025-01-01", "2025-01-31")

    # ----- Test 5: None values in precipitation -----

    @patch("api.weather.make_api_request")
    def test_none_values_treated_as_zero(self, mock_request):
        """None values in the daily array should become 0.0."""
        mock_request.return_value = {
            "daily": {
                "precipitation_sum": [1.0, None, 3.0, None, 2.0]
            }
        }

        result = get_historical_rainfall(
            19.0, 72.0, "2025-01-01", "2025-01-05"
        )

        self.assertEqual(result["daily_rainfall"], [1.0, 0.0, 3.0, 0.0, 2.0])
        self.assertAlmostEqual(result["total_rainfall_mm"], 6.0, places=1)

    @patch("api.weather.make_api_request")
    def test_network_failure_raises_weather_error(self, mock_request):
        """A network-level error should surface as WeatherAPIError."""
        mock_request.side_effect = WeatherAPIError("connection failed")

        with self.assertRaises(WeatherAPIError):
            get_historical_rainfall(19.0, 72.0, "2025-01-01", "2025-01-31")


if __name__ == "__main__":
    unittest.main()
