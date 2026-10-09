import { useState, useEffect } from 'react';

const API = 'http://127.0.0.1:8000';

const RANGES = [
  { label: '7d', value: 7 },
  { label: '30d', value: 30 },
  { label: '90d', value: 90 },
  { label: '365d', value: 365 },
];

const METRICS = [
  { key: 'records', label: 'Log entries' },
  { key: 'vehicles', label: 'Total vehicles' },
  { key: 'cars', label: 'Cars' },
  { key: 'ambulance_records', label: 'Ambulances' },
];

function TrafficTrends() {
  const [days, setDays] = useState(90);
  const [metric, setMetric] = useState('records');
  const [series, setSeries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(`${API}/stats/trends?days=${days}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (cancelled) return;
        setSeries(data.data || []);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message);
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [days]);

  const valueOf = (row) => {
    if (metric === 'vehicles') {
      return (row.cars || 0) + (row.bikes || 0) + (row.buses || 0) + (row.trucks || 0);
    }
    return row[metric] || 0;
  };

  const points = series.map((row) => ({
    date: row.date,
    time: new Date(`${row.date}T00:00:00Z`).getTime(),
    value: valueOf(row),
  }));

  const W = 720;
  const H = 260;
  const PAD = { top: 20, right: 24, bottom: 38, left: 52 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;

  const minTime = points.length ? Math.min(...points.map((p) => p.time)) : 0;
  const maxTime = points.length ? Math.max(...points.map((p) => p.time)) : 1;
  const span = Math.max(1, maxTime - minTime);
  const maxValue = points.length ? Math.max(...points.map((p) => p.value)) : 0;
  const niceMax = Math.max(1, maxValue);

  const xFor = (t) => PAD.left + ((t - minTime) / span) * plotW;
  const yFor = (v) => PAD.top + plotH - (v / niceMax) * plotH;

  const polyline = points
    .map((p) => `${xFor(p.time).toFixed(1)},${yFor(p.value).toFixed(1)}`)
    .join(' ');

  const yTicks = [0, 0.5, 1].map((f) => ({
    y: PAD.top + plotH - f * plotH,
    label: Math.round(f * niceMax),
  }));

  const xTicks = (() => {
    if (!points.length) return [];
    const picked =
      points.length >= 3
        ? [points[0], points[Math.floor(points.length / 2)], points[points.length - 1]]
        : points;
    const seen = new Set();
    return picked.filter((p) => {
      if (seen.has(p.date)) return false;
      seen.add(p.date);
      return true;
    });
  })();

  const metricLabel = METRICS.find((m) => m.key === metric)?.label || '';
  const windowTotal = points.reduce((sum, p) => sum + p.value, 0);
  const peak = points.length
    ? points.reduce((max, p) => (p.value > max.value ? p : max))
    : null;

  return (
    <section className="stats-section">
      <h2 className="section-title">Traffic Trends</h2>

      <div className="trend-controls">
        <div className="control-group">
          <span className="control-label">Metric</span>
          {METRICS.map((m) => (
            <button
              key={m.key}
              type="button"
              className={`pill ${metric === m.key ? 'pill-active' : ''}`}
              onClick={() => setMetric(m.key)}
            >
              {m.label}
            </button>
          ))}
        </div>
        <div className="control-group">
          <span className="control-label">Range</span>
          {RANGES.map((r) => (
            <button
              key={r.value}
              type="button"
              className={`pill ${days === r.value ? 'pill-active' : ''}`}
              onClick={() => setDays(r.value)}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {loading && <p className="status-message">Loading trend data...</p>}
      {error && <p className="status-message error">Error loading trends: {error}</p>}

      {!loading && !error && points.length === 0 && (
        <p className="status-message">
          No records in this range. Try a wider range.
        </p>
      )}

      {!loading && !error && points.length > 0 && (
        <div className="chart-card wide">
          <div className="trend-meta">
            <span>
              <strong>{metricLabel}</strong> across {points.length} recorded day
              {points.length === 1 ? '' : 's'}
            </span>
            <span>
              Window total: <strong>{windowTotal.toLocaleString()}</strong>
              {peak ? ` | Peak: ${peak.date} (${peak.value.toLocaleString()})` : ''}
            </span>
          </div>

          <svg
            className="trend-svg"
            viewBox={`0 0 ${W} ${H}`}
            role="img"
            aria-label={`${metricLabel} trend over the last ${days} days`}
          >
            {yTicks.map((t) => (
              <g key={t.y}>
                <line
                  x1={PAD.left}
                  x2={W - PAD.right}
                  y1={t.y}
                  y2={t.y}
                  stroke="#262e42"
                  strokeWidth="1"
                />
                <text x={PAD.left - 10} y={t.y + 4} textAnchor="end" className="axis-text">
                  {t.label}
                </text>
              </g>
            ))}

            <polyline points={polyline} fill="none" stroke="#4a9eff" strokeWidth="2.5" />

            {points.map((p) => (
              <circle
                key={p.date}
                cx={xFor(p.time)}
                cy={yFor(p.value)}
                r="4"
                fill="#4a9eff"
                stroke="#0f1420"
                strokeWidth="1.5"
              />
            ))}

            {xTicks.map((p) => (
              <text
                key={p.date}
                x={xFor(p.time)}
                y={H - 12}
                textAnchor="middle"
                className="axis-text"
              >
                {p.date.slice(5)}
              </text>
            ))}
          </svg>

          <p className="chart-caption">
            Only dates with recorded data are plotted. Gaps mean no data was collected that day,
            not zero traffic.
          </p>
        </div>
      )}
    </section>
  );
}

export default TrafficTrends;