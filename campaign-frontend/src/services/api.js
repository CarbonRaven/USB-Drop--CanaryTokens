import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 120000  // 2 minute timeout for long operations like prepare
})

// Request interceptor to add auth token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for token refresh
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refreshToken')
      if (refreshToken) {
        try {
          const response = await axios.post('/api/auth/refresh', {
            refresh_token: refreshToken
          })

          const newToken = response.data.access_token
          localStorage.setItem('accessToken', newToken)
          localStorage.setItem('refreshToken', response.data.refresh_token)

          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return api(originalRequest)
        } catch (refreshError) {
          localStorage.removeItem('accessToken')
          localStorage.removeItem('refreshToken')
          window.location.href = '/login'
        }
      }
    }

    return Promise.reject(error)
  }
)

export default api

// API helper functions
export const campaignsApi = {
  list: () => api.get('/campaigns'),
  get: (id) => api.get(`/campaigns/${id}`),
  create: (data) => api.post('/campaigns', data),
  update: (id, data) => api.put(`/campaigns/${id}`, data),
  deletePreview: (id) => api.get(`/campaigns/${id}/delete-preview`),
  delete: (id, confirm = true) => api.delete(`/campaigns/${id}?confirm=${confirm}`),
  stats: (id) => api.get(`/campaigns/${id}/stats`),
}

