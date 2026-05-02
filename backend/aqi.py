"""
aqi.py – pobieranie danych o jakości powietrza z OpenAQ API v3.
Bezpłatny klucz: https://explore.openaq.org/
Dokumentacja: https://docs.openaq.org/
"""

import requests
import time

# Współrzędne miast (te same co weather.py)
CITY_COORDS = {
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

# Prosta pamięć podręczna
_cache: dict = {}
CACHE_TTL = 1800  # 30 minut

# Klucz API – ustaw jako zmienną środowiskową OPENAQ_KEY lub wpisz tu
import os
OPENAQ_KEY = os.environ.get("OPENAQ_KEY", "")


def _calc_aqi_pl(pm25: float | None) -> tuple[int, str, str]:
    """
    Oblicza indeks AQI na podstawie PM2.5 wg GIOŚ (Polska).
    Zwraca: (wartość_int, kategoria, kolor_hex)
    """
    if pm25 is None:
        return 0, "Brak danych", "#888888"
    if pm25 <= 13:   return int(pm25 * 4),    "Bardzo dobry", "#00b050"
    if pm25 <= 35:   return int(pm25 * 2.5),  "Dobry",        "#92d050"
    if pm25 <= 55:   return int(pm25 * 1.6),  "Umiarkowany",  "#ffff00"
    if pm25 <= 75:   return int(pm25 * 1.2),  "Dostateczny",  "#ff9900"
    if pm25 <= 110:  return int(pm25 * 0.9),  "Zły",          "#ff0000"
    return 200,                                "Bardzo zły",   "#990000"


def _fallback_data(city: str) -> dict:
    """
    Zwraca dane zastępcze gdy API jest niedostępne.
    W produkcji zastąp prawdziwymi danymi historycznymi.
    """
    import random
    random.seed(hash(city) % 999)
    pm25 = random.uniform(5, 80)
    pm10 = pm25 * random.uniform(1.3, 2.0)
    no2  = random.uniform(10, 60)
    o3   = random.uniform(20, 90)
    aqi_val, aqi_cat, aqi_color = _calc_aqi_pl(pm25)
    return {
        "city":      city,
        "source":    "dane_zastępcze",
        "aqi":       aqi_val,
        "category":  aqi_cat,
        "color":     aqi_color,
        "pollutants": {
            "pm25": round(pm25, 1),
            "pm10": round(pm10, 1),
            "no2":  round(no2, 1),
            "o3":   round(o3, 1),
        }
    }


def get_aqi(city: str) -> dict | None:
    """
    Pobiera dane AQI dla podanego miasta z OpenAQ API.
    Jeśli klucz API nie jest ustawiony, zwraca dane zastępcze.
    """
    city = city.strip()

    # Szukaj bez rozróżniania wielkości liter
    coords = None
    matched_city = city
    for name, c in CITY_COORDS.items():
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

    # Jeśli brak klucza API – użyj danych zastępczych
    if not OPENAQ_KEY:
        result = _fallback_data(matched_city)
        _cache[city] = (now, result)
        return result

    lat, lon = coords
    radius_m = 25000  # 25 km

    headers = {"X-API-Key": OPENAQ_KEY}
    url = "https://api.openaq.org/v3/locations"
    params = {
        "coordinates": f"{lat},{lon}",
        "radius":      radius_m,
        "limit":       5,
        "order_by":    "distance",
        "sort_order":  "asc",
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        locations = resp.json().get("results", [])
    except Exception:
        result = _fallback_data(matched_city)
        _cache[city] = (now, result)
        return result

    if not locations:
        result = _fallback_data(matched_city)
        _cache[city] = (now, result)
        return result

    # Zbierz pomiary z najbliższych stacji
    pollutants_sum = {"pm25": [], "pm10": [], "no2": [], "o3": []}
    param_map = {"pm25": "pm25", "pm10": "pm10", "no2": "no2", "o3": "o3"}

    for loc in locations[:3]:
        loc_id = loc.get("id")
        try:
            r = requests.get(
                f"https://api.openaq.org/v3/locations/{loc_id}/latest",
                headers=headers, timeout=8
            )
            r.raise_for_status()
            measurements = r.json().get("results", [])
        except Exception:
            continue

        for m in measurements:
            param = m.get("parameter", {}).get("name", "").lower()
            value = m.get("value")
            if param in param_map and value is not None and value >= 0:
                pollutants_sum[param].append(value)

    # Oblicz średnie
    def avg(lst): return round(sum(lst) / len(lst), 1) if lst else None

    pm25_val = avg(pollutants_sum["pm25"])
    pm10_val = avg(pollutants_sum["pm10"])
    no2_val  = avg(pollutants_sum["no2"])
    o3_val   = avg(pollutants_sum["o3"])

    aqi_val, aqi_cat, aqi_color = _calc_aqi_pl(pm25_val)

    result = {
        "city":     matched_city,
        "source":   "openaq",
        "aqi":      aqi_val,
        "category": aqi_cat,
        "color":    aqi_color,
        "pollutants": {
            "pm25": pm25_val,
            "pm10": pm10_val,
            "no2":  no2_val,
            "o3":   o3_val,
        }
    }

    _cache[city] = (now, result)
    return result
