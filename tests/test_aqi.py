"""
tests/test_aqi.py – testy jednostkowe modułu aqi.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from aqi import _calc_aqi_pl, get_aqi, _fallback_data


class TestCalcAqi:
    def test_very_good(self):
        val, cat, color = _calc_aqi_pl(5.0)
        assert cat == "Bardzo dobry"
        assert color == "#00b050"

    def test_good(self):
        val, cat, color = _calc_aqi_pl(20.0)
        assert cat == "Dobry"

    def test_moderate(self):
        val, cat, color = _calc_aqi_pl(45.0)
        assert cat == "Umiarkowany"

    def test_bad(self):
        val, cat, color = _calc_aqi_pl(90.0)
        assert cat == "Zły"

    def test_none_returns_zero(self):
        val, cat, color = _calc_aqi_pl(None)
        assert val == 0
        assert color == "#888888"


class TestFallbackData:
    def test_has_required_keys(self):
        data = _fallback_data("Warszawa")
        for key in ["city", "aqi", "category", "color", "pollutants"]:
            assert key in data

    def test_pollutants_present(self):
        data = _fallback_data("Kraków")
        for p in ["pm25", "pm10", "no2", "o3"]:
            assert p in data["pollutants"]

    def test_unknown_city_returns_none(self):
        assert get_aqi("NieistniejąceMiasto") is None
