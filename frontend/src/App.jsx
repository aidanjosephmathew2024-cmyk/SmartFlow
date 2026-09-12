import { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [trafficData, setTrafficData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/traffic')
      .then((response) => response.json())
      .then((data) => {
        setTrafficData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <p>Loading traffic data...</p>;
  if (error) return <p>Error fetching data: {error}</p>;

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>SmartFlow Traffic Dashboard</h1>
      <table border="1" cellPadding="10" style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            <th>Road</th>
            <th>Cars</th>
            <th>Bikes</th>
            <th>Bus</th>
            <th>Truck</th>
            <th>Ambulance</th>
            <th>Congestion</th>
            <th>Priority Score</th>
            <th>Green Time (s)</th>
          </tr>
        </thead>
        <tbody>
          {trafficData.map((road, index) => (
            <tr key={index} style={{ backgroundColor: road.ambulance ? '#ffdddd' : 'white' }}>
              <td>{road.road}</td>
              <td>{road.cars}</td>
              <td>{road.bikes}</td>
              <td>{road.bus}</td>
              <td>{road.truck}</td>
              <td>{road.ambulance ? '🚨 Yes' : 'No'}</td>
              <td>{road.congestion}</td>
              <td>{road.priority_score}</td>
              <td>{road.green_time}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;