import React, { useState, useEffect, useMemo, useRef } from 'react'
import Plot from 'react-plotly.js'
import { X, Download, BarChart3, Map, TrendingUp } from 'lucide-react'

const VisualizationPanel = ({ data, profession = 'Researcher', intent = '', onClose }) => {
    const [activeTab, setActiveTab] = useState('table')

    const hasData = Array.isArray(data) && data.length > 0
    const [filterText, setFilterText] = useState('')
    const [visibleColumns, setVisibleColumns] = useState([])
    const lastPlotRef = useRef(null)

    // Normalize common schema differences so plots work across sources
    const normalizedData = hasData
        ? data.map((row) => {
            const out = { ...row }
            // Temperature
            if (out.TEMP === undefined) {
                out.TEMP = out.temperature_c ?? out.temp ?? out.temperature ?? null
            }
            // Salinity
            if (out.PSAL === undefined) {
                out.PSAL = out.salinity_psu ?? out.psal ?? out.salinity ?? null
            }
            // Pressure
            if (out.PRES === undefined) {
                out.PRES = out.pressure_dbar ?? out.pres ?? out.pressure ?? null
            }
            // Time
            if (out.TIME === undefined) {
                out.TIME = out.juld ?? out.time ?? null
            }
            return out
        })
        : []

    // Initialize visible columns when data changes
    useEffect(() => {
        if (hasData) {
            setVisibleColumns(Object.keys(data[0]))
        } else {
            setVisibleColumns([])
        }
    }, [hasData, data])

    // Convert data to CSV for download
    const convertToCSV = (data) => {
        if (!data || data.length === 0) return ''

        const headers = visibleColumns.length > 0 ? visibleColumns : Object.keys(data[0])
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => `"${row[header] ?? ''}"`).join(','))
        ].join('\n')

        return csvContent
    }

    const downloadCSV = () => {
        const csv = convertToCSV(data)
        const blob = new Blob([csv], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `argo_data_${new Date().toISOString().split('T')[0]}.csv`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
    }

    const copyCSVToClipboard = async () => {
        try {
            const csv = convertToCSV(data)
            await navigator.clipboard.writeText(csv)
            alert('CSV copied to clipboard')
        } catch (e) {
            alert('Failed to copy CSV')
        }
    }

    const exportActiveChartImage = async () => {
        try {
            const Plotly = window.Plotly
            if (lastPlotRef.current && Plotly && Plotly.toImage) {
                const url = await Plotly.toImage(lastPlotRef.current, { format: 'png', width: 1200, height: 800 })
                const a = document.createElement('a')
                a.href = url
                a.download = `chart_${new Date().toISOString().split('T')[0]}.png`
                document.body.appendChild(a)
                a.click()
                document.body.removeChild(a)
            } else {
                alert('Chart export is not available in this environment')
            }
        } catch (e) {
            alert('Failed to export chart image')
        }
    }

    // Create visualizations based on data structure
    const createVisualizations = () => {
        const visualizations = []
        const prof = String(profession || 'Researcher').toLowerCase()

        const hasTemp = normalizedData.some(d => d.TEMP !== undefined && d.PRES !== undefined)
        const hasSal = normalizedData.some(d => d.PSAL !== undefined && d.PRES !== undefined)
        const hasTime = normalizedData.some(d => d.TIME !== undefined)

        // Intent parsing for prioritization
        const q = String(intent || '').toLowerCase()
        const wantsProfile = /(temp.*pres|profile|vs\s*pressure)/.test(q)
        const wantsSurface = /(surface|0-10\s*dbar|shallow)/.test(q)
        const wantsTime = /(trend|time series|over time|monthly|daily)/.test(q)
        const wantsSalinity = /(salinity|psal)/.test(q)
        const wantsTemperature = /(temperature|temp)/.test(q)
        const wantsHistogram = /(histogram|\bhist\b|bar\s*chart)/.test(q)

        // Researcher: detailed scientific plots (TEMP-PRES, PSAL-PRES, time series)
        if (prof === 'researcher') {
            if (hasTemp) {
                const tempData = normalizedData.filter(d => d.TEMP !== null && d.PRES !== null)
                if (tempData.length > 0) {
                    visualizations.push({
                        type: 'scatter',
                        data: [{
                            x: tempData.map(d => d.TEMP),
                            y: tempData.map(d => d.PRES),
                            mode: 'markers',
                            type: 'scatter',
                            name: 'Temperature vs Pressure',
                            marker: {
                                color: tempData.map(d => d.TEMP),
                                colorscale: 'Viridis',
                                size: 8,
                                colorbar: { title: 'Temperature (°C)' }
                            }
                        }],
                        layout: {
                            title: 'Temperature vs Pressure Profile',
                            xaxis: { title: 'Temperature (°C)' },
                            yaxis: { title: 'Pressure (dbar)', autorange: 'reversed' },
                            height: 400
                        }
                    })
                }
            }
            if (hasSal) {
                const salData = normalizedData.filter(d => d.PSAL !== null && d.PRES !== null)
                if (salData.length > 0) {
                    visualizations.push({
                        type: 'scatter',
                        data: [{
                            x: salData.map(d => d.PSAL),
                            y: salData.map(d => d.PRES),
                            mode: 'markers',
                            type: 'scatter',
                            name: 'Salinity vs Pressure',
                            marker: {
                                color: salData.map(d => d.PSAL),
                                colorscale: 'Blues',
                                size: 8,
                                colorbar: { title: 'Salinity (PSU)' }
                            }
                        }],
                        layout: {
                            title: 'Salinity vs Pressure Profile',
                            xaxis: { title: 'Salinity (PSU)' },
                            yaxis: { title: 'Pressure (dbar)', autorange: 'reversed' },
                            height: 400
                        }
                    })
                }
            }
            if (hasTime) {
                const timeData = normalizedData.filter(d => d.TIME !== null)
                if (timeData.length > 0) {
                    visualizations.push({
                        type: 'scatter',
                        data: [{
                            x: timeData.map(d => new Date(d.TIME)),
                            y: timeData.map(d => d.TEMP || 0),
                            mode: 'lines+markers',
                            type: 'scatter',
                            name: 'Temperature Over Time',
                            line: { color: '#3b82f6' }
                        }],
                        layout: {
                            title: 'Temperature Over Time',
                            xaxis: { title: 'Time' },
                            yaxis: { title: 'Temperature (°C)' },
                            height: 400
                        }
                    })
                }
            }
        }

        // Fisherman: surface temp/sal histogram or shallow profile summary
        if (prof === 'fisherman') {
            if (hasTemp) {
                const surface = normalizedData.filter(d => (d.PRES || 0) <= 10 && d.TEMP !== null)
                if (surface.length > 0) {
                    visualizations.push({
                        type: 'histogram',
                        data: [{
                            x: surface.map(d => d.TEMP),
                            type: 'histogram',
                            name: 'Surface Temperature Distribution',
                            marker: { color: '#ef4444' }
                        }],
                        layout: {
                            title: 'Surface Temperature Distribution (0-10 dbar)',
                            xaxis: { title: 'Temperature (°C)' },
                            yaxis: { title: 'Count' },
                            height: 350
                        }
                    })
                }
            }
            if (hasSal) {
                const surfaceS = normalizedData.filter(d => (d.PRES || 0) <= 10 && d.PSAL !== null)
                if (surfaceS.length > 0) {
                    visualizations.push({
                        type: 'histogram',
                        data: [{
                            x: surfaceS.map(d => d.PSAL),
                            type: 'histogram',
                            name: 'Surface Salinity Distribution',
                            marker: { color: '#06b6d4' }
                        }],
                        layout: {
                            title: 'Surface Salinity Distribution (0-10 dbar)',
                            xaxis: { title: 'Salinity (PSU)' },
                            yaxis: { title: 'Count' },
                            height: 350
                        }
                    })
                }
            }
        }

        // Policymaker: summary KPI cards approximated as bar chart
        if (prof === 'policymaker') {
            const numRecords = normalizedData.length
            const avgTemp = normalizedData.reduce((s, d) => s + (d.TEMP || 0), 0) / Math.max(1, normalizedData.filter(d => d.TEMP !== null && d.TEMP !== undefined).length)
            const avgSal = normalizedData.reduce((s, d) => s + (d.PSAL || 0), 0) / Math.max(1, normalizedData.filter(d => d.PSAL !== null && d.PSAL !== undefined).length)
            visualizations.push({
                type: 'bar',
                data: [{
                    x: ['Records', 'Avg Temp', 'Avg Salinity'],
                    y: [numRecords, Number.isFinite(avgTemp) ? avgTemp : 0, Number.isFinite(avgSal) ? avgSal : 0],
                    type: 'bar',
                    marker: { color: ['#6b7280', '#3b82f6', '#10b981'] }
                }],
                layout: {
                    title: 'Summary Indicators',
                    yaxis: { title: 'Value' },
                    height: 350
                }
            })
        }

        // Student: simple combined scatter of TEMP and PSAL vs PRES
        if (prof === 'student') {
            const traces = []
            if (hasTemp) {
                const tempData = normalizedData.filter(d => d.TEMP !== null && d.PRES !== null)
                if (tempData.length > 0) {
                    traces.push({
                        x: tempData.map(d => d.TEMP),
                        y: tempData.map(d => d.PRES),
                        mode: 'markers',
                        type: 'scatter',
                        name: 'Temperature',
                        marker: { color: '#f59e0b' }
                    })
                }
            }
            if (hasSal) {
                const salData = normalizedData.filter(d => d.PSAL !== null && d.PRES !== null)
                if (salData.length > 0) {
                    traces.push({
                        x: salData.map(d => d.PSAL),
                        y: salData.map(d => d.PRES),
                        mode: 'markers',
                        type: 'scatter',
                        name: 'Salinity',
                        marker: { color: '#10b981' }
                    })
                }
            }
            if (traces.length > 0) {
                visualizations.push({
                    type: 'scatter',
                    data: traces,
                    layout: {
                        title: 'Profiles Overview',
                        xaxis: { title: 'Value' },
                        yaxis: { title: 'Pressure (dbar)', autorange: 'reversed' },
                        height: 400
                    }
                })
            }
        }

        // Ensure a histogram exists if explicitly requested, regardless of profession
        if (wantsHistogram) {
            const histVisuals = []
            if (hasTemp) {
                const tempSurface = normalizedData.filter(d => (d.PRES || 0) <= 10 && d.TEMP !== null)
                const tempAll = normalizedData.filter(d => d.TEMP !== null)
                const source = tempSurface.length > 10 ? tempSurface : tempAll
                if (source.length > 0) {
                    histVisuals.push({
                        type: 'histogram',
                        data: [{
                            x: source.map(d => d.TEMP),
                            type: 'histogram',
                            name: 'Temperature',
                            marker: { color: '#ef4444' }
                        }],
                        layout: {
                            title: tempSurface.length > 10 ? 'Surface Temperature Distribution (0-10 dbar)' : 'Temperature Distribution',
                            xaxis: { title: 'Temperature (°C)' },
                            yaxis: { title: 'Count' },
                            height: 350
                        }
                    })
                }
            }
            if (hasSal) {
                const salSurface = normalizedData.filter(d => (d.PRES || 0) <= 10 && d.PSAL !== null)
                const salAll = normalizedData.filter(d => d.PSAL !== null)
                const source = salSurface.length > 10 ? salSurface : salAll
                if (source.length > 0) {
                    histVisuals.push({
                        type: 'histogram',
                        data: [{
                            x: source.map(d => d.PSAL),
                            type: 'histogram',
                            name: 'Salinity',
                            marker: { color: '#06b6d4' }
                        }],
                        layout: {
                            title: salSurface.length > 10 ? 'Surface Salinity Distribution (0-10 dbar)' : 'Salinity Distribution',
                            xaxis: { title: 'Salinity (PSU)' },
                            yaxis: { title: 'Count' },
                            height: 350
                        }
                    })
                }
            }
            // Prepend deduplicated histograms if not already present
            const hasAnyHistogram = visualizations.some(v => v.type === 'histogram' || (v.data && v.data[0]?.type === 'histogram'))
            if (!hasAnyHistogram && histVisuals.length > 0) {
                histVisuals.forEach(h => visualizations.unshift(h))
            }
        }

        // Advanced: Temperature-Salinity (T-S) diagram
        if (hasTemp && hasSal) {
            const tsData = normalizedData.filter(d => d.TEMP !== null && d.PSAL !== null)
            if (tsData.length > 20) {
                visualizations.push({
                    type: 'scatter',
                    data: [{
                        x: tsData.map(d => d.PSAL),
                        y: tsData.map(d => d.TEMP),
                        mode: 'markers',
                        type: 'scatter',
                        name: 'T-S Diagram',
                        marker: { color: '#8b5cf6', size: 6, opacity: 0.6 }
                    }],
                    layout: {
                        title: 'Temperature–Salinity (T–S) Diagram',
                        xaxis: { title: 'Salinity (PSU)' },
                        yaxis: { title: 'Temperature (°C)' },
                        height: 400
                    }
                })
            }
        }

        // Advanced: Time–Depth heatmap (TEMP)
        if (hasTemp && hasTime) {
            const td = normalizedData
                .filter(d => d.TIME !== null && d.PRES !== null && d.TEMP !== null)
                .slice(0, 5000)
            if (td.length > 20) {
                const x = td.map(d => new Date(d.TIME))
                const y = td.map(d => d.PRES)
                const z = td.map(d => d.TEMP)
                visualizations.push({
                    type: 'heatmap',
                    data: [{
                        x,
                        y,
                        z,
                        type: 'histogram2dcontour',
                        colorscale: 'Viridis',
                        contours: { coloring: 'heatmap' },
                        name: 'Time-Depth TEMP'
                    }],
                    layout: {
                        title: 'Time–Depth Heatmap (Temperature)',
                        xaxis: { title: 'Time' },
                        yaxis: { title: 'Pressure (dbar)', autorange: 'reversed' },
                        height: 420
                    }
                })
            }
        }

        // Advanced: Monthly boxplots (TEMP)
        if (hasTemp && hasTime) {
            const byMonth = {}
            normalizedData.forEach(d => {
                if (d.TIME && d.TEMP != null) {
                    const dt = new Date(d.TIME)
                    if (!Number.isNaN(dt.getTime())) {
                        const k = `${dt.getUTCFullYear()}-${String(dt.getUTCMonth() + 1).padStart(2, '0')}`
                        byMonth[k] = byMonth[k] || []
                        byMonth[k].push(Number(d.TEMP))
                    }
                }
            })
            const labels = Object.keys(byMonth).sort()
            if (labels.length >= 2) {
                const traces = labels.map((lab) => ({
                    y: byMonth[lab],
                    type: 'box',
                    name: lab,
                    marker: { color: '#3b82f6' }
                }))
                visualizations.push({
                    type: 'box',
                    data: traces,
                    layout: {
                        title: 'Monthly Temperature Distribution',
                        yaxis: { title: 'Temperature (°C)' },
                        height: 420,
                        showlegend: false
                    }
                })
            }
        }

        return visualizations
    }

    let visualizations = hasData ? createVisualizations() : []

    // KPI calculations
    const kpis = useMemo(() => {
        if (!hasData) return null
        const numRecords = data.length
        const validTemps = normalizedData.map(d => d.TEMP).filter(v => v !== null && v !== undefined && !Number.isNaN(v))
        const validSal = normalizedData.map(d => d.PSAL).filter(v => v !== null && v !== undefined && !Number.isNaN(v))
        const avgTemp = validTemps.length ? (validTemps.reduce((a, b) => a + Number(b), 0) / validTemps.length) : null
        const avgSal = validSal.length ? (validSal.reduce((a, b) => a + Number(b), 0) / validSal.length) : null
        const times = normalizedData.map(d => d.TIME ? new Date(d.TIME).getTime() : null).filter(Boolean)
        const minTime = times.length ? new Date(Math.min(...times)) : null
        const maxTime = times.length ? new Date(Math.max(...times)) : null
        return { numRecords, avgTemp, avgSal, minTime, maxTime }
    }, [hasData, data, normalizedData])

    // Intent-aware ordering/filtering
    if (visualizations.length > 0 && intent) {
        const q = String(intent).toLowerCase()
        const wantsHistogram = /(histogram|\bhist\b|bar\s*chart)/.test(q)
        if (wantsHistogram) {
            // Show only histograms if explicitly requested
            const onlyHists = visualizations.filter(v => v.type === 'histogram' || (v.data && v.data[0]?.type === 'histogram'))
            if (onlyHists.length > 0) {
                visualizations = onlyHists
            }
        }
        const priority = visualizations.map((viz, idx) => {
            const title = (viz.layout && viz.layout.title ? String(viz.layout.title) : '').toLowerCase()
            let score = 0
            if (/pressure/.test(title) || /(temp.*pres|profile)/.test(q)) score += 3
            if (/salinity/.test(title) && /(salinity|psal)/.test(q)) score += 2
            if (/temperature/.test(title) && /(temperature|temp)/.test(q)) score += 2
            if (/time/.test(title) && /(trend|time series|over time|monthly|daily)/.test(q)) score += 3
            if (/surface|distribution/.test(title) && /(surface|0-10\s*dbar)/.test(q)) score += 2
            return { idx, score }
        })

        priority.sort((a, b) => b.score - a.score)
        visualizations = priority.map(p => visualizations[p.idx])
    }

    // If the user asked for a histogram and we have data, auto-focus the first viz tab
    useEffect(() => {
        const q = String(intent || '').toLowerCase()
        const wantsHistogram = /(histogram|\bhist\b|bar\s*chart)/.test(q)
        if (wantsHistogram && hasData) {
            setActiveTab('viz-0')
        }
    }, [intent, hasData])

    return (
        <div className="visualization-panel">
            <div className="visualization-header">
                <h3>📊 Data Visualizations — {profession}</h3>
                <div className="visualization-controls">
                    <button onClick={downloadCSV} className="download-btn"><Download size={16} />Download CSV</button>
                    <button onClick={copyCSVToClipboard} className="download-btn">Copy CSV</button>
                    <button onClick={exportActiveChartImage} className="download-btn">Export Chart Image</button>
                    <button onClick={onClose} className="close-btn"><X size={16} /></button>
                </div>
            </div>

            {hasData && (
                <div className="controls" style={{ marginBottom: '10px', gap: '10px', display: 'flex', flexWrap: 'wrap' }}>
                    <div style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, padding: '8px 10px' }}>
                        <div style={{ fontSize: 12, opacity: 0.9 }}>Records</div>
                        <div style={{ fontWeight: 700 }}>{kpis?.numRecords ?? 0}</div>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, padding: '8px 10px' }}>
                        <div style={{ fontSize: 12, opacity: 0.9 }}>Avg Temp</div>
                        <div style={{ fontWeight: 700 }}>{kpis?.avgTemp != null ? kpis.avgTemp.toFixed(2) + ' °C' : '-'}</div>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, padding: '8px 10px' }}>
                        <div style={{ fontSize: 12, opacity: 0.9 }}>Avg Salinity</div>
                        <div style={{ fontWeight: 700 }}>{kpis?.avgSal != null ? kpis.avgSal.toFixed(2) + ' PSU' : '-'}</div>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, padding: '8px 10px' }}>
                        <div style={{ fontSize: 12, opacity: 0.9 }}>Time Span</div>
                        <div style={{ fontWeight: 700 }}>{kpis?.minTime && kpis?.maxTime ? `${kpis.minTime.toISOString().split('T')[0]} → ${kpis.maxTime.toISOString().split('T')[0]}` : '-'}</div>
                    </div>
                    <input
                        type="text"
                        placeholder="Filter table..."
                        value={filterText}
                        onChange={(e) => setFilterText(e.target.value)}
                        style={{ flex: 1, minWidth: 220, background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', color: 'white', borderRadius: 8, padding: '8px 10px' }}
                    />
                </div>
            )}

            <div className="visualization-tabs">
                <button
                    className={activeTab === 'table' ? 'active' : ''}
                    onClick={() => setActiveTab('table')}
                >
                    <BarChart3 size={16} />
                    Data Table
                </button>
                {visualizations.map((viz, index) => (
                    <button
                        key={index}
                        className={activeTab === `viz-${index}` ? 'active' : ''}
                        onClick={() => setActiveTab(`viz-${index}`)}
                    >
                        <TrendingUp size={16} />
                        Chart {index + 1}
                    </button>
                ))}
            </div>

            <div className="visualization-content">
                {activeTab === 'table' && (
                    <div className="data-table">
                        <div className="table-header">
                            <h4>{hasData ? `Query Results (${data.length} records)` : 'No data yet'}</h4>
                        </div>
                        {hasData ? (
                            <div className="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            {visibleColumns.map(key => (
                                                <th key={key}>{key}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data
                                            .filter(row => {
                                                if (!filterText) return true
                                                const hay = visibleColumns.map(k => String(row[k] ?? '')).join(' ').toLowerCase()
                                                return hay.includes(filterText.toLowerCase())
                                            })
                                            .slice(0, 100)
                                            .map((row, index) => (
                                                <tr key={index}>
                                                    {visibleColumns.map((col, cellIndex) => (
                                                        <td key={cellIndex}>{row[col] !== null && row[col] !== undefined ? String(row[col]) : '-'}</td>
                                                    ))}
                                                </tr>
                                            ))}
                                    </tbody>
                                </table>
                                {data.length > 100 && (
                                    <div className="table-footer">
                                        Showing first 100 of {data.length} records
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="table-container dims" style={{ padding: '16px' }}>
                                No data yet. Use Fetch Insights or run a query to populate charts and table.
                            </div>
                        )}
                    </div>
                )}

                {visualizations.map((viz, index) => (
                    activeTab === `viz-${index}` && (
                        <div key={index} className="plot-container">
                            <Plot
                                data={viz.data}
                                layout={viz.layout}
                                style={{ width: '100%', height: '100%' }}
                                config={{ responsive: true }}
                                onInitialized={(fig, gd) => { lastPlotRef.current = gd }}
                                onUpdate={(fig, gd) => { lastPlotRef.current = gd }}
                            />
                        </div>
                    )
                ))}
            </div>

            {hasData && (
                <div className="controls" style={{ marginTop: 10 }}>
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                        {(Object.keys(data[0]) || []).slice(0, 20).map((col) => (
                            <label key={col} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', padding: '6px 8px', borderRadius: 6 }}>
                                <input
                                    type="checkbox"
                                    checked={visibleColumns.includes(col)}
                                    onChange={(e) => {
                                        setVisibleColumns(prev => e.target.checked ? [...prev, col] : prev.filter(c => c !== col))
                                    }}
                                />
                                <span style={{ fontSize: 12 }}>{col}</span>
                            </label>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

export default VisualizationPanel
