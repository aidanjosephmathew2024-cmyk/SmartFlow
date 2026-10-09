import { useState, useEffect } from 'react';

const API = 'http://127.0.0.1:8000';

const CONGESTION_COLORS = {
  Low: '#4caf50',
  Medium: '#ffc107',
  High: '#f44336',
};

function StatsSummary() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API}/stats/summary`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setSummary(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <p className="status-message">Loading statistics...</p>;
  if (error) return <p className="status-message error">Error loading statistics: {error}</p>;
  if (!summary) return null;

  const byRoad = summary.by_road || [];
  const congestion = summary.congestion || [];
  const vehicleTotals = summary.vehicle_totals || {};
  const dateRange = summary.date_range || {};

  const roadTotals = byRoad.map((r) => ({
    road: r.road,
    total: (r.cars || 0) + (r.bikes || 0) + (r.buses || 0) + (r.trucks || 0),
  }));

  const maxRoadTotal = Math.max(1, ...roadTotals.map((r) => r.total));
  const congestionTotal = congestion.reduce((sum, c) => sum + c.records, 0) || 1;

  const shortDate = (iso) => (iso ? iso.slice(0, 10) : 'n/a');

  return (
    <section className="stats-section">
      <h2 className="section-title">Historical Traffic Statistics</h2>

      <div className="stat-strip">
        <div className="stat-chip">
          <span className="stat-chip-label">Records analysed</span>
          <span className="stat-chip-value">{summary.records_analyzed}</span>
        </div>
        <div className="stat-chip">
          <span className="stat-chip-label">Date range</span>
          <span className="stat-chip-value small">
            {shortDate(dateRange.from)} to {shortDate(dateRange.to)}
          </span>
        </div>
        <div className="stat-chip">
          <span className="stat-chip-label">Ambulance log entries</span>
          <span className="stat-chip-value">{summary.ambulance_records}</span>
        </div>
        <div className="stat-chip">
          <span className="stat-chip-label">Avg. green time</span>
          <span className="stat-chip-value">
            {summary.average_green_time != null
              ? `${summary.average_green_time.toFixed(1)}s`
              : 'n/a'}
          </span>
        </div>
      </div>

      <div className="chart-row">
        <div className="chart-card">
          <h3 className="chart-title">Total vehicles detected per road</h3>
          <div className="bar-chart">
            {roadTotals.map((r) => (
              <div className="bar-column" key={r.road}>
                <div className="bar-value">{r.total.toLocaleString()}</div>
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{ height: `${(r.total / maxRoadTotal) * 100}%` }}
                  />
                </div>
                <div className="bar-label">{r.road}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-card">
          <h3 className="chart-title">Congestion level distribution</h3>
          <div className="congestion-list">
            {congestion.map((c) => {
              const pct = (c.records / congestionTotal) * 100;
              return (
                <div className="congestion-row" key={c.level}>
                  <div className="congestion-head">
                    <span>{c.level}</span>
                    <span className="congestion-count">
                      {c.records} ({pct.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="congestion-track">
                    <div
                      className="congestion-fill"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: CONGESTION_COLORS[c.level] || '#8a93a6',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="chart-card wide">
        <h3 className="chart-title">Vehicle type totals (all roads)</h3>
        <div className="vehicle-type-grid">
          {[
            ['Cars', vehicleTotals.cars],
            ['Bikes', vehicleTotals.bikes],
            ['Buses', vehicleTotals.buses],
            ['Trucks', vehicleTotals.trucks],
          ].map(([label, value]) => (
            <div className="vehicle-type-card" key={label}>
              <div className="vehicle-type-label">{label}</div>
              <div className="vehicle-type-value">{(value || 0).toLocaleString()}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default StatsSummary;