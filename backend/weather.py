"""
weather.py – pobieranie danych pogodowych z Open-Meteo API.
Nie wymaga klucza API.
Dokumentacja: https://open-meteo.com/en/docs
"""

import requests
import time

# Słownik: nazwa miasta → (szerokość, długość geograficzna)
CITIES = {
    "Warszawa":   (52.2297, 21.0122),
    "Kraków":     (50.0647, 19.9450),
    "Gdańsk":     (54.3520, 18.6466),
    "Wrocław":    (51.1079, 17.0385),
    "Poznań":     (52.4064, 16.9252),
    "Łódź":       (51.7592, 19.4560),
    "Katowice":   (50.2598, 19.0216),
    "Szczecin":   (53.4285, 14.5528),
    "Lublin":     (51.2465, 22.5684),
    "Białystok":  (53.1325, 23.1688),
}

# Prosta pamięć podręczna: {city: (timestamp, data)}
_cache: dict = {}
CACHE_TTL = 1800  # 30 minut


def _wmo_description(code: int) -> str:
    """Tłumaczy kod WMO na opis po polsku."""
    descriptions = {
        0:  "Bezchmurnie",
        1:  "Przeważnie słonecznie",
        2:  "Częściowe zachmurzenie",
        3:  "Pochmurno",
        45: "Mgła",
        48: "Mgła szronowa",
        51: "Mżawka lekka",
        53: "Mżawka umiarkowana",
        55: "Mżawka gęsta",
        61: "Deszcz lekki",
        63: "Deszcz umiarkowany",
        65: "Deszcz intensywny",
        71: "Śnieg lekki",
        73: "Śnieg umiarkowany",
        75: "Śnieg intensywny",
        77: "Ziarna śniegu",
        80: "Przelotny deszcz lekki",
        81: "Przelotny deszcz",
        82: "Przelotny deszcz intensywny",
        85: "Przelotny śnieg lekki",
        86: "Przelotny śnieg intensywny",
        95: "Burza",
        96: "Burza z gradem",
        99: "Burza z silnym gradem",
    }
    return descriptions.get(code, "Brak danych")


def _wmo_icon(code: int) -> str:
    """Zwraca emoji dla kodu WMO."""
    if code == 0:               return "☀"
    if code in (1, 2):         return "⛅"
    if code == 3:               return "☁"
    if code in (45, 48):       return "🌫"
    if code in (51, 53, 55):   return "🌦"
    if code in (61, 63, 65):   return "🌧"
    if code in (71, 73, 75, 77): return "❄"
    if code in (80, 81, 82):   return "🌧"
    if code in (85, 86):       return "🌨"
    if code in (95, 96, 99):   return "⛈"
    return "🌡"


def get_weather(city: str) -> dict | None:
    """
    Pobiera dane pogodowe dla podanego miasta.
    Zwraca słownik z aktualnymi danymi i prognozą lub None przy błędzie.
    """
    city = city.strip()

    # Szukaj bez rozróżniania wielkości liter
    coords = None
    matched_city = city
    for name, c in CITIES.items():
        if name.lower() == city.lower():
            coords = c
            matched_city = name
            break

    if coords is None:
        return None

    # Sprawdź cache
    now = time.time()
    if city in _cache:
        ts, data = _cache[city]
        if now - ts < CACHE_TTL:
            return data

    lat, lon = coords

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":  lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "weathercode",
            "cloudcover",
            "precipitation",
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "weathercode",
            "precipitation_sum",
        ],
        "hourly": ["temperature_2m"],
        "timezone": "Europe/Warsaw",
        "forecast_days": 6,
        "past_days": 1,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        raw = resp.json()
    except Exception:
        return None

    current = raw.get("current", {})
    daily   = raw.get("daily", {})
    hourly  = raw.get("hourly", {})

    # Buduj prognozę 5 dni (od jutra)
    forecast = []
    dates      = daily.get("time", [])
    max_temps  = daily.get("temperature_2m_max", [])
    min_temps  = daily.get("temperature_2m_min", [])
    codes      = daily.get("weathercode", [])
    precips    = daily.get("precipitation_sum", [])

    # Pomiń dzień 0 (wczoraj) i dzień 1 (dziś), weź kolejne 5
    start = 2
    for i in range(start, min(start + 5, len(dates))):
        forecast.append({
            "date":        dates[i],
            "temp_max":    round(max_temps[i]) if i < len(max_temps) else None,
            "temp_min":    round(min_temps[i]) if i < len(min_temps) else None,
            "code":        codes[i]            if i < len(codes)     else 0,
            "icon":        _wmo_icon(codes[i] if i < len(codes) else 0),
            "description": _wmo_description(codes[i] if i < len(codes) else 0),
            "precip_mm":   round(precips[i], 1) if i < len(precips) else 0,
        })

    # Dane godzinowe temperatury z ostatnich 24h (do wykresu)
    times_h  = hourly.get("time", [])
    temps_h  = hourly.get("temperature_2m", [])
    chart_data = [
        {"time": t, "temp": round(v, 1)}
        for t, v in zip(times_h, temps_h)
        if v is not None
    ][-48:]  # ostatnie 48 godzin

    wcode = current.get("weathercode", 0)

    result = {
        "city":        matched_city,
        "lat":         lat,
        "lon":         lon,
        "updated_at":  current.get("time", ""),
        "current": {
            "temp":         round(current.get("temperature_2m", 0)),
            "feels_like":   round(current.get("apparent_temperature", 0)),
            "humidity":     current.get("relative_humidity_2m", 0),
            "wind_speed":   round(current.get("wind_speed_10m", 0)),
            "wind_dir":     current.get("wind_direction_10m", 0),
            "cloudcover":   current.get("cloudcover", 0),
            "precipitation":current.get("precipitation", 0),
            "code":         wcode,
            "icon":         _wmo_icon(wcode),
            "description":  _wmo_description(wcode),
        },
        "forecast":    forecast,
        "chart_temps": chart_data,
    }

    _cache[city] = (now, result)
    return result
