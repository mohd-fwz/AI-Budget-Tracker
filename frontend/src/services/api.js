import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

// Create axios instance with JWT support
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/api/auth/refresh`, {}, {
            headers: { Authorization: `Bearer ${refreshToken}` }
          })

          const newAccessToken = response.data.access_token
          localStorage.setItem('access_token', newAccessToken)

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          return api(originalRequest)
        } catch (refreshError) {
          // Refresh failed - logout user
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      } else {
        // No refresh token - redirect to login
        window.location.href = '/login'
      }
    }

    console.error('API Error:', error.config?.url, error.response?.data)
    return Promise.reject(error)
  }
)

// Expense API calls
export const expenseAPI = {
  // Add single expense
  addExpense: async (expenseData) => {
    const response = await api.post('/api/expenses', expenseData)
    return response.data
  },

  // Get all expenses
  getExpenses: async (params = {}) => {
    const response = await api.get('/api/expenses', { params })
    return response.data
  },

  // Delete expense
  deleteExpense: async (expenseId) => {
    const response = await api.delete(`/api/expenses/${expenseId}`)
    return response.data
  },

  // Update expense category
  updateExpenseCategory: async (expenseId, category) => {
    const response = await api.patch(`/api/expenses/${expenseId}/category`, { category })
    return response.data
  },

  // Upload bank statement (CSV, PDF, Excel)
  // Three-phase process:
  // Phase 1: Upload and extract
  uploadStatement: async (file, password = null, clearPrevious = true) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('clear_previous', clearPrevious ? 'true' : 'false')

    if (password) {
      formData.append('password', password)
    }

    const response = await api.post('/api/upload-statement', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Phase 2: Select date range and filter transactions
  selectDateRange: async (sessionId, startDate, endDate) => {
    const response = await api.post('/api/select-date-range', {
      session_id: sessionId,
      start_date: startDate,
      end_date: endDate,
    })
    return response.data
  },

  // Phase 3: Import transactions with clarifications
  importTransactions: async (sessionId, clarifications = {}) => {
    const response = await api.post('/api/import-transactions', {
      session_id: sessionId,
      clarifications: clarifications,
    })
    return response.data
  },
}

// Analytics API calls
export const analyticsAPI = {
  // Get analytics
  getAnalytics: async (params = {}) => {
    const response = await api.get('/api/analytics', { params })
    return response.data
  },
}

// Recommendations API calls
export const recommendationsAPI = {
  // Get AI recommendations
  getRecommendations: async (params = {}) => {
    const response = await api.get('/api/recommendations', { params })
    return response.data
  },
}

// Profile API calls
export const profileAPI = {
  // Get user profile
  getProfile: async () => {
    const response = await api.get('/api/profile')
    return response.data
  },

  // Update location
  updateLocation: async (state, city) => {
    const response = await api.put('/api/profile/location', { state, city })
    return response.data
  },

  // Update financial profile
  updateFinancialProfile: async (financialData) => {
    const response = await api.put('/api/profile/financial', financialData)
    return response.data
  },

  // Get category preferences
  getCategoryPreferences: async (category) => {
    const response = await api.get(`/api/profile/category-preferences/${category}`)
    return response.data
  },

  // Update category preferences
  updateCategoryPreferences: async (category, preferences) => {
    const response = await api.put(`/api/profile/category-preferences/${category}`, preferences)
    return response.data
  },

  // Get all states
  getStates: async () => {
    const response = await api.get('/api/locations/states')
    return response.data
  },

  // Get cities for a state
  getCities: async (state) => {
    const response = await api.get(`/api/locations/cities/${state}`)
    return response.data
  },
}

// Auth API calls
export const authAPI = {
  // Change password
  changePassword: async (currentPassword, newPassword) => {
    const response = await api.put('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    })
    return response.data
  },

  // Change email
  changeEmail: async (newEmail, password) => {
    const response = await api.put('/api/auth/change-email', {
      new_email: newEmail,
      password: password
    })
    return response.data
  },

  // Get current user
  getCurrentUser: async () => {
    const response = await api.get('/api/auth/user')
    return response.data
  },

  // Forgot password (request reset token)
  forgotPassword: async (email) => {
    const response = await api.post('/api/auth/forgot-password', { email })
    return response.data
  },

  // Reset password (using token)
  resetPassword: async (token, newPassword) => {
    const response = await api.post('/api/auth/reset-password', {
      token: token,
      new_password: newPassword
    })
    return response.data
  },
}

// Budget API calls
export const budgetAPI = {
  // Generate AI budget recommendations
  generateRecommendations: async (targetMonth = null) => {
    const response = await api.post('/api/budgets/generate', { target_month: targetMonth })
    return response.data
  },

  // Get budgets for a month
  getBudgets: async (month) => {
    const response = await api.get(`/api/budgets/${month}`)
    return response.data
  },

  // Save budgets
  saveBudgets: async (month, budgets) => {
    const response = await api.post('/api/budgets', { month, budgets })
    return response.data
  },

  // Compare budget vs actual
  compareBudgetVsActual: async (month) => {
    const response = await api.get(`/api/budgets/vs-actual/${month}`)
    return response.data
  },
}

// Transaction Insights API
export const insightsAPI = {
  // Get transaction insights
  getTransactionInsights: async (daysBack = 30) => {
    const response = await api.get('/api/insights/transactions', {
      params: { days_back: daysBack }
    })
    return response.data
  },
}

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health')
  return response.data
}

export default api
