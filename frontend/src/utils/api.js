const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiClient {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`
        console.log('API Request:', { url, options })

        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        }

        try {
            const response = await fetch(url, config)
            console.log('API Response:', { status: response.status, ok: response.ok })

            if (!response.ok) {
                const errorText = await response.text()
                console.error('API Error:', { status: response.status, text: errorText })
                throw new Error(`HTTP ${response.status}: ${errorText}`)
            }

            const data = await response.json()
            console.log('API Data:', data)
            return data
        } catch (error) {
            console.error('API request failed:', error)
            throw error
        }
    }

    async chatQuery(text, profession = 'researcher', lat = null, lon = null, developerMode = false) {
        return this.request('/api/chat', {
            method: 'POST',
            body: JSON.stringify({
                text,
                profession: profession.toLowerCase(),
                ...(lat && lon && { lat, lon }),
                developerMode
            })
        })
    }

    async getData(query) {
        return this.request(`/api/data?query=${encodeURIComponent(query)}`)
    }

    async getParquet(file = 'argo_profiles_long.parquet', limit = 500) {
        const params = new URLSearchParams({ file, limit: String(limit) })
        return this.request(`/api/parquet?${params.toString()}`)
    }

    async parquetSql(query, files = ['argo_profiles_long.parquet'], limit = 500) {
        return this.request('/api/parquet_sql', {
            method: 'POST',
            body: JSON.stringify({ query, files, limit })
        })
    }

    async postgresSql(query, limit = 200) {
        return this.request('/api/sql', {
            method: 'POST',
            body: JSON.stringify({ query, limit })
        })
    }

    async analyzeLocation(lat, lon, profession = 'researcher') {
        return this.chatQuery(
            `Analyze ARGO data near coordinates ${lat}, ${lon}`,
            profession,
            lat,
            lon
        )
    }
}

export const apiClient = new ApiClient()
export default apiClient
