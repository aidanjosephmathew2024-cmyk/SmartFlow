import { useState, useEffect, useMemo } from 'react';
import './App.css';

function App() {
  const [trafficData, setTrafficData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [roadFilter, setRoadFilter] = useState('All');
  const [sortConfig, setSortConfig] = useState({ key: 'timestamp', direction: 'desc' });
  const [cameraStatus, setCameraStatus] = useState(null);

  const fetchCameraStatus = () => {
    fetch('http://127.0.0.1:8000/camera-status')
      .then((res) => res.json())
      .then((data) => setCameraStatus(data))
      .catch(() => setCameraStatus(null));
  };

  const fetchTraffic = () => {
    fetch('http://127.0.0.1:8000/traffic')
      .then((response) => response.json())
      .then((data) => {
        setTrafficData(data);
        setLoading(false);
        setLastUpdated(new Date().toLocaleTimeString());
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchTraffic();
    fetchCameraStatus();
    const interval = setInterval(() => {
      fetchTraffic();
      fetchCameraStatus();
    }, 3000); // poll every 3s to match rotation timing
    return () => clearInterval(interval);
  }, []);

  const congestionColor = (level) => {
    switch (level) {
      case 'Low':
        return { backgroundColor: '#d4edda', color: '#155724' };
      case 'Medium':
        return { backgroundColor: '#fff3cd', color: '#856404' };
      case 'High':
        return { backgroundColor: '#f8d7da', color: '#721c24' };
      default:
        return { backgroundColor: '#e2e3e5', color: '#383d41' };
    }
  };

  const handleSort = (key) => {
    setSortConfig((prev) => {
      if (prev.key === key) {
        return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' };
      }
      return { key, direction: 'desc' };
    });
  };

  const displayedData = useMemo(() => {
    let rows = [...trafficData];

    if (roadFilter !== 'All') {
      rows = rows.filter((r) => r.road === roadFilter);
    }

    rows.sort((a, b) => {
      const valA = a[sortConfig.key];
      const valB = b[sortConfig.key];
      if (valA == null) return 1;
      if (valB == null) return -1;
      if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
      if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return rows;
  }, [trafficData, roadFilter, sortConfig]);

  if (loading) return <p className="status-message">Loading traffic data...</p>;
  if (error) return <p className="status-message error">Error fetching data: {error}</p>;

  const activeEmergency = trafficData.find((road) => road.ambulance);

  const roadsWithScore = trafficData.filter((r) => r.priority_score != null);
  const priorityRoad = roadsWithScore.length
    ? roadsWithScore.reduce((max, r) => (r.priority_score > max.priority_score ? r : max))
    : null;
  const avgGreenTime = roadsWithScore.length
    ? (roadsWithScore.reduce((sum, r) => sum + (r.green_time || 0), 0) / roadsWithScore.length).toFixed(1)
    : '—';
  const highCongestionCount = trafficData.filter((r) => r.congestion === 'High').length;
  const totalScans = trafficData.length;

  const sortArrow = (key) =>
    sortConfig.key === key ? (sortConfig.direction === 'asc' ? ' ▲' : ' ▼') : '';

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        {cameraStatus && cameraStatus.current_road && (
          <div className="camera-status">
            📷 Camera currently scanning: <strong>{cameraStatus.current_road}</strong>
          </div>
        )}
        <h1>SmartFlow Traffic Dashboard</h1>
        {lastUpdated && <span className="last-updated">Last updated: {lastUpdated}</span>}
      </div>

      {activeEmergency && (
        <div className="emergency-banner">
          🚨 EMERGENCY OVERRIDE ACTIVE — Ambulance detected on {activeEmergency.road} road. Signal priority given.
        </div>
      )}

      <div className="summary-cards">
        <div className="card">
          <div className="card-label">Current Priority Road</div>
          <div className="card-value">{priorityRoad ? priorityRoad.road : '—'}</div>
        </div>
        <div className="card">
          <div className="card-label">Avg. Green Time</div>
          <div className="card-value">
            {avgGreenTime}
            {avgGreenTime !== '—' ? 's' : ''}
          </div>
        </div>
        <div className="card">
          <div className="card-label">High Congestion Roads</div>
          <div className="card-value">{highCongestionCount}</div>
        </div>
        <div className="card">
          <div className="card-label">Total Scans Logged</div>
          <div className="card-value">{totalScans}</div>
        </div>
      </div>

      <div className="controls">
        <label htmlFor="roadFilter">Filter by road: </label>
        <select
          id="roadFilter"
          value={roadFilter}
          onChange={(e) => setRoadFilter(e.target.value)}
        >
          <option value="All">All</option>
          <option value="North">North</option>
          <option value="East">East</option>
          <option value="South">South</option>
          <option value="West">West</option>
        </select>
      </div>

      <table className="traffic-table">
        <thead>
          <tr>
            <th onClick={() => handleSort('road')}>Road{sortArrow('road')}</th>
            <th onClick={() => handleSort('cars')}>Cars{sortArrow('cars')}</th>
            <th onClick={() => handleSort('bikes')}>Bikes{sortArrow('bikes')}</th>
            <th onClick={() => handleSort('bus')}>Bus{sortArrow('bus')}</th>
            <th onClick={() => handleSort('truck')}>Truck{sortArrow('truck')}</th>
            <th>Ambulance</th>
            <th onClick={() => handleSort('congestion')}>Congestion{sortArrow('congestion')}</th>
            <th onClick={() => handleSort('priority_score')}>Priority Score{sortArrow('priority_score')}</th>
            <th onClick={() => handleSort('green_time')}>Green Time (s){sortArrow('green_time')}</th>
          </tr>
        </thead>
        <tbody>
          {displayedData.map((road, index) => (
            <tr key={index} className={road.ambulance ? 'ambulance-row' : ''}>
              <td>{road.road}</td>
              <td>{road.cars}</td>
              <td>{road.bikes}</td>
              <td>{road.bus}</td>
              <td>{road.truck}</td>
              <td>{road.ambulance ? '🚨 Yes' : 'No'}</td>
              <td>
                <span className="badge" style={congestionColor(road.congestion)}>
                  {road.congestion}
                </span>
              </td>
              <td>{road.priority_score ?? '—'}</td>
              <td>{road.green_time ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {displayedData.length === 0 && (
        <p className="status-message">No records match this filter.</p>
      )}
    </div>
  );
}

export default App;