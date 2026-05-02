from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os

from weather import get_weather
from aqi import get_aqi

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend'),
    static_url_path=''
)
CORS(app)

# ── Strona główna ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# ── API: pogoda ───────────────────────────────────────────────────────────────
@app.route('/api/weather')
def weather():
    """
    Query params:
        city  – nazwa miasta (domyślnie: Warszawa)
    Zwraca JSON z aktualnymi danymi i prognozą 5-dniową.
    """
    from flask import request
    city = request.args.get('city', 'Warszawa')
    data = get_weather(city)
    if data is None:
        return jsonify({'error': 'Nie można pobrać danych pogodowych'}), 502
    return jsonify(data)

# ── API: jakość powietrza ─────────────────────────────────────────────────────
@app.route('/api/aqi')
def aqi():
    """
    Query params:
        city  – nazwa miasta (domyślnie: Warszawa)
    Zwraca JSON z indeksem AQI i stężeniami PM2.5, PM10, NO2, O3.
    """
    from flask import request
    city = request.args.get('city', 'Warszawa')
    data = get_aqi(city)
    if data is None:
        return jsonify({'error': 'Nie można pobrać danych AQI'}), 502
    return jsonify(data)

# ── API: lista miast ──────────────────────────────────────────────────────────
@app.route('/api/cities')
def cities():
    from weather import CITIES
    return jsonify(list(CITIES.keys()))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
