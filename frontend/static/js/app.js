/**
 * app.js – logika dashboardu PolskaPogoda
 * Pobiera dane z backendu Flask i aktualizuje UI.
 */

const API = '';  // pusty string = ten sam origin co serwer Flask

let tempChart = null;

// ── Pomocnicze ────────────────────────────────────────────────────────────────

function windDirection(deg) {
  const dirs = ['N','NE','E','SE','S','SW','W','NW'];
  return dirs[Math.round(deg / 45) % 8];
}

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T12:00:00');
  const days = ['Nd','Pn','Wt','Śr','Cz','Pt','Sb'];
  const months = ['sty','lut','mar','kwi','maj','cze','lip','sie','wrz','paź','lis','gru'];
  return `${days[d.getDay()]} ${d.getDate()} ${months[d.getMonth()]}`;
}

function showError(msg) {
  const banner = document.getElementById('error-banner');
  document.getElementById('error-msg').textContent = msg;
  banner.hidden = false;
  setTimeout(() => { banner.hidden = true; }, 4000);
}

function hideError() {
  const banner = document.getElementById('error-banner');
  if (banner) banner.hidden = true;
}

function showSkeleton() {
  ['sk-current','sk-aqi','sk-chart'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'flex';
  });
  document.getElementById('hero-content').hidden = true;
  document.getElementById('aqi-content').hidden  = true;
  document.getElementById('chart-wrap').hidden   = true;
}

function hideSkeleton() {
  ['sk-current','sk-aqi','sk-chart'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
}

// ── Render: pogoda ────────────────────────────────────────────────────────────

function renderWeather(data) {
  const c = data.current;
  document.getElementById('weather-icon').textContent = c.icon || '🌡';
  document.getElementById('temp-main').textContent    = c.temp ?? '—';
  document.getElementById('hero-desc').textContent    = c.description || '';
  document.getElementById('feels-like').textContent   = `${c.feels_like}°C`;
  document.getElementById('humidity').textContent     = `${c.humidity}%`;
  document.getElementById('wind').textContent         = `${c.wind_speed} km/h ${windDirection(c.wind_dir)}`;
  document.getElementById('cloudcover').textContent   = `${c.cloudcover}%`;

  // Czas ostatniego zapytania (nie czas serwera)
  const now = new Date();
  document.getElementById('update-time').textContent =
    `Aktualizacja: ${now.toLocaleTimeString('pl-PL', {hour:'2-digit', minute:'2-digit'})}`;

  document.getElementById('hero-content').hidden = false;
}

// ── Render: AQI ───────────────────────────────────────────────────────────────

function renderAqi(data) {
  document.getElementById('aqi-score').textContent = data.aqi ?? '—';

  const badge = document.getElementById('aqi-badge');
  badge.textContent = data.category || '—';

  const colorMap = {
    'Bardzo dobry': ['rgba(63,185,80,0.15)',  '#3fb950', 'rgba(63,185,80,0.25)'],
    'Dobry':        ['rgba(63,185,80,0.10)',  '#56d364', 'rgba(63,185,80,0.20)'],
    'Umiarkowany':  ['rgba(210,153,34,0.15)', '#d29922', 'rgba(210,153,34,0.25)'],
    'Dostateczny':  ['rgba(255,160,0,0.15)',  '#ffa500', 'rgba(255,160,0,0.25)'],
    'Zły':          ['rgba(248,81,73,0.15)',  '#f85149', 'rgba(248,81,73,0.25)'],
    'Bardzo zły':   ['rgba(180,0,0,0.2)',     '#ff4444', 'rgba(180,0,0,0.3)'],
  };
  const [bg, color, border] = colorMap[data.category] || colorMap['Umiarkowany'];
  badge.style.background  = bg;
  badge.style.color       = color;
  badge.style.borderColor = border;

  const p = data.pollutants || {};
  const pollutants = [
    { name: 'PM2.5', key: 'pm25', max: 75,  unit: 'µg/m³', color: '#58a6ff' },
    { name: 'PM10',  key: 'pm10', max: 150, unit: 'µg/m³', color: '#56d364' },
    { name: 'NO₂',   key: 'no2',  max: 100, unit: 'µg/m³', color: '#d29922' },
    { name: 'O₃',    key: 'o3',   max: 180, unit: 'µg/m³', color: '#f0883e' },
  ];

  const container = document.getElementById('pollutant-bars');
  container.innerHTML = '';

  pollutants.forEach(pol => {
    const val = p[pol.key];
    const pct = val != null ? Math.min(100, Math.round(val / pol.max * 100)) : 0;
    const display = val != null ? `${val} ${pol.unit}` : 'brak danych';

    container.innerHTML += `
      <div class="poll-row">
        <div class="poll-header">
          <span class="poll-name">${pol.name}</span>
          <span class="poll-val">${display}</span>
        </div>
        <div class="poll-track">
          <div class="poll-fill" style="width:0%;background:${pol.color}"
               data-target="${pct}"></div>
        </div>
      </div>`;
  });

  requestAnimationFrame(() => {
    document.querySelectorAll('.poll-fill').forEach(el => {
      el.style.width = el.dataset.target + '%';
    });
  });

  const srcEl = document.getElementById('aqi-source');
  if (srcEl) {
    srcEl.textContent = data.source === 'openaq' ? 'OpenAQ' : 'dane szacunkowe';
  }

  document.getElementById('aqi-content').hidden = false;
}

// ── Render: wykres temperatury ────────────────────────────────────────────────

function renderChart(chartData) {
  const wrap   = document.getElementById('chart-wrap');
  const canvas = document.getElementById('temp-chart');

  if (!chartData || chartData.length === 0) {
    wrap.hidden = true;
    return;
  }

  const data24 = chartData.slice(-24);
  const labels = data24.map(d => {
    const t = new Date(d.time);
    return t.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });
  });
  const temps = data24.map(d => d.temp);

  if (tempChart) tempChart.destroy();

  const ctx = canvas.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 110);
  gradient.addColorStop(0, 'rgba(88,166,255,0.25)');
  gradient.addColorStop(1, 'rgba(88,166,255,0)');

  tempChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Temperatura (°C)',
        data: temps,
        fill: true,
        backgroundColor: gradient,
        borderColor: '#58a6ff',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: '#58a6ff',
        tension: 0.4,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1c2128',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          titleColor: '#8b949e',
          bodyColor: '#e6edf3',
          callbacks: { label: ctx => `${ctx.parsed.y}°C` }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
          ticks: { color: '#656d76', font: { family: "'DM Mono'", size: 10 }, maxTicksLimit: 8 }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
          ticks: { color: '#656d76', font: { family: "'DM Mono'", size: 10 }, callback: v => v + '°' }
        }
      }
    }
  });

  wrap.hidden = false;
}

