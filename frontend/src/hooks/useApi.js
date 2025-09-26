import { useState, useCallback } from 'react'
import { apiClient } from '../utils/api'

export const useApi = () => {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const execute = useCallback(async (apiCall) => {
        setLoading(true)
        setError(null)

        try {
            const result = await apiCall()
            return result
        } catch (err) {
            setError(err.message)
            throw err
        } finally {
            setLoading(false)
        }
    }, [])

    const chatQuery = useCallback(async (text, profession = 'researcher', lat = null, lon = null, developerMode = false) => {
        return execute(() => apiClient.chatQuery(text, profession, lat, lon, developerMode))
    }, [execute])

    const analyzeLocation = useCallback(async (lat, lon, profession = 'researcher') => {
        return execute(() => apiClient.analyzeLocation(lat, lon, profession))
    }, [execute])

    const getData = useCallback(async (query) => {
        return execute(() => apiClient.getData(query))
    }, [execute])

    return {
        loading,
        error,
        chatQuery,
        analyzeLocation,
        getData,
        execute
    }
}
