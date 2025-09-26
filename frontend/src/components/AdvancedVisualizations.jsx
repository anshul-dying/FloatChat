import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';

const AdvancedVisualizations = ({ location, profession }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        if (location && location.length === 2) {
            fetchFloatData();
        }
    }, [location]);

    const fetchFloatData = async () => {
        setLoading(true);
        setError(null);

        try {
            // Simulate API call - replace with actual endpoint
            const response = await fetch('/api/nearest_floats', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    lat: location[0],
                    lon: location[1],
                    limit: 3
                })
            });

            if (!response.ok) {
                throw new Error('Failed to fetch float data');
            }

            const result = await response.json();
            setData(result);
        } catch (err) {
            console.error('Error fetching float data:', err);
            setError(err.message);
            // Fallback to sample data
            setData({
                floats: [
                    {
                        id: '1900022',
                        lat: location[0] + (Math.random() - 0.5) * 0.1,
                        lon: location[1] + (Math.random() - 0.5) * 0.1,
                        temp: 28.5 + (Math.random() - 0.5) * 2,
                        salinity: 35.2 + (Math.random() - 0.5) * 0.5,
                        pressure: [0, 10, 20, 50, 100, 200, 500],
                        temp_profile: [28.5, 28.2, 27.8, 26.5, 24.2, 20.1, 15.3],
                        sal_profile: [35.2, 35.1, 35.0, 34.8, 34.5, 34.2, 33.9]
                    },
                    {
                        id: '1900033',
                        lat: location[0] + (Math.random() - 0.5) * 0.1,
                        lon: location[1] + (Math.random() - 0.5) * 0.1,
                        temp: 27.8 + (Math.random() - 0.5) * 2,
                        salinity: 34.9 + (Math.random() - 0.5) * 0.5,
                        pressure: [0, 10, 20, 50, 100, 200, 500],
                        temp_profile: [27.8, 27.5, 27.1, 25.8, 23.5, 19.4, 14.6],
                        sal_profile: [34.9, 34.8, 34.7, 34.5, 34.2, 33.9, 33.6]
                    },
                    {
                        id: '1900034',
                        lat: location[0] + (Math.random() - 0.5) * 0.1,
                        lon: location[1] + (Math.random() - 0.5) * 0.1,
                        temp: 29.1 + (Math.random() - 0.5) * 2,
                        salinity: 35.5 + (Math.random() - 0.5) * 0.5,
                        pressure: [0, 10, 20, 50, 100, 200, 500],
                        temp_profile: [29.1, 28.8, 28.4, 27.1, 24.8, 20.7, 15.9],
                        sal_profile: [35.5, 35.4, 35.3, 35.1, 34.8, 34.5, 34.2]
                    }
                ]
            });
        } finally {
            setLoading(false);
        }
    };

    const renderOverview = () => {
        if (!data?.floats) return <div>No data available</div>;

        return (
            <div className="overview-section">
                <h4>📍 Nearest ARGO Floats</h4>
                <div className="float-cards">
                    {data.floats.map((float, i) => (
                        <div key={i} className="float-card">
                            <div className="float-header">
                                <h5>Float {float.id}</h5>
                                <span className="distance">~{Math.round(Math.random() * 50 + 10)} km</span>
                            </div>
                            <div className="float-data">
                                <div className="data-row">
                                    <span>📍 Location:</span>
                                    <span>{float.lat.toFixed(3)}°, {float.lon.toFixed(3)}°</span>
                                </div>
                                <div className="data-row">
                                    <span>🌡️ Surface Temp:</span>
                                    <span>{float.temp.toFixed(1)}°C</span>
                                </div>
                                <div className="data-row">
                                    <span>🧂 Surface Salinity:</span>
                                    <span>{float.salinity.toFixed(2)} PSU</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    const renderProfiles = () => {
        if (!data?.floats) return <div>No data available</div>;

        const traces = [];
        data.floats.forEach((float, i) => {
            // Temperature profile
            traces.push({
                x: float.temp_profile,
                y: float.pressure,
                type: 'scatter',
                mode: 'lines+markers',
                name: `Float ${float.id} - Temp`,
                line: { color: `hsl(${i * 120}, 70%, 50%)` },
                yaxis: 'y'
            });

            // Salinity profile
            traces.push({
                x: float.sal_profile,
                y: float.pressure,
                type: 'scatter',
                mode: 'lines+markers',
                name: `Float ${float.id} - Salinity`,
                line: { color: `hsl(${i * 120}, 70%, 50%)`, dash: 'dash' },
                yaxis: 'y2'
            });
        });

        return (
            <div className="profiles-section">
                <h4>📈 Temperature & Salinity Profiles</h4>
                <Plot
                    data={traces}
                    layout={{
                        title: 'Oceanographic Profiles Comparison',
                        xaxis: { title: 'Temperature (°C) / Salinity (PSU)' },
                        yaxis: {
                            title: 'Pressure (dbar)',
                            autorange: 'reversed',
                            side: 'left'
                        },
                        yaxis2: {
                            title: 'Pressure (dbar)',
                            autorange: 'reversed',
                            side: 'right',
                            overlaying: 'y'
                        },
                        height: 500,
                        showlegend: true,
                        legend: { x: 1.02, y: 1 }
                    }}
                    style={{ width: '100%', height: '100%' }}
                />
            </div>
        );
    };

    const renderComparison = () => {
        if (!data?.floats) return <div>No data available</div>;

        const comparisonData = data.floats.map(float => ({
            'Float ID': float.id,
            'Latitude': float.lat.toFixed(3),
            'Longitude': float.lon.toFixed(3),
            'Surface Temp (°C)': float.temp.toFixed(1),
            'Surface Salinity (PSU)': float.salinity.toFixed(2),
            'Max Depth (m)': Math.max(...float.pressure).toFixed(0)
        }));

        return (
            <div className="comparison-section">
                <h4>🔬 Comparative Analysis</h4>
                <div className="comparison-table">
                    <table>
                        <thead>
                            <tr>
                                {Object.keys(comparisonData[0]).map(key => (
                                    <th key={key}>{key}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {comparisonData.map((row, i) => (
                                <tr key={i}>
                                    {Object.values(row).map((value, j) => (
                                        <td key={j}>{value}</td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="insights">
                    <h5>🧠 AI Insights for {profession}</h5>
                    <div className="insight-content">
                        {profession === 'Researcher' && (
                            <p>Temperature variations suggest seasonal mixing patterns. Salinity gradients indicate freshwater influence from nearby sources.</p>
                        )}
                        {profession === 'Fisherman' && (
                            <p>Surface temperatures are optimal for fishing. Salinity levels indicate good water quality for marine life.</p>
                        )}
                        {profession === 'Policymaker' && (
                            <p>Data shows stable oceanographic conditions. Monitoring trends suggest healthy marine ecosystem status.</p>
                        )}
                        {profession === 'Student' && (
                            <p>These profiles demonstrate typical tropical ocean characteristics with warm surface waters and decreasing temperature with depth.</p>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    const renderMap = () => {
        if (!data?.floats) return <div>No data available</div>;

        const mapData = [
            {
                type: 'scattermapbox',
                mode: 'markers',
                marker: { size: 15, color: 'red' },
                text: data.floats.map(f => `Float ${f.id}`),
                lat: data.floats.map(f => f.lat),
                lon: data.floats.map(f => f.lon),
                name: 'ARGO Floats'
            },
            {
                type: 'scattermapbox',
                mode: 'markers',
                marker: { size: 20, color: 'blue', symbol: 'star' },
                text: ['Selected Location'],
                lat: [location[0]],
                lon: [location[1]],
                name: 'Selected Location'
            }
        ];

        return (
            <div className="map-section">
                <h4>🗺️ Float Locations</h4>
                <Plot
                    data={mapData}
                    layout={{
                        mapbox: {
                            style: 'open-street-map',
                            center: { lat: location[0], lon: location[1] },
                            zoom: 8
                        },
                        height: 500,
                        margin: { t: 0, b: 0, l: 0, r: 0 }
                    }}
                    style={{ width: '100%', height: '100%' }}
                />
            </div>
        );
    };

    if (loading) {
        return (
            <div className="loading-state">
                <div className="spinner"></div>
                <p>Loading ARGO float data...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="error-state">
                <p>⚠️ {error}</p>
                <button onClick={fetchFloatData}>Retry</button>
            </div>
        );
    }

    return (
        <div className="advanced-visualizations">
            <div className="viz-tabs">
                <button
                    className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
                    onClick={() => setActiveTab('overview')}
                >
                    📊 Overview
                </button>
                <button
                    className={`tab ${activeTab === 'profiles' ? 'active' : ''}`}
                    onClick={() => setActiveTab('profiles')}
                >
                    📈 Profiles
                </button>
                <button
                    className={`tab ${activeTab === 'comparison' ? 'active' : ''}`}
                    onClick={() => setActiveTab('comparison')}
                >
                    🔬 Comparison
                </button>
                <button
                    className={`tab ${activeTab === 'map' ? 'active' : ''}`}
                    onClick={() => setActiveTab('map')}
                >
                    🗺️ Map
                </button>
            </div>

            <div className="viz-content">
                {activeTab === 'overview' && renderOverview()}
                {activeTab === 'profiles' && renderProfiles()}
                {activeTab === 'comparison' && renderComparison()}
                {activeTab === 'map' && renderMap()}
            </div>
        </div>
    );
};

export default AdvancedVisualizations;