export const drivesApi = {
  list: (params) => api.get('/drives', { params }),
  get: (id) => api.get(`/drives/${id}`),
  getByCode: (code) => api.get(`/drives/by-code/${code}`),
  create: (data) => api.post('/drives', data),
  update: (id, data) => api.put(`/drives/${id}`, data),
  delete: (id) => api.delete(`/drives/${id}`),
  prepare: (id) => api.post(`/drives/${id}/prepare`),
  deploy: (id, data) => api.post(`/drives/${id}/deploy`, data),
  deployWithPhoto: (id, formData) => api.post(`/drives/${id}/deploy-with-photo`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deployment: (id) => api.get(`/drives/${id}/deployment`),
  updateDeployment: (id, data) => api.put(`/drives/${id}/deployment`, data),
  download: (id) => api.get(`/drives/${id}/download`, { responseType: 'blob' }),
  tokens: (id) => api.get(`/drives/${id}/tokens`),
}

export const profilesApi = {
  list: (params) => api.get('/profiles', { params }),
  listActive: () => api.get('/profiles', { params: { active_only: true } }),
  get: (id) => api.get(`/profiles/${id}`),
  create: (data) => api.post('/profiles', data),
  update: (id, data) => api.put(`/profiles/${id}`, data),
  delete: (id) => api.delete(`/profiles/${id}`),
  toggle: (id) => api.post(`/profiles/${id}/toggle`),
  preview: (id) => api.get(`/profiles/${id}/preview`),
  // Templates
  templates: () => api.get('/profiles/templates/list'),
  getTemplate: (id) => api.get(`/profiles/templates/${id}`),
  createFromTemplate: (templateId, name) => api.post(`/profiles/from-template/${templateId}`, null, { params: { name } }),
  textTemplates: () => api.get('/profiles/text-templates/list'),
  getTextTemplate: (id) => api.get(`/profiles/text-templates/${id}`),
  tokenTypes: () => api.get('/profiles/token-types/list'),
  // File uploads
  listFiles: (profileId) => api.get(`/profiles/${profileId}/files`),
  uploadFile: (profileId, file, folder = '', tokenType = null) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('folder', folder)
    if (tokenType) {
      formData.append('token_type', tokenType)
    }
    return api.post(`/profiles/${profileId}/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getFile: (profileId, fileId) => api.get(`/profiles/${profileId}/files/${fileId}`),
  updateFile: (profileId, fileId, data) => api.put(`/profiles/${profileId}/files/${fileId}`, data),
  deleteFile: (profileId, fileId) => api.delete(`/profiles/${profileId}/files/${fileId}`),
  downloadFile: (profileId, fileId) => api.get(`/profiles/${profileId}/files/${fileId}/download`, { responseType: 'blob' }),
  reorderFiles: (profileId, fileIds) => api.post(`/profiles/${profileId}/files/reorder`, { file_ids: fileIds }),
  // Shortcuts
  createShortcut: (profileId, data) => api.post(`/profiles/${profileId}/shortcuts`, data),
  // Custom templates
  createTemplate: (profileId, data) => api.post(`/profiles/${profileId}/templates`, data),
  previewTemplate: (profileId, fileId) => api.post(`/profiles/${profileId}/templates/${fileId}/preview`),
}

export const alertsApi = {
  list: (params) => api.get('/alerts', { params }),
  recent: (hours = 24) => api.get('/alerts/recent', { params: { hours } }),
  stats: (campaignId) => api.get('/alerts/stats', { params: { campaign_id: campaignId } }),
  map: (params) => api.get('/alerts/map', { params }),
}

export const reportsApi = {
  campaign: (id) => api.get(`/reports/campaign/${id}`),
  exportCsv: (id) => api.get(`/reports/export/${id}/csv`, { responseType: 'blob' }),
  summary: () => api.get('/reports/summary'),
  // Advanced reports
  executiveSummary: (id) => api.get(`/reports/executive-summary/${id}`),
  temporal: (id) => api.get(`/reports/temporal/${id}`),
  geographic: (id) => api.get(`/reports/geographic/${id}`),
  behavioral: (id) => api.get(`/reports/behavioral/${id}`),
  comparative: () => api.get('/reports/comparative'),
}

export const targetsApi = {
  list: (params) => api.get('/targets', { params }),
  get: (id) => api.get(`/targets/${id}`),
  create: (data) => api.post('/targets', data),
  update: (id, data) => api.put(`/targets/${id}`, data),
  delete: (id) => api.delete(`/targets/${id}`),
  options: () => api.get('/targets/options'),
  recommendScenario: (id) => api.post(`/targets/${id}/recommend-scenario`),
}

export const usersApi = {
  list: () => api.get('/auth/users'),
  get: (id) => api.get(`/auth/users/${id}`),
  create: (data) => api.post('/auth/users', data),
  update: (id, data) => api.put(`/auth/users/${id}`, data),
  delete: (id) => api.delete(`/auth/users/${id}`),
  resetPassword: (id, data) => api.post(`/auth/users/${id}/reset-password`, data),
  changePassword: (data) => api.post('/auth/change-password', data),
  roles: () => api.get('/auth/roles'),
}

export const shortenerApi = {
  // Get all short URLs for a drive
  getByDrive: (driveId) => api.get(`/shortener/drives/${driveId}`),
  // Get a specific short URL
  get: (id) => api.get(`/shortener/${id}`),
  // Get visit stats for a short URL
  stats: (id) => api.get(`/shortener/${id}/stats`),
  // Create short URL for a specific token
  createForToken: (driveId, tokenId, data) => api.post(`/shortener/drives/${driveId}/tokens/${tokenId}`, data),
  // Create short URLs for all tokens on a drive
  createBulk: (driveId, params) => api.post(`/shortener/bulk/drives/${driveId}`, null, { params }),
  // Delete a short URL
  delete: (id) => api.delete(`/shortener/${id}`),
}

export const settingsApi = {
  // Shlink status and configuration
  shlinkStatus: () => api.get('/settings/shlink/status'),
  shlinkConfig: () => api.get('/settings/shlink/config'),
  shlinkTest: () => api.post('/settings/shlink/test'),
  // Domain management (Shlink)
  listDomains: () => api.get('/settings/shlink/domains'),
  addDomain: (domain) => api.post('/settings/shlink/domains', { domain }),
  configureDomainRedirects: (data) => api.patch('/settings/shlink/domains/redirects', data),
  verifyDomainDNS: (domain) => api.post('/settings/shlink/domains/verify-dns', { domain }),
  // Full domain setup (Caddy + Shlink)
  fullDomainSetup: (domain) => api.post('/settings/shlink/domains/full-setup', { domain }),
  // Caddy management
  caddyStatus: () => api.get('/settings/caddy/status'),
  addCaddyDomain: (domain) => api.post('/settings/caddy/domains', { domain }),
  removeCaddyDomain: (domain) => api.delete(`/settings/caddy/domains/${domain}`),
  reloadCaddy: () => api.post('/settings/caddy/reload'),
  // Profile URL configurations
  getUrlConfigs: () => api.get('/settings/url-configs'),
  updateUrlConfig: (profileId, data) => api.put(`/settings/url-configs/${profileId}`, data),
  bulkUpdateUrlConfigs: (updates) => api.put('/settings/url-configs/bulk', updates),
}
