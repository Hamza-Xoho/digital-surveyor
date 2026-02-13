"""Tests for geocoding service — postcode validation, normalisation, coordinate transforms."""

import pytest

from app.services.geocoding import (
    bng_to_latlng,
    latlng_to_bng,
    normalise_postcode,
    validate_postcode,
)


class TestNormalisePostcode:
    def test_already_normalised(self):
        assert normalise_postcode("BN1 1AB") == "BN1 1AB"

    def test_lowercase(self):
        assert normalise_postcode("bn1 1ab") == "BN1 1AB"

    def test_no_space(self):
        assert normalise_postcode("BN11AB") == "BN1 1AB"

    def test_extra_whitespace(self):
        assert normalise_postcode("  BN1  1AB ") == "BN1 1AB"

    def test_short_postcode(self):
        assert normalise_postcode("E1") == "E1"

    def test_long_outward(self):
        assert normalise_postcode("SW1A2AA") == "SW1A 2AA"


class TestValidatePostcode:
    def test_valid_standard(self):
        assert validate_postcode("BN1 1AB") is True

    def test_valid_london(self):
        assert validate_postcode("SW1A 2AA") is True

    def test_valid_no_space(self):
        assert validate_postcode("BN11AB") is True

    def test_invalid_numbers_only(self):
        assert validate_postcode("12345") is False

    def test_invalid_empty(self):
        assert validate_postcode("") is False

    def test_invalid_too_short(self):
        assert validate_postcode("B1") is False

    def test_invalid_non_uk(self):
        assert validate_postcode("90210") is False


class TestCoordinateTransforms:
    """Test BNG <-> WGS84 round-trips.

    Uses known reference point: Tower of London
    BNG: 533600, 180500 ≈ WGS84: 51.508, -0.076
    """

    def test_latlng_to_bng_tower(self):
        easting, northing = latlng_to_bng(51.508, -0.076)
        assert abs(easting - 533600) < 200
        assert abs(northing - 180500) < 200

    def test_bng_to_latlng_tower(self):
        lat, lon = bng_to_latlng(533600, 180500)
        assert abs(lat - 51.508) < 0.01
        assert abs(lon - (-0.076)) < 0.01

    def test_round_trip(self):
        original_lat, original_lon = 51.5074, -0.1278  # Central London
        easting, northing = latlng_to_bng(original_lat, original_lon)
        lat, lon = bng_to_latlng(easting, northing)
        assert abs(lat - original_lat) < 0.0001
        assert abs(lon - original_lon) < 0.0001

    def test_brighton_coords(self):
        """Brighton: BNG ~530600, 104100."""
        easting, northing = latlng_to_bng(50.822, -0.137)
        assert abs(easting - 530600) < 500
        assert abs(northing - 104100) < 500
