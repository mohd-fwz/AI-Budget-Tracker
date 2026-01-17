import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tokens, setTokens] = useState(() => {
    return {
      access: localStorage.getItem('access_token'),
      refresh: localStorage.getItem('refresh_token')
    }
  })

  // Update localStorage when tokens change
  useEffect(() => {
    if (tokens.access) {
      localStorage.setItem('access_token', tokens.access)
    } else {
      localStorage.removeItem('access_token')
    }

    if (tokens.refresh) {
      localStorage.setItem('refresh_token', tokens.refresh)
    } else {
      localStorage.removeItem('refresh_token')
    }
  }, [tokens])

  // Fetch current user on mount if token exists
  useEffect(() => {
    const fetchCurrentUser = async () => {
      if (!tokens.access) {
        setLoading(false)
        return
      }

      try {
        const response = await axios.get(`${API_BASE_URL}/api/auth/user`, {
          headers: {
            Authorization: `Bearer ${tokens.access}`
          }
        })

        setUser(response.data.user)
        setProfile(response.data.profile)
      } catch (error) {
        console.error('Failed to fetch user:', error)
        // Token might be expired, clear it
        if (error.response?.status === 401) {
          logout()
        }
      } finally {
        setLoading(false)
      }
    }

    fetchCurrentUser()
  }, [])

  // Auto-refresh token before expiry (every 50 minutes)
  useEffect(() => {
    if (!tokens.refresh) return

    const refreshInterval = setInterval(async () => {
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/auth/refresh`,
          {},
          {
            headers: {
              Authorization: `Bearer ${tokens.refresh}`
            }
          }
        )

        setTokens(prev => ({
          ...prev,
          access: response.data.access_token
        }))
      } catch (error) {
        console.error('Token refresh failed:', error)
        logout()
      }
    }, 50 * 60 * 1000) // 50 minutes

    return () => clearInterval(refreshInterval)
  }, [tokens.refresh])

  const register = async (email, password, name) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/register`, {
        email,
        password,
        name
      })

      const { user: newUser, tokens: newTokens, profile: newProfile } = response.data

      setTokens({
        access: newTokens.access,
        refresh: newTokens.refresh
      })
      setUser(newUser)
      setProfile(newProfile)

      return { success: true }
    } catch (error) {
      const message = error.response?.data?.error || 'Registration failed'
      return { success: false, error: message }
    }
  }

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        email,
        password
      })

      const { user: loggedInUser, tokens: newTokens, profile: userProfile } = response.data

      setTokens({
        access: newTokens.access,
        refresh: newTokens.refresh
      })
      setUser(loggedInUser)
      setProfile(userProfile)

      return { success: true }
    } catch (error) {
      const message = error.response?.data?.error || 'Login failed'
      return { success: false, error: message }
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setTokens({ access: null, refresh: null })
    setUser(null)
    setProfile(null)
  }

  const updateProfile = (newProfile) => {
    setProfile(newProfile)
  }

  const value = {
    user,
    profile,
    loading,
    tokens,
    register,
    login,
    logout,
    updateProfile,
    isAuthenticated: !!user
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
