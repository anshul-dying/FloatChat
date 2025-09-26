import React, { useState, useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap, LayerGroup, GeoJSON, CircleMarker } from 'react-leaflet'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import ChatInput from './ChatInput'
import VisualizationPanel from './VisualizationPanel'
import { useApi } from '../hooks/useApi'
import { MapPin, Waves, Database, Download } from 'lucide-react'
import 'leaflet/dist/leaflet.css'
import api from '../utils/api'

const guidanceByProfession = {
    Researcher: {
        placeholder: 'E.g., “Plot TEMP vs PRES for 2902275 near 10N, 75E (last 30 days)”',
        suggestions: [
            'Show TEMP vs PRES profile for last 30 days at my selected location',
            'Compare salinity profiles across two months near the Arabian Sea',
            'List available parameters and their units in this dataset',
            'Find anomalous temperature events in the Bay of Bengal (past 6 months)'
        ]
    },
    Fisherman: {
        placeholder: 'E.g., “What is today’s surface temperature near my location?”',
        suggestions: [
            'What is the surface temperature (0–10 dbar) near my selected point?',
            'Suggest nearby areas with warmer surface water for fishing',
            'Show salinity trend at the surface in the last two weeks',
            'Are there temperature fronts close to my location today?'
        ]
    },
    Policymaker: {
        placeholder: 'E.g., “Summarize ocean temp/salinity indicators for the region”',
        suggestions: [
            'Summarize key indicators (avg TEMP, avg PSAL, record count) for my region',
            'Show monthly trend of average temperature for the last year',
            'Identify hotspots with unusual warming in the Indian Ocean',
            'Provide a brief regional ocean conditions summary for briefing'
        ]
    },
    Student: {
        placeholder: 'E.g., “Explain ARGO profiles and show a simple plot”',
        suggestions: [
            'What is an ARGO profile? Explain simply and show a basic chart',
            'Plot temperature and salinity vs pressure at my location',
            'Show me how to read a profile plot step by step',
            'List 3 interesting facts about ARGO data near India'
        ]
    }
}

