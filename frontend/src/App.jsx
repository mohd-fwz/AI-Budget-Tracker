import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Dashboard from './components/Dashboard'
import AuthPage from './components/AuthPage'
import ResetPassword from './components/ResetPassword'
import OnboardingWizard from './components/onboarding/OnboardingWizard'
import { profileAPI } from './services/api'

// Protected Route Component
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return children
}

// Public Route Component (redirect to dashboard if already logged in)
function PublicRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

// Main App with Onboarding Check
function AppContent() {
  const { user, profile } = useAuth()
  const [needsOnboarding, setNeedsOnboarding] = useState(false)
  const [checkingProfile, setCheckingProfile] = useState(true)

  useEffect(() => {
    const checkOnboardingStatus = async () => {
      if (!user) {
        setCheckingProfile(false)
        return
      }

      try {
        const data = await profileAPI.getProfile()

        // Check if profile is incomplete (less than 30% complete)
        // Basic onboarding requires at least: location (state + city)
        const hasLocation = data.profile.state && data.profile.city

        if (!hasLocation) {
          setNeedsOnboarding(true)
        } else {
          setNeedsOnboarding(false)
        }
      } catch (error) {
        console.error('Failed to check profile status:', error)
        // Assume needs onboarding if we can't check
        setNeedsOnboarding(true)
      } finally {
        setCheckingProfile(false)
      }
    }

    checkOnboardingStatus()
  }, [user])

  const handleOnboardingComplete = () => {
    setNeedsOnboarding(false)
  }

  if (checkingProfile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your profile...</p>
        </div>
      </div>
    )
  }

  // Show onboarding if user is logged in but profile is incomplete
  if (user && needsOnboarding) {
    return <OnboardingWizard onComplete={handleOnboardingComplete} />
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <AuthPage />
          </PublicRoute>
        }
      />

      {/* Reset Password Route (public) */}
      <Route path="/reset-password" element={<ResetPassword />} />

      {/* Protected Routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      {/* Default redirects */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  )
}

export default App
