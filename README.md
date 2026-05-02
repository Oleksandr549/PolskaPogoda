# PolskaPogoda Dashboard

Platforma monitoringu pogody i jakości powietrza dla miast Polski.  
Projekt Zespołowy 2025/26 · Kolegium Informatyki Stosowanej

## Zespół

| Lp. | Imię i nazwisko         | Nr indeksu | Rola                      |
|-----|------------------------|------------|---------------------------|
| 1   | Oleksandr Vyshneskyi   | 69956      | Project Manager / Frontend|
| 2   | Maksym Vyshneskyi      | 69955      | Backend Developer         |
| 3   | Nazar Franchuk         | 69938      | Backend Developer         |
| 4   | Oleksandr Derkach      | 69933      | Frontend Developer        |
| 5   | Illia Vynokhodov       | 69954      | Frontend Developer        |
| 6   | Vitalii Pyzh           | 69948      | Tester / Dokumentacja     |

---

## Wymagania

- Python 3.11+
- pip

## Instalacja i uruchomienie

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/wasz-zespol/polskapogoda.git
cd polskapogoda

# 2. Zainstaluj zależności
pip3 install -r requirements.txt

# 3. (Opcjonalnie) Ustaw klucz OpenAQ API dla prawdziwych danych AQI
#    Bez klucza aplikacja używa danych szacunkowych
export OPENAQ_KEY=""

# 4. Uruchom serwer
cd backend
python3 app.py

# 5. Otwórz w przeglądarce
# http://localhost:5000
```

## Struktura projektu

```
polskapogoda/
├── backend/
│   ├── app.py          # Główna aplikacja Flask + endpointy API
│   ├── weather.py      # Pobieranie danych pogodowych (Open-Meteo)
│   └── aqi.py          # Pobieranie danych AQI (OpenAQ)
├── frontend/
│   ├── index.html      # Strona główna dashboardu
│   └── static/
│       ├── css/style.css   # Style CSS
│       └── js/app.js       # Logika JavaScript + wykresy
├── tests/
│   ├── test_weather.py # Testy modułu weather.py
│   └── test_aqi.py     # Testy modułu aqi.py
├── requirements.txt
└── README.md
```

## Endpointy API

| Endpoint             | Metoda | Parametry       | Opis                          |
|----------------------|--------|-----------------|-------------------------------|
| `/api/weather`       | GET    | `city` (string) | Pogoda + prognoza 5-dniowa    |
| `/api/aqi`           | GET    | `city` (string) | Jakość powietrza (AQI)        |
| `/api/cities`        | GET    | —               | Lista dostępnych miast        |

### Przykład odpowiedzi `/api/weather?city=Warszawa`

```json
{
  "city": "Warszawa",
  "updated_at": "2024-05-01T12:00",
  "current": {
    "temp": 15,
    "feels_like": 13,
    "humidity": 65,
    "wind_speed": 20,
    "wind_dir": 270,
    "cloudcover": 30,
    "icon": "⛅",
    "description": "Częściowe zachmurzenie"
  },
  "forecast": [...],
  "chart_temps": [...]
}
```

## Uruchomienie testów

```bash
pip3 install pytest
pytest tests/ -v
```

## Zewnętrzne API

| API           | URL                       | Klucz API | Dane                    |
|---------------|---------------------------|-----------|-------------------------|
| Open-Meteo    | https://api.open-meteo.com| Nie       | Pogoda, prognoza        |
| OpenAQ v3     | https://api.openaq.org    | Tak (darmowy) | Jakość powietrza   |

Rejestracja OpenAQ: https://explore.openaq.org/
