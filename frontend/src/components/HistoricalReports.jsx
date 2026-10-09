import { useState, useEffect, useMemo } from 'react';

const API = 'http://127.0.0.1:8000';

const RANGES = [7, 30, 90, 365];

function HistoricalReports() {
  const [days, setDays] = useState(90);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });

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
        setRows(data.data || []);
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

  const enriched = useMemo(
    () =>
      rows.map((r) => ({
        ...r,
        vehicles: (r.cars || 0) + (r.bikes || 0) + (r.buses || 0) + (r.trucks || 0),
      })),
    [rows]
  );

  const sorted = useMemo(() => {
    const copy = [...enriched];
    copy.sort((a, b) => {
      const av = a[sortConfig.key];
      const bv = b[sortConfig.key];
      if (av == null) return 1;
      if (bv == null) return -1;
      if (av < bv) return sortConfig.direction === 'asc' ? -1 : 1;
      if (av > bv) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
    return copy;
  }, [enriched, sortConfig]);

  const totals = useMemo(
    () =>
      enriched.reduce(
        (acc, r) => ({
          records: acc.records + (r.records || 0),
          cars: acc.cars + (r.cars || 0),
          bikes: acc.bikes + (r.bikes || 0),
          buses: acc.buses + (r.buses || 0),
          trucks: acc.trucks + (r.trucks || 0),
          vehicles: acc.vehicles + (r.vehicles || 0),
          ambulance_records: acc.ambulance_records + (r.ambulance_records || 0),
        }),
        {
          records: 0,
          cars: 0,
          bikes: 0,
          buses: 0,
          trucks: 0,
          vehicles: 0,
          ambulance_records: 0,
        }
      ),
    [enriched]
  );

  const handleSort = (key) => {
    setSortConfig((prev) =>
      prev.key === key
        ? { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
        : { key, direction: 'desc' }
    );
  };

  const sortArrow = (key) =>
    sortConfig.key === key ? (sortConfig.direction === 'asc' ? ' \u25B2' : ' \u25BC') : '';

  const exportCsv = () => {
    const headers = [
      'Date',
      'Log entries',
      'Cars',
      'Bikes',
      'Buses',
      'Trucks',
      'Total vehicles',
      'Ambulance entries',
    ];
    const lines = sorted.map((r) =>
      [r.date, r.records, r.cars, r.bikes, r.buses, r.trucks, r.vehicles, r.ambulance_records].join(',')
    );
    lines.push(
      [
        'TOTAL',
        totals.records,
        totals.cars,
        totals.bikes,
        totals.buses,
        totals.trucks,
        totals.vehicles,
        totals.ambulance_records,
      ].join(',')
    );

    const blob = new Blob([[headers.join(','), ...lines].join('\n')], {
      type: 'text/csv;charset=utf-8;',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `smartflow-history-${days}d.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="stats-section">
      <div className="reports-header">
        <h2 className="section-title">Historical Reports</h2>
        <div className="control-group">
          <span className="control-label">Range</span>
          {RANGES.map((r) => (
            <button
              key={r}
              type="button"
              className={`pill ${days === r ? 'pill-active' : ''}`}
              onClick={() => setDays(r)}
            >
              {r}d
            </button>
          ))}
          <button
            type="button"
            className="pill export-btn"
            onClick={exportCsv}
            disabled={sorted.length === 0}
          >
            Export CSV
          </button>
        </div>
      </div>

      {loading && <p className="status-message">Loading report data...</p>}
      {error && <p className="status-message error">Error loading report: {error}</p>}

      {!loading && !error && sorted.length === 0 && (
        <p className="status-message">No records in this range. Try a wider range.</p>
      )}

      {!loading && !error && sorted.length > 0 && (
        <table className="traffic-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('date')}>Date{sortArrow('date')}</th>
              <th onClick={() => handleSort('records')}>Log entries{sortArrow('records')}</th>
              <th onClick={() => handleSort('cars')}>Cars{sortArrow('cars')}</th>
              <th onClick={() => handleSort('bikes')}>Bikes{sortArrow('bikes')}</th>
              <th onClick={() => handleSort('buses')}>Buses{sortArrow('buses')}</th>
              <th onClick={() => handleSort('trucks')}>Trucks{sortArrow('trucks')}</th>
              <th onClick={() => handleSort('vehicles')}>Total vehicles{sortArrow('vehicles')}</th>
              <th onClick={() => handleSort('ambulance_records')}>
                Ambulances{sortArrow('ambulance_records')}
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => (
              <tr key={r.date} className={r.ambulance_records > 0 ? 'ambulance-row' : ''}>
                <td>{r.date}</td>
                <td>{r.records}</td>
                <td>{r.cars}</td>
                <td>{r.bikes}</td>
                <td>{r.buses}</td>
                <td>{r.trucks}</td>
                <td>{r.vehicles.toLocaleString()}</td>
                <td>{r.ambulance_records}</td>
              </tr>
            ))}
            <tr className="totals-row">
              <td>Total</td>
              <td>{totals.records}</td>
              <td>{totals.cars.toLocaleString()}</td>
              <td>{totals.bikes}</td>
              <td>{totals.buses}</td>
              <td>{totals.trucks}</td>
              <td>{totals.vehicles.toLocaleString()}</td>
              <td>{totals.ambulance_records}</td>
            </tr>
          </tbody>
        </table>
      )}
    </section>
  );
}

export default HistoricalReports;