// ── Render: prognoza ──────────────────────────────────────────────────────────

function renderForecast(forecast) {
  const grid = document.getElementById('forecast-grid');
  grid.innerHTML = '';

  if (!forecast || forecast.length === 0) return;

  forecast.forEach(day => {
    const precip = day.precip_mm > 0
      ? `<div class="fc-precip">💧 ${day.precip_mm} mm</div>`
      : '';

    grid.innerHTML += `
      <div class="forecast-day">
        <div class="fc-date">${formatDate(day.date)}</div>
        <div class="fc-icon">${day.icon}</div>
        <div class="fc-desc">${day.description}</div>
        <div class="fc-temps">
          <span class="fc-max">${day.temp_max ?? '—'}°</span>
          <span class="fc-min">${day.temp_min ?? '—'}°</span>
        </div>
        ${precip}
      </div>`;
  });
}

// ── Fetch i główna logika ─────────────────────────────────────────────────────

async function loadData(city) {
  showSkeleton();
  hideError();

  try {
    const [weatherResp, aqiResp] = await Promise.allSettled([
      fetch(`${API}/api/weather?city=${encodeURIComponent(city)}`),
      fetch(`${API}/api/aqi?city=${encodeURIComponent(city)}`),
    ]);

    // Pogoda
    if (weatherResp.status === 'fulfilled' && weatherResp.value.ok) {
      const wData = await weatherResp.value.json();
      renderWeather(wData);
      renderForecast(wData.forecast);
      renderChart(wData.chart_temps);
    } else {
      showError('Nie udało się pobrać danych pogodowych.');
    }

    // AQI
    if (aqiResp.status === 'fulfilled' && aqiResp.value.ok) {
      const aData = await aqiResp.value.json();
      renderAqi(aData);
    } else {
      console.warn('Brak danych AQI');
    }

  } catch (err) {
    console.warn('Błąd:', err.message);
  } finally {
    hideSkeleton();
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  const select = document.getElementById('city-select');

  loadData(select.value);

  select.addEventListener('change', () => loadData(select.value));

  // Auto-odświeżanie co 30 minut
  setInterval(() => loadData(select.value), 30 * 60 * 1000);
});
