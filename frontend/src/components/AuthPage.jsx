import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import { Lock, Mail, User, Eye, EyeOff } from 'lucide-react'
import { authAPI } from '../services/api'

export default function AuthPage() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login') // 'login', 'register', or 'forgot-password'
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      if (mode === 'forgot-password') {
        // Handle forgot password
        const response = await authAPI.forgotPassword(formData.email)
        setSuccess(response.message)

        // For development: show the reset token
        if (response.reset_token) {
          console.log('Reset Token (dev only):', response.reset_token)
          setSuccess(`${response.message}\n\nFor testing: Your reset token is ${response.reset_token}\nNavigate to /reset-password?token=${response.reset_token}`)
        }
      } else {
        // Handle login or register
        let result
        if (mode === 'login') {
          result = await login(formData.email, formData.password)
        } else {
          result = await register(formData.email, formData.password, formData.name)
        }

        if (result.success) {
          navigate('/dashboard')
        } else {
          setError(result.error)
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleModeSwitch = () => {
    if (mode === 'login') {
      setMode('register')
    } else if (mode === 'register') {
      setMode('login')
    } else {
      setMode('login')
    }
    setError('')
    setSuccess('')
    setFormData({ email: '', password: '', name: '' })
  }

  const handleForgotPassword = () => {
    setMode('forgot-password')
    setError('')
    setSuccess('')
    setFormData({ email: '', password: '', name: '' })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full mb-4">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900">
            {mode === 'login' && 'Welcome Back'}
            {mode === 'register' && 'Create Account'}
            {mode === 'forgot-password' && 'Reset Password'}
          </h2>
          <p className="text-gray-600 mt-2">
            {mode === 'login' && 'Sign in to access your budget planner'}
            {mode === 'register' && 'Start managing your finances smarter'}
            {mode === 'forgot-password' && 'Enter your email to receive reset instructions'}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded">
            <p className="text-sm text-red-800 whitespace-pre-line">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-6 rounded">
            <p className="text-sm text-green-800 whitespace-pre-line">{success}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Name field (register only) */}
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  placeholder="John Doe"
                />
              </div>
            </div>
          )}

          {/* Email field */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                placeholder="you@example.com"
              />
            </div>
          </div>

          {/* Password field (not shown in forgot-password mode) */}
          {mode !== 'forgot-password' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  placeholder={mode === 'register' ? 'Min. 8 characters' : '••••••••'}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
              {mode === 'register' && (
                <p className="text-xs text-gray-500 mt-1">
                  Must contain: 8+ characters, uppercase, lowercase, and number
                </p>
              )}
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {loading && mode === 'login' && 'Logging in...'}
            {loading && mode === 'register' && 'Creating account...'}
            {loading && mode === 'forgot-password' && 'Sending reset link...'}
            {!loading && mode === 'login' && 'Log In'}
            {!loading && mode === 'register' && 'Sign Up'}
            {!loading && mode === 'forgot-password' && 'Send Reset Link'}
          </button>
        </form>

        {/* Forgot password link (only in login mode) */}
        {mode === 'login' && (
          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={handleForgotPassword}
              className="text-sm text-purple-600 hover:text-purple-700 font-medium"
            >
              Forgot your password?
            </button>
          </div>
        )}

        {/* Mode switch */}
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={handleModeSwitch}
            className="text-purple-600 hover:text-purple-700 font-medium text-sm"
          >
            {mode === 'login' && "Don't have an account? Sign up"}
            {mode === 'register' && 'Already have an account? Log in'}
            {mode === 'forgot-password' && 'Back to login'}
          </button>
        </div>

        {/* Privacy note */}
        {mode === 'register' && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <p className="text-xs text-blue-800">
              <strong>Your privacy matters:</strong> All your financial data is encrypted and
              stored securely. We never share your information with third parties.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
