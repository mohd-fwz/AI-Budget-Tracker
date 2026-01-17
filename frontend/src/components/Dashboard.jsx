import { useState } from 'react'
import { DollarSign, TrendingUp, Receipt, Upload, Sparkles, User, LogOut } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import ExpensesView from './ExpensesView'
import AnalyticsView from './AnalyticsView'
import UploadView from './UploadView'
import BudgetPlanner from './BudgetPlanner'
import ProfilePage from './ProfilePage'

const VIEWS = {
  EXPENSES: 'expenses',
  ANALYTICS: 'analytics',
  UPLOAD: 'upload',
  BUDGET: 'budget',
  PROFILE: 'profile',
}

export default function Dashboard() {
  const [activeView, setActiveView] = useState(VIEWS.EXPENSES)
  const navigate = useNavigate()

  const handleSignOut = () => {
    // Clear tokens from localStorage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')

    // Redirect to login
    navigate('/login')
  }

  const menuItems = [
    { id: VIEWS.EXPENSES, label: 'Expenses', icon: Receipt },
    { id: VIEWS.ANALYTICS, label: 'Analytics', icon: TrendingUp },
    { id: VIEWS.UPLOAD, label: 'Upload CSV', icon: Upload },
    { id: VIEWS.BUDGET, label: 'Budget Planner', icon: Sparkles },
    { id: VIEWS.PROFILE, label: 'Profile', icon: User },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="bg-primary-600 p-2 rounded-lg">
                <DollarSign className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">Budget Tracker</h1>
            </div>

            <button
              onClick={handleSignOut}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span className="font-medium">Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Navigation */}
          <aside className="lg:w-64">
            <nav className="bg-white rounded-lg shadow-sm p-4">
              <ul className="space-y-2">
                {menuItems.map(({ id, label, icon: Icon }) => (
                  <li key={id}>
                    <button
                      onClick={() => setActiveView(id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                        activeView === id
                          ? 'bg-primary-600 text-white'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="font-medium">{label}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </nav>
          </aside>

          {/* Main Content */}
          <main className="flex-1">
            {activeView === VIEWS.EXPENSES && <ExpensesView />}
            {activeView === VIEWS.ANALYTICS && <AnalyticsView />}
            {activeView === VIEWS.UPLOAD && <UploadView />}
            {activeView === VIEWS.BUDGET && <BudgetPlanner />}
            {activeView === VIEWS.PROFILE && <ProfilePage />}
          </main>
        </div>
      </div>
    </div>
  )
}