const Dashboard = () => {
    const [showMap, setShowMap] = useState(true)
    const [position, setPosition] = useState([51.505, -0.09])
    const [selected, setSelected] = useState(null) // [lat, lng]
    const [profession, setProfession] = useState('Researcher')
    const [messages, setMessages] = useState([]) // {role, content}
    const [showVisualizations, setShowVisualizations] = useState(false)
    const [visualizationData, setVisualizationData] = useState(null)
    const [sqlInput, setSqlInput] = useState('SELECT * FROM p0 LIMIT 200')
    const [sqlEngine, setSqlEngine] = useState('postgres') // 'parquet' | 'postgres'
    const [chatWidth, setChatWidth] = useState(600) // Default chat width in pixels
    const [isResizing, setIsResizing] = useState(false)
    const [selectedCategory, setSelectedCategory] = useState(null)
    const [guideOpen, setGuideOpen] = useState(false)
    const [lastUserQuery, setLastUserQuery] = useState('')
    const [latInput, setLatInput] = useState('')
    const [lngInput, setLngInput] = useState('')
    const [developerMode, setDeveloperMode] = useState(false)
    const [liveTrackerOn, setLiveTrackerOn] = useState(true)
    const [overlaySstOn, setOverlaySstOn] = useState(false)
    const [overlayCycloneOn, setOverlayCycloneOn] = useState(false)
    const [overlayFishingOn, setOverlayFishingOn] = useState(false)
    const [overlayAisOn, setOverlayAisOn] = useState(false)
    const [liveFloats, setLiveFloats] = useState([])
    const [aisTargets, setAisTargets] = useState([])

    const currentGuidance = useMemo(() => guidanceByProfession[profession] || guidanceByProfession['Researcher'], [profession])
    const dynamicExamples = currentGuidance.suggestions

    const guidedCategories = useMemo(() => ({
        'Report an issue': {
            description: 'Report data or app problems',
            options: [
                {
                    label: 'Wrong data or missing values',
                    prompt: 'I found wrong or missing ARGO data near my selected location. Help me verify and describe how to report it properly.'
                },
                {
                    label: 'App bug or error message',
                    prompt: 'I encountered an error while using the app. Help me diagnose and gather details (steps, screenshots, logs) to report.'
                },
                {
                    label: 'Performance problem (slow/timeout)',
                    prompt: 'The app feels slow or times out. Provide steps to check, and summarize possible causes from my recent actions.'
                }
            ]
        },
        'Ask about data': {
            description: 'Query ARGO data by place/time/params',
            options: [
                {
                    label: 'What does this location look like?',
                    prompt: 'Analyze ARGO profiles near my selected coordinates. Summarize temperature and salinity patterns for the last month.'
                },
                {
                    label: 'Find warm areas nearby',
                    prompt: 'Find nearby regions with higher surface temperature within 200km and list top 5 spots.'
                },
                {
                    label: 'Trend over time',
                    prompt: 'Show a time trend of average temperature for my selected area over the last year.'
                }
            ]
        },
        'Create a visualization': {
            description: 'Make a quick chart/table',
            options: [
                { label: 'TEMP vs PRES profile', prompt: 'Create a Temperature vs Pressure profile chart for my selected location (last 30 days).' },
                { label: 'Surface temp histogram', prompt: 'Create a histogram of surface temperature (0–10 dbar) near my selected location.' },
                { label: 'Data table preview', prompt: 'Show a table preview of recent ARGO profiles for my selected area.' }
            ]
        },
        'Learn/explain': {
            description: 'Guided help and explanations',
            options: [
                { label: 'What is an ARGO profile?', prompt: 'Explain what an ARGO profile is in simple terms and show a basic plot.' },
                { label: 'How to read charts', prompt: 'Explain how to read temperature/salinity vs pressure charts step by step.' },
                { label: 'Glossary of terms', prompt: 'Provide a short glossary of oceanographic terms in this app (TEMP, PSAL, PRES, etc.).' }
            ]
        }
    }), [])

    const handleQuickReply = async (text) => {
        if (!text) return
        await handleSendMessage(text)
    }

    const { loading, error, chatQuery, analyzeLocation } = useApi()

    useEffect(() => {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                setPosition([pos.coords.latitude, pos.coords.longitude])
            },
            () => {
                console.log("Could not get user location.")
            }
        )
    }, [])

    // Auto-load sample from Postgres when panel is opened and there is no data yet
    useEffect(() => {
        if (showVisualizations && (!visualizationData || visualizationData.length === 0)) {
            (async () => {
                try {
                    const sampleSql = `SELECT platform_number, juld AS TIME, pressure_dbar AS PRES, temperature_c AS TEMP, salinity_psu AS PSAL, latitude, longitude
FROM argo_data
WHERE (temperature_c IS NOT NULL OR salinity_psu IS NOT NULL)
LIMIT 500`
                    const res = await api.postgresSql(sampleSql, 500)
                    if (res && res.results && res.results.length > 0) {
                        setVisualizationData(res.results)
                        setMessages(prev => [...prev, { role: 'assistant', content: `Loaded ${res.count || res.results.length} rows from Postgres.` }])
                    }
                } catch (e) {
                    setMessages(prev => [...prev, { role: 'assistant', content: `Failed to load sample from Postgres: ${String(e)}` }])
                }
            })()
        }
    }, [showVisualizations])

    // Live Float Tracker (poll latest cycles from Postgres)
    useEffect(() => {
        let timer = null
        let lastCycles = new Map()
        const fetchLatestFloats = async () => {
            try {
                const sql = `SELECT DISTINCT ON (platform_number) platform_number, cycle_number, juld, latitude, longitude\nFROM argo_data\nWHERE latitude IS NOT NULL AND longitude IS NOT NULL\nORDER BY platform_number, juld DESC\nLIMIT 100`
                const res = await api.postgresSql(sql, 100)
                const rows = res.results || []
                rows.forEach(r => {
                    const key = String(r.platform_number)
                    const prev = lastCycles.get(key)
                    if (prev === undefined) {
                        lastCycles.set(key, r.cycle_number)
                    } else if (r.cycle_number !== prev) {
                        lastCycles.set(key, r.cycle_number)
                        setMessages(prevMsgs => ([
                            ...prevMsgs,
                            { role: 'assistant', content: `Live update: Float ${key} reached cycle ${r.cycle_number}.` }
                        ]))
                    }
                })
                setLiveFloats(rows)
            } catch (e) {
                // ignore polling errors in UI
            }
        }
        if (liveTrackerOn) {
            fetchLatestFloats()
            timer = setInterval(fetchLatestFloats, 30000)
        }
        return () => { if (timer) clearInterval(timer) }
    }, [liveTrackerOn])

    // AIS overlay (poll real endpoint if configured)
    useEffect(() => {
        let timer = null
        const endpoint = (import.meta.env.VITE_AIS_URL || '').trim()
        const poll = async () => {
            if (!endpoint) return
            try {
                const res = await fetch(endpoint)
                const json = await res.json()
                const targets = Array.isArray(json) ? json : (json?.targets || [])
                if (Array.isArray(targets)) setAisTargets(targets)
            } catch (_) { }
        }
        if (overlayAisOn) {
            poll()
            timer = setInterval(poll, 15000)
        }
        return () => { if (timer) clearInterval(timer) }
    }, [overlayAisOn])

    function colorForTemp(val) {
        if (val == null || isNaN(val)) return '#999999'
        const t = Math.max(0, Math.min(1, (val - 0) / 30))
        const r = Math.round(255 * t)
        const b = Math.round(255 * (1 - t))
        return `rgb(${r},80,${b})`
    }

    // Cyclone tracks (fetch GeoJSON from env URL)
    const [cycloneData, setCycloneData] = useState(null)
    useEffect(() => {
        const url = (import.meta.env.VITE_CYCLONE_GEOJSON_URL || '').trim()
        let timer = null
        const fetchCyclones = async () => {
            if (!url) return
            try {
                const res = await fetch(url)
                const json = await res.json()
                setCycloneData(json)
            } catch (_) { }
        }
        if (overlayCycloneOn) {
            fetchCyclones()
            timer = setInterval(fetchCyclones, 600000)
        }
        return () => { if (timer) clearInterval(timer) }
    }, [overlayCycloneOn])

    // Fishing zones (fetch GeoJSON from env URL)
    const [fishingData, setFishingData] = useState(null)
    useEffect(() => {
        const url = (import.meta.env.VITE_FISHING_ZONES_GEOJSON_URL || '').trim()
        const fetchZones = async () => {
            if (!url) return
            try {
                const res = await fetch(url)
                const json = await res.json()
                setFishingData(json)
            } catch (_) { }
        }
        if (overlayFishingOn) fetchZones()
    }, [overlayFishingOn])

    async function analyzeAt(lat, lng) {
        try {
            const data = await analyzeLocation(lat, lng, profession.toLowerCase())

            const insights = data.response || 'No insights available.'
            setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: insights },
            ])

            // Show visualizations if we have data
            if (data.query_results && data.query_results.length > 0) {
                setVisualizationData(data.query_results)
                setShowVisualizations(true)
            }
        } catch (e) {
            setMessages((prev) => [...prev, { role: 'assistant', content: 'Failed to analyze location.' }])
        }
    }

    async function askGeneral(text) {
        const [lat, lng] = selected || position

        try {
            const data = await chatQuery(text, profession.toLowerCase(), lat, lng, developerMode)

            setMessages((prev) => [...prev, { role: 'assistant', content: data.response }])

            // Show visualizations if we have data
            if (data.query_results && data.query_results.length > 0) {
                setVisualizationData(data.query_results)
                setShowVisualizations(true)
            }

            // Developer Mode: optionally show and execute SQL
            if (developerMode && data.sql_query) {
                setMessages((prev) => [
                    ...prev,
                    { role: 'assistant', content: `**Generated SQL Query:**\n\`\`\`sql\n${data.sql_query}\n\`\`\`` },
                ])
                try {
                    const res = sqlEngine === 'parquet'
                        ? await api.parquetSql(data.sql_query, ['argo_profiles_long.parquet'], 500)
                        : await api.postgresSql(data.sql_query, 200)
                    setVisualizationData(res.results)
                    setShowVisualizations(true)
                    setMessages(prev => [...prev, { role: 'assistant', content: `SQL returned ${res.count || res.results?.length || 0} rows.` }])
                } catch (e) {
                    setMessages(prev => [...prev, { role: 'assistant', content: `SQL execution error: ${String(e)}` }])
                }
            }

        } catch (e) {
            setMessages((prev) => [...prev, { role: 'assistant', content: `Query request failed: ${String(e)}` }])
        }
    }

    function ClickCapture({ onSelect }) {
        useMapEvents({
            click(e) {
                const { lat, lng } = e.latlng
                onSelect([lat, lng])
            },
        })
        return null
    }

    function RecenterMap({ center }) {
        const map = useMap()
        useEffect(() => {
            if (center && Array.isArray(center) && center.length === 2) {
                map.setView(center)
            }
        }, [center])
        return null
    }

    function AnalyzeVisibleAreaButton({ onAnalyze }) {
        const map = useMap()
        return (
            <button
                className="fetch-button"
                onClick={() => {
                    const b = map.getBounds()
                    const north = b.getNorth()
                    const south = b.getSouth()
                    const east = b.getEast()
                    const west = b.getWest()
                    onAnalyze({ north, south, east, west })
                }}
                style={{ marginLeft: 20 }}
            >
                Analyze Visible Area
            </button>
        )
    }

    function formatCoord(value) {
        return value.toFixed(5)
    }

    const handleSendMessage = async (text) => {
        if (!text.trim()) return
        const [lat, lng] = selected || position

        setMessages((prev) => [...prev, { role: 'user', content: text }])
        setLastUserQuery(text)
        await askGeneral(text)
    }

    // Resize functionality
    const handleMouseDown = (e) => {
        setIsResizing(true)
        e.preventDefault()
    }

    const handleMouseMove = (e) => {
        if (!isResizing) return

        const newWidth = e.clientX
        const minWidth = 400
        const maxWidth = window.innerWidth - 400 // Leave some space for map

        // Use requestAnimationFrame for smoother updates
        requestAnimationFrame(() => {
            if (newWidth >= minWidth && newWidth <= maxWidth) {
                setChatWidth(newWidth)
            }
        })
    }

    const handleMouseUp = () => {
        setIsResizing(false)
    }

    // Add event listeners for resize
    useEffect(() => {
        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove)
            document.addEventListener('mouseup', handleMouseUp)
            document.body.style.cursor = 'col-resize'
            document.body.style.userSelect = 'none'
        } else {
            document.removeEventListener('mousemove', handleMouseMove)
            document.removeEventListener('mouseup', handleMouseUp)
            document.body.style.cursor = ''
            document.body.style.userSelect = ''
        }

        return () => {
            document.removeEventListener('mousemove', handleMouseMove)
            document.removeEventListener('mouseup', handleMouseUp)
            document.body.style.cursor = ''
            document.body.style.userSelect = ''
        }
    }, [isResizing])

    return (
        <div className={`dashboard ${!showMap ? 'map-hidden' : ''} ${isResizing ? 'resizing' : ''}`}>
            <div
                className="chat-container"
                style={{ width: showMap ? `${chatWidth}px` : '100%' }}
            >
                <div className="header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Waves size={32} color="#3b82f6" />
                        <h1>FloatChat</h1>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                            className="map-toggle-button"
                            onClick={() => setDeveloperMode(v => !v)}
                            aria-label={developerMode ? 'Turn off developer mode' : 'Turn on developer mode'}
                            title="Toggle Developer Mode"
                        >
                            {developerMode ? 'Dev: ON' : 'Dev: OFF'}
                        </button>
                        <button
                            className="map-toggle-button"
                            onClick={() => setGuideOpen(v => !v)}
                            aria-label={guideOpen ? 'Close guidance' : 'Open guidance'}
                        >
                            {guideOpen ? 'Close Guide' : 'Guide Me'}
                        </button>
                        <button
                            className="map-toggle-button"
                            onClick={() => setShowMap(!showMap)}
                            aria-label={showMap ? 'Hide map' : 'Show map'}
                        >
                            {showMap ? 'Hide Map' : 'Show Map'}
                        </button>
                        <button
                            className="map-toggle-button"
                            onClick={() => setShowVisualizations(v => !v)}
                            aria-label={showVisualizations ? 'Hide visualizations' : 'Show visualizations'}
                        >
                            {showVisualizations ? 'Hide Visualizations' : 'Show Visualizations'}
                        </button>
                    </div>
                </div>

                <div className="controls">
                    <select value={profession} onChange={(e) => setProfession(e.target.value)}>
                        <option>Researcher</option>
                        <option>Fisherman</option>
                        <option>Policymaker</option>
                        <option>Student</option>
                    </select>
                    <select>
                        <option>--Choose location on map--</option>
                        <option>--Choose location on map--</option>

                    </select>
                    <button
                        className="map-toggle-button"
                        onClick={async () => {
                            try {
                                const sampleSql = `SELECT platform_number, juld AS TIME, pressure_dbar AS PRES, temperature_c AS TEMP, salinity_psu AS PSAL, latitude, longitude
FROM argo_data
WHERE (temperature_c IS NOT NULL OR salinity_psu IS NOT NULL)
LIMIT 500`
                                const res = await api.postgresSql(sampleSql, 500)
                                setVisualizationData(res.results)
                                setShowVisualizations(true)
                                setMessages(prev => [...prev, { role: 'assistant', content: `Loaded ${res.count || res.results?.length || 0} rows from Postgres.` }])
                            } catch (e) {
                                setMessages(prev => [...prev, { role: 'assistant', content: `Failed to load sample from Postgres: ${String(e)}` }])
                            }
                        }}
                    >
                        Load Sample Data
                    </button>
                    <button
                        className="map-toggle-button"
                        onClick={() => {
                            const md = [
                                `# FloatChat Summary — ${new Date().toISOString()}`,
                                '',
                                `Profession: ${profession}`,
                                selected ? `Location: ${formatCoord((selected || position)[0])}, ${formatCoord((selected || position)[1])}` : 'Location: Current position',
                                '',
                                '## Conversation',
                            ]
                            messages.forEach((m) => {
                                const role = m.role === 'user' ? 'User' : 'Assistant'
                                md.push(`- **${role}:** ${m.content}`)
                            })
                            const blob = new Blob([md.join('\n')], { type: 'text/markdown;charset=utf-8' })
                            const url = URL.createObjectURL(blob)
                            const a = document.createElement('a')
                            a.href = url
                            a.download = `floatchat_summary_${Date.now()}.md`
                            document.body.appendChild(a)
                            a.click()
                            document.body.removeChild(a)
                            URL.revokeObjectURL(url)
                        }}
                    >
                        Export Summary (MD)
                    </button>
                </div>

                {/* SQL Runner - visible only in Developer Mode */}
                {developerMode && (
                    <div className="controls" style={{ marginTop: '8px' }}>
                        <select value={sqlEngine} onChange={(e) => setSqlEngine(e.target.value)}>
                            <option value="parquet">Parquet (DuckDB)</option>
                            <option value="postgres">PostgreSQL</option>
                        </select>
                        <input
                            type="text"
                            value={sqlInput}
                            onChange={(e) => setSqlInput(e.target.value)}
                            placeholder="SQL (FOR DEVS) e.g., SELECT COUNT(*) FROM argo_data"
                            style={{ flex: 1 }}
                        />
                        <button
                            className="map-toggle-button"
                            onClick={async () => {
                                try {
                                    const res = sqlEngine === 'parquet'
                                        ? await api.parquetSql(sqlInput, ['argo_profiles_long.parquet'], 500)
                                        : await api.postgresSql(sqlInput, 200)
                                    setVisualizationData(res.results)
                                    setShowVisualizations(true)
                                    setMessages(prev => [...prev, { role: 'assistant', content: `SQL returned ${res.count || res.results?.length || 0} rows.` }])
                                } catch (e) {
                                    setMessages(prev => [...prev, { role: 'assistant', content: `SQL error: ${String(e)}` }])
                                }
                            }}
                        >
                            Run SQL
                        </button>
                    </div>
                )}

                {/* Realtime and overlay toggles */}
                <div className="controls" style={{ marginTop: '8px' }}>
                    <button
                        className="map-toggle-button"
                        onClick={() => setLiveTrackerOn(v => !v)}
                        aria-label={liveTrackerOn ? 'Turn off Live Tracker' : 'Turn on Live Tracker'}
                    >
                        {liveTrackerOn ? 'Live Tracker: ON' : 'Live Tracker: OFF'}
                    </button>
                    <button className="map-toggle-button" onClick={() => setOverlaySstOn(v => !v)}>
                        {overlaySstOn ? 'SST Overlay: ON' : 'SST Overlay: OFF'}
                    </button>
                    <button className="map-toggle-button" onClick={() => setOverlayCycloneOn(v => !v)}>
                        {overlayCycloneOn ? 'Cyclones: ON' : 'Cyclones: OFF'}
                    </button>
                    <button className="map-toggle-button" onClick={() => setOverlayFishingOn(v => !v)}>
                        {overlayFishingOn ? 'Fishing Zones: ON' : 'Fishing Zones: OFF'}
                    </button>
                    <button className="map-toggle-button" onClick={() => setOverlayAisOn(v => !v)}>
                        {overlayAisOn ? 'AIS: ON' : 'AIS: OFF'}
                    </button>
                </div>

                {/* Guided flow panel (WhatsApp-like) when chat is empty) */}
                {(messages.length === 0 || guideOpen) && (
                    <div className="suggestions-panel" style={{
                        background: 'rgba(255,255,255,0.06)',
                        border: '1px solid rgba(255,255,255,0.12)',
                        borderRadius: '12px',
                        padding: '14px',
                        marginBottom: '16px'
                    }}>
                        {!selectedCategory && (
                            <>
                                <div style={{ marginBottom: '8px', opacity: 0.9 }}>
                                    <strong>What do you want to do?</strong>
                                </div>
                                <div className="example-queries">
                                    {Object.keys(guidedCategories).map((cat) => (
                                        <button
                                            key={cat}
                                            className="map-toggle-button"
                                            onClick={() => setSelectedCategory(cat)}
                                            aria-label={`Choose category: ${cat}`}
                                        >
                                            {cat}
                                        </button>
                                    ))}
                                </div>
                                <div style={{ marginTop: '8px', opacity: 0.8, fontSize: '12px' }}>
                                    Or try suggestions for {profession} below
                                </div>
                                <div className="example-queries" style={{ marginTop: '8px' }}>
                                    {dynamicExamples.map((q, index) => (
                                        <button
                                            key={index}
                                            className="map-toggle-button"
                                            onClick={() => handleQuickReply(q)}
                                            aria-label={`Run example: ${q}`}
                                        >
                                            {q}
                                        </button>
                                    ))}
                                </div>
                            </>
                        )}

                        {selectedCategory && (
                            <>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                    <strong>{selectedCategory}</strong>
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <button className="map-toggle-button" onClick={() => setSelectedCategory(null)}>Back</button>
                                        <button className="map-toggle-button" onClick={() => { setSelectedCategory(null); setGuideOpen(false) }}>Close</button>
                                    </div>
                                </div>
                                <div className="example-queries">
                                    {guidedCategories[selectedCategory].options.map((opt, idx) => (
                                        <button
                                            key={idx}
                                            className="map-toggle-button"
                                            onClick={() => handleQuickReply(opt.prompt)}
                                            aria-label={`Quick reply: ${opt.label}`}
                                        >
                                            {opt.label}
                                        </button>
                                    ))}
                                </div>
                            </>
                        )}
                    </div>
                )}

                <div className="messages">
                    {messages.map((m, i) => (
                        <div key={i} className={`message ${m.role}`}>
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                        </div>
                    ))}
                    {loading && (
                        <div className="message assistant loading">
                            <div className="loading">🔍 Processing your query...</div>
                        </div>
                    )}
                    {error && (
                        <div className="message assistant error">
                            <div className="error">❌ API Error: {error}</div>
                        </div>
                    )}
                </div>

                <ChatInput onSend={handleSendMessage} placeholder={currentGuidance.placeholder} />
            </div>

            {showMap && (
                <>
                    <div
                        className="resize-handle"
                        onMouseDown={handleMouseDown}
                    >
                        <div className="resize-handle-line"></div>
                    </div>
                </>
            )}

            {showMap && (
                <div className="map-container">
                    <div className="map-topbar">
                        {selected ? (
                            <div className="coords">
                                <span>Lat:</span> {formatCoord(selected[0])} <span>Lng:</span> {formatCoord(selected[1])}
                            </div>
                        ) : (
                            <div className="coords dims">Click on the map to select coordinates</div>
                        )}
                        <div style={{ display: 'flex', gap: '8px', marginTop: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                            <input
                                type="number"
                                placeholder="Lat (-90 to 90)"
                                value={latInput}
                                onChange={(e) => setLatInput(e.target.value)}
                                style={{
                                    background: 'rgba(83, 92, 145, 0.3)',
                                    border: '1px solid rgba(146, 144, 195, 0.4)',
                                    color: 'white',
                                    padding: '6px 10px',
                                    borderRadius: '6px',
                                    width: '160px'
                                }}
                            />
                            <input
                                type="number"
                                placeholder="Lng (-180 to 180)"
                                value={lngInput}
                                onChange={(e) => setLngInput(e.target.value)}
                                style={{
                                    background: 'rgba(83, 92, 145, 0.3)',
                                    border: '1px solid rgba(146, 144, 195, 0.4)',
                                    color: 'white',
                                    padding: '6px 10px',
                                    borderRadius: '6px',
                                    width: '180px'
                                }}
                            />
                            <button
                                className="map-toggle-button"
                                onClick={() => {
                                    const lat = parseFloat(latInput)
                                    const lng = parseFloat(lngInput)
                                    if (Number.isFinite(lat) && Number.isFinite(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
                                        setSelected([lat, lng])
                                    } else {
                                        setMessages(prev => [...prev, { role: 'assistant', content: 'Please enter valid coordinates: lat -90..90, lng -180..180.' }])
                                    }
                                }}
                            >
                                Set on Map
                            </button>
                        </div>
                    </div>

                    <MapContainer center={selected || position} zoom={5} scrollWheelZoom={true} key={(selected || position).join(',')}>
                        <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                        <ClickCapture onSelect={setSelected} />
                        <RecenterMap center={selected || position} />
                        <Marker position={selected || position}>
                            <Popup>
                                {selected ? 'Selected location' : 'Your current location.'}
                            </Popup>
                        </Marker>
                        {/* Live Float Tracker Markers */}
                        {liveTrackerOn && liveFloats && liveFloats.map((f, idx) => (
                            <Marker key={`float-${idx}`} position={[f.latitude, f.longitude]}>
                                <Popup>
                                    Float {String(f.platform_number)}<br />
                                    Cycle {String(f.cycle_number)}<br />
                                    Last: {String(f.juld)}<br />
                                    ETA: ~{new Date(new Date(f.juld).getTime() + 10 * 24 * 3600 * 1000).toISOString().split('T')[0]}
                                </Popup>
                            </Marker>
                        ))}

                        {/* SST tile overlay (real) */}
                        {overlaySstOn && (
                            <TileLayer
                                opacity={0.65}
                                zIndex={400}
                                url={(import.meta.env.VITE_SST_TILE_URL || '').trim() || 'about:blank'}
                                attribution={import.meta.env.VITE_SST_ATTR || ''}
                            />
                        )}

                        {/* Cyclone tracks (real GeoJSON) */}
                        {overlayCycloneOn && cycloneData && (
                            <GeoJSON data={cycloneData} style={{ color: '#f97316', weight: 3 }} />
                        )}

                        {/* Fishing zones (real GeoJSON) */}
                        {overlayFishingOn && fishingData && (
                            <GeoJSON data={fishingData} style={{ color: '#22c55e', weight: 2, fillOpacity: 0.15 }} />
                        )}

                        {/* AIS demo overlay */}
                        {overlayAisOn && (
                            <LayerGroup>
                                {aisTargets.map(t => (
                                    <CircleMarker key={t.id} center={[t.lat, t.lng]} radius={5} pathOptions={{ color: '#60a5fa', fillColor: '#60a5fa', fillOpacity: 0.8 }}>
                                        <Popup>
                                            {t.id}<br />
                                            Heading: {Math.round(t.heading)}°<br />
                                            Speed: {Math.round(t.speed)} kn
                                        </Popup>
                                    </CircleMarker>
                                ))}
                            </LayerGroup>
                        )}
                        <AnalyzeVisibleAreaButton
                            onAnalyze={({ north, south, east, west }) => {
                                const prompt = `Analyze ARGO data in the visible area (N:${north.toFixed(2)}, S:${south.toFixed(2)}, E:${east.toFixed(2)}, W:${west.toFixed(2)}). Summarize temperature and salinity patterns, notable anomalies, and recent trends for non-technical users.`
                                handleSendMessage(prompt)
                            }}
                        />
                    </MapContainer>

                    <button
                        className="fetch-button"
                        onClick={() => {
                            const [lat, lng] = selected || position
                            analyzeAt(lat, lng)
                        }}
                        disabled={loading}
                    >
                        <MapPin size={16} style={{ marginRight: '8px' }} />
                        {loading ? 'Analyzing...' : 'Fetch Insights'}
                    </button>
                </div>
            )}


            {/* Visualization Panel */}
            {showVisualizations && (
                <VisualizationPanel
                    data={visualizationData}
                    profession={profession}
                    intent={lastUserQuery}
                    onClose={() => setShowVisualizations(false)}
                />
            )}
        </div>
    )
}

export default Dashboard
