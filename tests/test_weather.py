"""
tests/test_weather.py – testy jednostkowe modułu weather.py
Uruchomienie: pytest tests/ -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from unittest.mock import patch, MagicMock
from weather import get_weather, _wmo_description, _wmo_icon, CITIES


# ── Testy funkcji pomocniczych ────────────────────────────────────────────

class TestWmoDescription:
    def test_clear_sky(self):
        assert _wmo_description(0) == "Bezchmurnie"

    def test_rain(self):
        assert "eszcz" in _wmo_description(63)   # Deszcz umiarkowany

    def test_thunderstorm(self):
        assert "urz" in _wmo_description(95)     # Burza

    def test_unknown_code(self):
        assert _wmo_description(999) == "Brak danych"


class TestWmoIcon:
    def test_clear(self):
        assert _wmo_icon(0) == "☀"

    def test_snow(self):
        assert _wmo_icon(71) == "❄"

    def test_thunderstorm(self):
        assert _wmo_icon(95) == "⛈"


# ── Testy pobierania danych ───────────────────────────────────────────────

class TestGetWeather:
    def test_unknown_city_returns_none(self):
        assert get_weather("NieistniejąceMiasto") is None

    def test_known_city_keys(self):
        """Sprawdza że wszystkie wymagane klucze są w odpowiedzi."""
        mock_response = {
            "current": {
                "temperature_2m": 15.3,
                "apparent_temperature": 13.0,
                "relative_humidity_2m": 65,
                "wind_speed_10m": 20.5,
                "wind_direction_10m": 270,
                "weathercode": 1,
                "cloudcover": 30,
                "precipitation": 0.0,
                "time": "2024-05-01T12:00",
            },
            "daily": {
                "time": ["2024-04-30","2024-05-01","2024-05-02","2024-05-03","2024-05-04","2024-05-05","2024-05-06"],
                "temperature_2m_max": [18,15,14,16,17,19,20],
                "temperature_2m_min": [8, 7, 6, 9, 10,11,12],
                "weathercode": [0, 1, 2, 3, 1, 0, 2],
                "precipitation_sum": [0,0,1.2,0.5,0,0,0],
            },
            "hourly": {
                "time": [f"2024-05-01T{h:02d}:00" for h in range(24)],
                "temperature_2m": [12+i*0.1 for i in range(24)],
            }
        }

        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status.return_value = None

        with patch('weather.requests.get', return_value=mock_resp):
            # Wyczyść cache przed testem
            import weather
            weather._cache.clear()
            result = get_weather("Warszawa")

        assert result is not None
        assert "current" in result
        assert "forecast" in result
        assert "chart_temps" in result

        current = result["current"]
        for key in ["temp","feels_like","humidity","wind_speed","icon","description"]:
            assert key in current, f"Brak klucza: {key}"

    def test_api_error_returns_none(self):
        """Sprawdza że błąd API zwraca None."""
        import weather
        weather._cache.clear()

        with patch('weather.requests.get', side_effect=Exception("Connection error")):
            result = get_weather("Kraków")

        assert result is None

    def test_case_insensitive_city(self):
        """Sprawdza wyszukiwanie miast bez rozróżniania wielkości liter."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "current": {
                "temperature_2m": 10, "apparent_temperature": 8,
                "relative_humidity_2m": 70, "wind_speed_10m": 15,
                "wind_direction_10m": 180, "weathercode": 3,
                "cloudcover": 80, "precipitation": 0, "time": "2024-05-01T10:00",
            },
            "daily": {"time":[],"temperature_2m_max":[],"temperature_2m_min":[],"weathercode":[],"precipitation_sum":[]},
            "hourly": {"time":[], "temperature_2m": []}
        }
        mock_resp.raise_for_status.return_value = None

        import weather
        weather._cache.clear()

        with patch('weather.requests.get', return_value=mock_resp):
            result = get_weather("warszawa")   # małe litery

        assert result is not None
        assert result["city"] == "Warszawa"

    def test_cache_works(self):
        """Sprawdza że cache działa – drugi call nie odpytuje API."""
        import weather
        weather._cache.clear()

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "current": {
                "temperature_2m": 20, "apparent_temperature": 18,
                "relative_humidity_2m": 50, "wind_speed_10m": 10,
                "wind_direction_10m": 90, "weathercode": 0,
                "cloudcover": 10, "precipitation": 0, "time": "2024-05-01T14:00",
            },
            "daily": {"time":[],"temperature_2m_max":[],"temperature_2m_min":[],"weathercode":[],"precipitation_sum":[]},
            "hourly": {"time":[], "temperature_2m": []}
        }

        with patch('weather.requests.get', return_value=mock_resp) as mock_get:
            weather.get_weather("Gdańsk")
            weather.get_weather("Gdańsk")
            assert mock_get.call_count == 1, "API powinno być odpytane tylko raz (cache)"

    def test_all_cities_in_dict(self):
        """Sprawdza że słownik miast zawiera oczekiwane miasta."""
        expected = ["Warszawa", "Kraków", "Gdańsk", "Wrocław", "Poznań"]
        for city in expected:
            assert city in CITIES, f"Brak miasta: {city}"
            lat, lon = CITIES[city]
            assert 49 <= lat <= 55, f"Nieprawidłowa szerokość geograficzna dla {city}"
            assert 14 <= lon <= 24, f"Nieprawidłowa długość geograficzna dla {city}"
