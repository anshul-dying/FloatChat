import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';

const DashboardPage = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get('http://localhost:8000/dashboard-data');
                setData(response.data);
                setLoading(false);
            } catch (err) {
                setError(err);
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>Error: {error.message}</div>;
    }

    const { profile_data, metadata } = data;

    return (
        <div className="dashboard-page">
            <h1>ARGO Data Dashboard</h1>
            <div className="charts">
                <Plot
                    data={[
                        {
                            type: 'scattermapbox',
                            lat: metadata.map(d => d.LATITUDE_min),
                            lon: metadata.map(d => d.LONGITUDE_min),
                            mode: 'markers',
                            marker: {
                                size: 5,
                                color: 'red'
                            },
                            text: metadata.map(d => d.PLATFORM_NUMBER),
                        },
                    ]}
                    layout={{
                        mapbox: {
                            style: 'open-street-map',
                            center: { lat: 0, lon: 80 },
                            zoom: 2,
                        },
                        title: 'ARGO Float Locations',
                    }}
                />
                <Plot
                    data={[
                        {
                            x: profile_data.map(d => d.TIME),
                            y: profile_data.map(d => d.PRES),
                            mode: 'markers',
                            type: 'scatter',
                            marker: {
                                color: profile_data.map(d => d.TEMP),
                                colorscale: 'Viridis',
                                showscale: true
                            }
                        }
                    ]}
                    layout={{
                        title: 'Temperature-Depth-Time Profile',
                        xaxis: { title: 'Time' },
                        yaxis: { title: 'Pressure (dbar)', autorange: 'reversed' }
                    }}
                />
            </div>
        </div>
    );
};

export default DashboardPage;