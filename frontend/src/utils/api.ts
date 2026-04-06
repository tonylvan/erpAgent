/**
 * 简单的 API 工具类
 * 基于 Fetch API 封装
 */

const API_BASE = '/api/v1'

export const api = {
  /**
   * GET 请求
   */
  async get(url: string) {
    const response = await fetch(url.startsWith('http') ? url : `${API_BASE}${url}`)
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    return response.json()
  },

  /**
   * POST 请求
   */
  async post(url: string, data?: any) {
    const response = await fetch(url.startsWith('http') ? url : `${API_BASE}${url}`, {
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
   * PUT 请求
   */
  async put(url: string, data?: any) {
    const response = await fetch(url.startsWith('http') ? url : `${API_BASE}${url}`, {
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
   * DELETE 请求
   */
  async delete(url: string) {
    const response = await fetch(url.startsWith('http') ? url : `${API_BASE}${url}`)
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    return response.json()
  },
}
