"""
test_location.py - Unit tests for api.location (Nominatim geocoding).

All tests use unittest.mock to avoid hitting the real Nominatim API,
so they run offline and are fast + deterministic.

Run with:
    python -m pytest test_location.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from unittest.mock import patch, MagicMock

from api.location import geocode_location
from api.api_utils import GeocodingError


class TestGeocodeLocation(unittest.TestCase):
    """Tests for geocode_location()."""

    # ----- Test 1: Valid location -----

    @patch("api.location.make_api_request")
    def test_valid_location_returns_coords(self, mock_request):
        """A valid address should return lat, lon, and display_name."""
        mock_request.return_value = [
            {
                "lat": "19.0760",
                "lon": "72.8777",
                "display_name": "Mumbai, Maharashtra, India",
            }
        ]

        result = geocode_location("Mumbai, Maharashtra, India")

        self.assertAlmostEqual(result["latitude"], 19.0760, places=3)
        self.assertAlmostEqual(result["longitude"], 72.8777, places=3)
        self.assertEqual(result["display_name"], "Mumbai, Maharashtra, India")

    # ----- Test 2: Empty address -----

    def test_empty_address_raises_value_error(self):
        """An empty string should raise ValueError immediately."""
        with self.assertRaises(ValueError):
            geocode_location("")

    def test_whitespace_address_raises_value_error(self):
        """A whitespace-only string should raise ValueError."""
        with self.assertRaises(ValueError):
            geocode_location("   ")

    # ----- Test 3: No results -----

    @patch("api.location.make_api_request")
    def test_no_results_raises_geocoding_error(self, mock_request):
        """If Nominatim returns an empty list, raise GeocodingError."""
        mock_request.return_value = []

        with self.assertRaises(GeocodingError):
            geocode_location("some_random_nonexistent_place_123456")

    # ----- Test 4: Network timeout -----

    @patch("api.location.make_api_request")
    def test_timeout_raises_geocoding_error(self, mock_request):
        """A timeout in the HTTP layer should surface as GeocodingError."""
        mock_request.side_effect = GeocodingError("timed out")

        with self.assertRaises(GeocodingError):
            geocode_location("Mumbai")

    # ----- Test 5: Malformed API response -----

    @patch("api.location.make_api_request")
    def test_malformed_response_raises_geocoding_error(self, mock_request):
        """If the response lacks 'lat'/'lon', raise GeocodingError."""
        mock_request.return_value = [{"name": "Mumbai"}]  # no lat/lon

        with self.assertRaises(GeocodingError):
            geocode_location("Mumbai")

    # ----- Test 6: Non-list response -----

    @patch("api.location.make_api_request")
    def test_non_list_response_raises_geocoding_error(self, mock_request):
        """If Nominatim returns a dict instead of a list, handle it."""
        mock_request.return_value = {"error": "something"}

        with self.assertRaises(GeocodingError):
            geocode_location("Mumbai")


if __name__ == "__main__":
    unittest.main()
