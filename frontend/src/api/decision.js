/**
 * 决策分析 API 模块
 */

import axios from 'axios'

const API_BASE = '/api/v1/decision'

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000
})

export const decisionAnalyticsApi = {
  // 库存决策分析
  async getInventoryReplenishment(productId = null) {
    const params = productId ? { product_id: productId } : {}
    const { data } = await apiClient.get('/inventory/replenishment', { params })
    return data
  },

  async getSlowMovingInventory(daysThreshold = 90) {
    const { data } = await apiClient.get('/inventory/slow-moving', {
      params: { days_threshold: daysThreshold }
    })
    return data
  },

  async getInventoryDistribution() {
    const { data } = await apiClient.get('/inventory/distribution')
    return data
  },

  // 采购决策分析
  async getSupplierPerformance(supplierId = null) {
    const params = supplierId ? { supplier_id: supplierId } : {}
    const { data } = await apiClient.get('/procurement/supplier-performance', { params })
    return data
  },

  async getProcurementTiming(productId = null) {
    const params = productId ? { product_id: productId } : {}
    const { data } = await apiClient.get('/procurement/timing', { params })
    return data
  },

  async getSupplierRisk() {
    const { data } = await apiClient.get('/procurement/supplier-risk')
    return data
  },

  // 销售决策分析
  async getPricingElasticity(productId = null) {
    const params = productId ? { product_id: productId } : {}
    const { data } = await apiClient.get('/sales/pricing-elasticity', { params })
    return data
  },

  async getPromotionEffectiveness(daysLookback = 90) {
    const { data } = await apiClient.get('/sales/promotion-effectiveness', {
      params: { days_lookback: daysLookback }
    })
    return data
  },

  async getCustomerSegmentation() {
    const { data } = await apiClient.get('/sales/customer-segmentation')
    return data
  },

  // 财务决策分析
  async getCashFlowForecast(daysForecast = 30) {
    const { data } = await apiClient.get('/financial/cash-flow-forecast', {
      params: { days_forecast: daysForecast }
    })
    return data
  },

  async getPaymentPriority() {
    const { data } = await apiClient.get('/financial/payment-priority')
    return data
  },

  async getARAging() {
    const { data } = await apiClient.get('/financial/ar-aging')
    return data
  },

  // 客户决策分析
  async getCustomerLifetimeValue() {
    const { data } = await apiClient.get('/customer/lifetime-value')
    return data
  },

  async getChurnRisk() {
    const { data } = await apiClient.get('/customer/churn-risk')
    return data
  },

  async getCustomerAcquisitionCost() {
    const { data } = await apiClient.get('/customer/acquisition-cost')
    return data
  }
}
