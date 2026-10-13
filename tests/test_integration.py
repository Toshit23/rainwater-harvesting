"""
test_integration.py - Live API integration tests.

These tests call the REAL Nominatim and Open-Meteo APIs.
Run manually to verify end-to-end connectivity:

    python test_integration.py

Do NOT run these in CI (they need internet and may be rate-limited).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import (
    geocode_location,
    get_historical_rainfall,
    get_rainfall_for_location,
    GeocodingError,
    WeatherAPIError,
)


def separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_1_valid_geocoding():
    """Test 1: Geocode a valid address."""
    separator("Test 1 - Valid Geocoding")
    address = "Mumbai, Maharashtra, India"
    print(f"  Address: {address}")

    result = geocode_location(address)

    print(f"  Latitude:     {result['latitude']}")
    print(f"  Longitude:    {result['longitude']}")
    print(f"  Display name: {result['display_name']}")

    assert isinstance(result["latitude"], float)
    assert isinstance(result["longitude"], float)
    assert 18 < result["latitude"] < 20, "Mumbai lat should be ~19"
    assert 72 < result["longitude"] < 73, "Mumbai lon should be ~72.8"
    print("  PASSED")


def test_2_invalid_geocoding():
    """Test 2: Geocode a nonsense address."""
    separator("Test 2 - Invalid Geocoding")
    address = "some_random_nonexistent_place_123456"
    print(f"  Address: {address}")

    try:
        geocode_location(address)
        print("  FAILED - should have raised GeocodingError")
    except GeocodingError as e:
        print(f"  Correctly raised GeocodingError: {e}")
        print("  PASSED")


def test_3_valid_rainfall():
    """Test 3: Fetch rainfall for Mumbai, Jan 2025."""
    separator("Test 3 - Valid Rainfall Request")
    lat, lon = 19.076, 72.877
    start, end = "2025-01-01", "2025-03-31"
    print(f"  Coords: ({lat}, {lon})")
    print(f"  Period: {start} to {end}")

    result = get_historical_rainfall(lat, lon, start, end)

    print(f"  Total rainfall: {result['total_rainfall_mm']} mm")
    print(f"  Days of data:   {len(result['daily_rainfall'])}")
    print(f"  First 5 days:   {result['daily_rainfall'][:5]}")

    assert result["total_rainfall_mm"] >= 0
    assert len(result["daily_rainfall"]) > 0
    print("  PASSED")


def test_4_invalid_coordinates():
    """Test 4: Invalid coordinates should raise ValueError."""
    separator("Test 4 - Invalid Coordinates")

    try:
        get_historical_rainfall(999, 999, "2025-01-01", "2025-01-31")
        print("  FAILED - should have raised ValueError")
    except ValueError as e:
        print(f"  Correctly raised ValueError: {e}")
        print("  PASSED")


def test_5_full_pipeline():
    """Test 5: Full address -> rainfall pipeline."""
    separator("Test 5 - Full Pipeline (get_rainfall_for_location)")
    address = "K J Somaiya Institute of Technology, Mumbai"
    start, end = "2025-06-01", "2025-06-30"
    print(f"  Address: {address}")
    print(f"  Period:  {start} to {end}")

    result = get_rainfall_for_location(address, start, end)

    print(f"  Location:       {result['location_name']}")
    print(f"  Latitude:       {result['latitude']}")
    print(f"  Longitude:      {result['longitude']}")
    print(f"  Total rainfall: {result['total_rainfall_mm']} mm")
    print(f"  Days of data:   {len(result['daily_rainfall'])}")

    # This is exactly what Member 3 would do:
    rainfall_mm = result["total_rainfall_mm"]
    print(f"\n  Member 3 receives: rainfall_mm = {rainfall_mm}")

    assert rainfall_mm >= 0
    print("  PASSED")


if __name__ == "__main__":
    passed = 0
    failed = 0
    tests = [
        test_1_valid_geocoding,
        test_2_invalid_geocoding,
        test_3_valid_rainfall,
        test_4_invalid_coordinates,
        test_5_full_pipeline,
    ]

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAILED with exception: {e}")
            failed += 1

    separator("SUMMARY")
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")
    sys.exit(1 if failed else 0)
