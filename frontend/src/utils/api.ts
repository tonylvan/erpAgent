/**
 * API utility class
 * Based on Fetch API
 */

const API_BASE = '/api/v1'

export const api = {
  /**
   * GET request
   */
  async get(url: string) {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`
    console.log('[API] GET request:', fullUrl)
    try {
      const response = await fetch(fullUrl)
      console.log('[API] Response status:', response.status, response.statusText)
      if (!response.ok) {
        let errorDetail = `HTTP ${response.status}: ${response.statusText}`
        try {
          const errorData = await response.json()
          errorDetail = errorData.detail || errorData.message || errorDetail
        } catch {
          // No JSON body, use status text
        }
        throw new Error(errorDetail)
      }
      return response.json()
    } catch (error: any) {
      console.error('[API] GET error:', error.message)
      throw error
    }
  },

  /**
   * POST request
   */
  async post(url: string, data?: any) {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`
    console.log('[API] POST request:', fullUrl)
    const response = await fetch(fullUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    return response.json()
  },

  /**
   * PUT request
   */
  async put(url: string, data?: any) {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`
    console.log('[API] PUT request:', fullUrl)
    const response = await fetch(fullUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    return response.json()
  },

  /**
   * DELETE request
   */
  async delete(url: string) {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`
    console.log('[API] DELETE request:', fullUrl)
    const response = await fetch(fullUrl)
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    return response.json()
  },
}