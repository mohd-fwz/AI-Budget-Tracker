import { useState, useEffect } from 'react'
import { profileAPI, authAPI } from '../services/api'
import { Save, MapPin, DollarSign, Users, Briefcase, Calendar, RefreshCw, Settings, Lock, Mail, Shield } from 'lucide-react'

const INDIAN_STATES_CITIES = {
  "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kurnool"],
  "Karnataka": ["Bangalore", "Mysore", "Mangalore", "Hubli", "Belgaum"],
  "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Thane", "Nashik"],
  "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"],
  "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam"],
  "Delhi": ["New Delhi", "North Delhi", "South Delhi", "East Delhi", "West Delhi"],
  "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar"],
  "West Bengal": ["Kolkata", "Asansol", "Siliguri", "Durgapur", "Bardhaman"],
  "Rajasthan": ["Jaipur", "Jodhpur", "Kota", "Bikaner", "Ajmer"],
  "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Kollam", "Thrissur"]
}

const STREAMING_SERVICES = [
  { id: 'netflix', name: 'Netflix', typical_cost: 649 },
  { id: 'prime_video', name: 'Amazon Prime Video', typical_cost: 299 },
  { id: 'hotstar', name: 'Disney+ Hotstar', typical_cost: 299 },
  { id: 'spotify', name: 'Spotify', typical_cost: 119 },
  { id: 'youtube_premium', name: 'YouTube Premium', typical_cost: 129 },
  { id: 'zee5', name: 'ZEE5', typical_cost: 99 },
  { id: 'sony_liv', name: 'SonyLIV', typical_cost: 299 }
]

const DEFAULT_ACTIVITY_TYPES = [
  { id: 'movies', name: 'Movies/Cinema', icon: '🎬' },
  { id: 'dining', name: 'Dining Out', icon: '🍽️' },
  { id: 'sports', name: 'Sports (Gym/Sports)', icon: '⚽' },
  { id: 'hobbies', name: 'Hobbies/Classes', icon: '🎨' },
  { id: 'bowling', name: 'Bowling', icon: '🎳' },
  { id: 'gokarting', name: 'Go-Karting', icon: '🏎️' },
  { id: 'gaming', name: 'Gaming/Arcade', icon: '🎮' },
  { id: 'concerts', name: 'Concerts/Events', icon: '🎵' },
  { id: 'travel', name: 'Weekend Trips', icon: '✈️' },
  { id: 'spa', name: 'Spa/Wellness', icon: '💆' }
]

export default function ProfilePage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [activeSection, setActiveSection] = useState('basic')
  const [currentUser, setCurrentUser] = useState(null)

  // Basic info state
  const [basicInfo, setBasicInfo] = useState({
    state: '',
    city: '',
    monthly_income: '',
    savings_goal: '',
    family_size: 1,
    age_group: '',
    occupation: ''
  })

  // Category preferences state
  const [categoryPrefs, setCategoryPrefs] = useState({
    Groceries: {},
    Transport: {},
    Entertainment: {},
    Bills: {}
  })

  // Account settings state
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  })

  const [emailForm, setEmailForm] = useState({
    new_email: '',
    password: ''
  })

  // Custom activity state
  const [customActivity, setCustomActivity] = useState('')
  const [customActivities, setCustomActivities] = useState([])

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      setLoading(true)
      const data = await profileAPI.getProfile()
      const userData = await authAPI.getCurrentUser()

      // Set current user
      setCurrentUser(userData.user)

      // Set basic info
      setBasicInfo({
        state: data.profile.state || '',
        city: data.profile.city || '',
        monthly_income: data.profile.monthly_income || '',
        savings_goal: data.profile.savings_goal || '',
        family_size: data.profile.family_size || 1,
        age_group: data.profile.age_group || '',
        occupation: data.profile.occupation || ''
      })

      // Load category preferences
      const categoryPreferences = JSON.parse(data.profile.category_preferences || '{}')

      // Load custom activities if any
      if (categoryPreferences.Entertainment?.custom_activities) {
        setCustomActivities(categoryPreferences.Entertainment.custom_activities)
      }

      setCategoryPrefs({
        Groceries: categoryPreferences.Groceries || {},
        Transport: categoryPreferences.Transport || {},
        Entertainment: categoryPreferences.Entertainment || {},
        Bills: categoryPreferences.Bills || {}
      })

    } catch (error) {
      console.error('Error loading profile:', error)
      setMessage({ type: 'error', text: 'Failed to load profile' })
    } finally {
      setLoading(false)
    }
  }

  const handleSaveBasicInfo = async () => {
    try {
      setSaving(true)
      setMessage({ type: '', text: '' })

      // Update location
      if (basicInfo.state && basicInfo.city) {
        await profileAPI.updateLocation(basicInfo.state, basicInfo.city)
      }

      // Update financial profile
      await profileAPI.updateFinancialProfile({
        monthly_income: basicInfo.monthly_income,
        savings_goal: basicInfo.savings_goal,
        family_size: basicInfo.family_size,
        age_group: basicInfo.age_group,
        occupation: basicInfo.occupation
      })

      setMessage({ type: 'success', text: 'Basic information updated successfully!' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      console.error('Error saving basic info:', error)
      setMessage({ type: 'error', text: 'Failed to update information' })
    } finally {
      setSaving(false)
    }
  }

  const handleSaveCategoryPrefs = async (category) => {
    try {
      setSaving(true)
      setMessage({ type: '', text: '' })

      await profileAPI.updateCategoryPreferences(category, categoryPrefs[category])

      setMessage({ type: 'success', text: `${category} preferences updated successfully!` })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      console.error('Error saving category preferences:', error)
      setMessage({ type: 'error', text: 'Failed to update preferences' })
    } finally {
      setSaving(false)
    }
  }

  const updateCategoryPref = (category, field, value) => {
    setCategoryPrefs(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [field]: value
      }
    }))
  }

  const toggleSubscription = (serviceId) => {
    const current = categoryPrefs.Entertainment.subscriptions || []
    const updated = current.includes(serviceId)
      ? current.filter(s => s !== serviceId)
      : [...current, serviceId]

    updateCategoryPref('Entertainment', 'subscriptions', updated)
  }

  const toggleActivity = (activityId) => {
    const activities = categoryPrefs.Entertainment.activities || {}
    updateCategoryPref('Entertainment', 'activities', {
      ...activities,
      [activityId]: !activities[activityId]
    })
  }

  const addCustomActivity = () => {
    if (!customActivity.trim()) return

    const activityId = customActivity.toLowerCase().replace(/[^a-z0-9]/g, '_')
    const newActivity = {
      id: activityId,
      name: customActivity.trim(),
      icon: '🎯', // Default icon for custom activities
      custom: true
    }

    // Add to custom activities list
    const updatedCustomActivities = [...customActivities, newActivity]
    setCustomActivities(updatedCustomActivities)

    // Automatically select the new activity
    const activities = categoryPrefs.Entertainment.activities || {}
    updateCategoryPref('Entertainment', 'activities', {
      ...activities,
      [activityId]: true
    })

    // Save custom activities list
    updateCategoryPref('Entertainment', 'custom_activities', updatedCustomActivities)

    // Clear input
    setCustomActivity('')
  }

  const removeCustomActivity = (activityId) => {
    // Remove from custom activities list
    const updatedCustomActivities = customActivities.filter(a => a.id !== activityId)
    setCustomActivities(updatedCustomActivities)

    // Remove from selected activities
    const activities = { ...(categoryPrefs.Entertainment.activities || {}) }
    delete activities[activityId]
    updateCategoryPref('Entertainment', 'activities', activities)

    // Update custom activities list
    updateCategoryPref('Entertainment', 'custom_activities', updatedCustomActivities)
  }

  const handleChangePassword = async () => {
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match' })
      return
    }

    try {
      setSaving(true)
      setMessage({ type: '', text: '' })

      await authAPI.changePassword(passwordForm.current_password, passwordForm.new_password)

      setMessage({ type: 'success', text: 'Password changed successfully!' })
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      console.error('Error changing password:', error)
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to change password' })
    } finally {
      setSaving(false)
    }
  }

  const handleChangeEmail = async () => {
    try {
      setSaving(true)
      setMessage({ type: '', text: '' })

      const response = await authAPI.changeEmail(emailForm.new_email, emailForm.password)

      setCurrentUser(response.user)
      setMessage({ type: 'success', text: 'Email changed successfully!' })
      setEmailForm({ new_email: '', password: '' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      console.error('Error changing email:', error)
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to change email' })
    } finally {
      setSaving(false)
    }
  }

  const sections = [
    { id: 'account', label: 'Account', icon: Shield },
    { id: 'basic', label: 'Basic Info', icon: Settings },
    { id: 'groceries', label: 'Groceries', icon: '🛒' },
    { id: 'transport', label: 'Transport', icon: '🚗' },
    { id: 'entertainment', label: 'Entertainment', icon: '🎬' },
    { id: 'bills', label: 'Rent & Bills', icon: '🏠' }
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl shadow-lg px-8 py-6 text-white">
        <div className="flex items-center gap-3">
          <div className="bg-white/20 p-3 rounded-lg backdrop-blur-sm">
            <Settings className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Profile Settings</h2>
            <p className="text-purple-100 text-sm mt-1">
              Manage your personal information and preferences
            </p>
          </div>
        </div>
      </div>

      {/* Message */}
      {message.text && (
        <div
          className={`flex items-center gap-3 p-4 rounded-xl ${
            message.type === 'success'
              ? 'bg-green-50 border-2 border-green-200 text-green-800'
              : 'bg-red-50 border-2 border-red-200 text-red-800'
          }`}
        >
          <Save className="w-5 h-5 flex-shrink-0" />
          <span className="font-medium">{message.text}</span>
        </div>
      )}

      {/* Section Navigation */}
      <div className="bg-white rounded-xl shadow-sm p-4">
        <div className="flex flex-wrap gap-2">
          {sections.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveSection(id)}
              className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${
                activeSection === id
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {typeof Icon === 'string' ? (
                <span>{Icon}</span>
              ) : (
                <Icon className="w-4 h-4" />
              )}
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Account Section */}
      {activeSection === 'account' && currentUser && (
        <div className="space-y-6">
          {/* Current Account Info */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl shadow-sm p-6 border-2 border-blue-200">
            <h3 className="text-xl font-semibold text-gray-900 flex items-center gap-2 mb-4">
              <Shield className="w-5 h-5" />
              Account Information
            </h3>
            <div className="bg-white p-4 rounded-lg">
              <div className="flex items-center gap-3">
                <Mail className="w-5 h-5 text-gray-600" />
                <div>
                  <p className="text-sm text-gray-600">Email Address</p>
                  <p className="text-lg font-semibold text-gray-900">{currentUser.email}</p>
                </div>
              </div>
              {currentUser.created_at && (
                <p className="text-xs text-gray-500 mt-2">
                  Member since {new Date(currentUser.created_at).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>

          {/* Change Password */}
          <div className="bg-white rounded-xl shadow-sm p-6 space-y-4">
            <h3 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <Lock className="w-5 h-5" />
              Change Password
            </h3>
            <p className="text-sm text-gray-600">
              Password must be at least 8 characters with uppercase, lowercase, and number.
            </p>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Current Password</label>
              <input
                type="password"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                placeholder="Enter current password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">New Password</label>
              <input
                type="password"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                placeholder="Enter new password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Confirm New Password</label>
              <input
                type="password"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                placeholder="Confirm new password"
              />
            </div>

            <button
              onClick={handleChangePassword}
              disabled={saving || !passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_password}
              className="w-full py-3 px-6 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-indigo-700 disabled:from-gray-300 disabled:to-gray-300 transition-all flex items-center justify-center gap-2"
            >
              <Lock className="w-5 h-5" />
              {saving ? 'Changing Password...' : 'Change Password'}
            </button>
          </div>

          {/* Change Email */}
          <div className="bg-white rounded-xl shadow-sm p-6 space-y-4">
            <h3 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <Mail className="w-5 h-5" />
              Change Email Address
            </h3>
            <p className="text-sm text-gray-600">
              Update your email address. You'll need to enter your password to confirm.
            </p>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">New Email Address</label>
              <input
                type="email"
                value={emailForm.new_email}
                onChange={(e) => setEmailForm({ ...emailForm, new_email: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                placeholder="newemail@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Confirm Password</label>
              <input
                type="password"
                value={emailForm.password}
                onChange={(e) => setEmailForm({ ...emailForm, password: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                placeholder="Enter your password"
              />
            </div>

            <button
              onClick={handleChangeEmail}
              disabled={saving || !emailForm.new_email || !emailForm.password}
              className="w-full py-3 px-6 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-cyan-700 disabled:from-gray-300 disabled:to-gray-300 transition-all flex items-center justify-center gap-2"
            >
              <Mail className="w-5 h-5" />
              {saving ? 'Changing Email...' : 'Change Email'}
            </button>
          </div>
        </div>
      )}

      {/* Basic Info Section */}
      {activeSection === 'basic' && (
        <div className="bg-white rounded-xl shadow-sm p-6 space-y-6">
          <h3 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Basic Information
          </h3>

          {/* Location */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <MapPin className="w-4 h-4 inline mr-1" />
                State
              </label>
              <select
                value={basicInfo.state}
                onChange={(e) => setBasicInfo({ ...basicInfo, state: e.target.value, city: '' })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              >
                <option value="">Select state</option>
                {Object.keys(INDIAN_STATES_CITIES).map(state => (
                  <option key={state} value={state}>{state}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                City
              </label>
              <select
                value={basicInfo.city}
                onChange={(e) => setBasicInfo({ ...basicInfo, city: e.target.value })}
                disabled={!basicInfo.state}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-50"
              >
                <option value="">Select city</option>
                {basicInfo.state && INDIAN_STATES_CITIES[basicInfo.state]?.map(city => (
                  <option key={city} value={city}>{city}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Financial Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <DollarSign className="w-4 h-4 inline mr-1" />
                Monthly Income (Rs.)
              </label>
              <input
                type="number"
                value={basicInfo.monthly_income}
                onChange={(e) => setBasicInfo({ ...basicInfo, monthly_income: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                placeholder="50000"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Savings Goal (Rs./month)
              </label>
              <input
                type="number"
                value={basicInfo.savings_goal}
                onChange={(e) => setBasicInfo({ ...basicInfo, savings_goal: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                placeholder="15000"
              />
            </div>
          </div>

          {/* Personal Info */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Users className="w-4 h-4 inline mr-1" />
                Family Size
              </label>
              <input
                type="number"
                min="1"
                value={basicInfo.family_size}
                onChange={(e) => setBasicInfo({ ...basicInfo, family_size: parseInt(e.target.value) || 1 })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-1" />
                Age Group
              </label>
              <select
                value={basicInfo.age_group}
                onChange={(e) => setBasicInfo({ ...basicInfo, age_group: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              >
                <option value="">Select age</option>
                <option value="18-25">18-25</option>
                <option value="26-35">26-35</option>
                <option value="36-45">36-45</option>
                <option value="46-60">46-60</option>
                <option value="60+">60+</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Briefcase className="w-4 h-4 inline mr-1" />
                Occupation
              </label>
              <select
                value={basicInfo.occupation}
                onChange={(e) => setBasicInfo({ ...basicInfo, occupation: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              >
                <option value="">Select</option>
                <option value="salaried">Salaried</option>
                <option value="self_employed">Self Employed</option>
                <option value="student">Student</option>
                <option value="retired">Retired</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleSaveBasicInfo}
            disabled={saving}
            className="w-full py-3 px-6 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-300 transition-all flex items-center justify-center gap-2"
          >
            <Save className="w-5 h-5" />
            {saving ? 'Saving...' : 'Save Basic Information'}
          </button>
        </div>
      )}

      {/* Groceries Section */}
      {activeSection === 'groceries' && (
        <div className="bg-white rounded-xl shadow-sm p-6 space-y-6">
          <h3 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <span className="text-2xl">🛒</span>
            Groceries Preferences
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Dietary Preference</label>
              <select
                value={categoryPrefs.Groceries.diet_type || ''}
                onChange={(e) => updateCategoryPref('Groceries', 'diet_type', e.target.value)}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
              >
                <option value="">Select diet type</option>
                <option value="vegetarian">Vegetarian</option>
                <option value="non_vegetarian">Non-Vegetarian</option>
                <option value="vegan">Vegan</option>
                <option value="eggetarian">Eggetarian</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Shopping Frequency</label>
              <select
                value={categoryPrefs.Groceries.shopping_frequency || ''}
                onChange={(e) => updateCategoryPref('Groceries', 'shopping_frequency', e.target.value)}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
              >
                <option value="">Select frequency</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="bi_weekly">Bi-Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Rice (kg/month)</label>
                <input
                  type="number"
                  min="0"
                  value={categoryPrefs.Groceries.consumption_items?.rice_kg_per_month || 0}
                  onChange={(e) => updateCategoryPref('Groceries', 'consumption_items', {
                    ...categoryPrefs.Groceries.consumption_items,
                    rice_kg_per_month: parseFloat(e.target.value) || 0
                  })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Wheat (kg/month)</label>
                <input
                  type="number"
                  min="0"
                  value={categoryPrefs.Groceries.consumption_items?.wheat_kg_per_month || 0}
                  onChange={(e) => updateCategoryPref('Groceries', 'consumption_items', {
                    ...categoryPrefs.Groceries.consumption_items,
                    wheat_kg_per_month: parseFloat(e.target.value) || 0
                  })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Vegetables (kg/week)</label>
                <input
                  type="number"
                  min="0"
                  value={categoryPrefs.Groceries.consumption_items?.vegetables_kg_per_week || 0}
                  onChange={(e) => updateCategoryPref('Groceries', 'consumption_items', {
                    ...categoryPrefs.Groceries.consumption_items,
                    vegetables_kg_per_week: parseFloat(e.target.value) || 0
                  })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Dairy (L/week)</label>
                <input
                  type="number"
                  min="0"
                  value={categoryPrefs.Groceries.consumption_items?.dairy_liters_per_week || 0}
                  onChange={(e) => updateCategoryPref('Groceries', 'consumption_items', {
                    ...categoryPrefs.Groceries.consumption_items,
                    dairy_liters_per_week: parseFloat(e.target.value) || 0
                  })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>
          </div>

          <button
            onClick={() => handleSaveCategoryPrefs('Groceries')}
            disabled={saving}
            className="w-full py-3 px-6 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 disabled:from-gray-300 disabled:to-gray-300 transition-all flex items-center justify-center gap-2"
          >
            <Save className="w-5 h-5" />
            {saving ? 'Saving...' : 'Save Groceries Preferences'}
          </button>
        </div>
      )}

      {/* Transport Section */}
      {activeSection === 'transport' && (
        <div className="bg-white rounded-xl shadow-sm p-6 space-y-6">
          <h3 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <span className="text-2xl">🚗</span>
            Transport Preferences
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Primary Transport Mode</label>
              <select
                value={categoryPrefs.Transport.mode || ''}
                onChange={(e) => updateCategoryPref('Transport', 'mode', e.target.value)}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select mode</option>
                <option value="own_vehicle">Own Vehicle</option>
                <option value="public_transport">Public Transport</option>
                <option value="mixed">Mixed (Both)</option>
              </select>
            </div>

            {(categoryPrefs.Transport.mode === 'own_vehicle' || categoryPrefs.Transport.mode === 'mixed') && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Vehicle Type</label>
                    <select
                      value={categoryPrefs.Transport.vehicle_type || ''}
                      onChange={(e) => updateCategoryPref('Transport', 'vehicle_type', e.target.value)}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select</option>
                      <option value="bike">Bike/Scooter</option>
                      <option value="car">Car</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Fuel Type</label>
                    <select
                      value={categoryPrefs.Transport.fuel_type || ''}
                      onChange={(e) => updateCategoryPref('Transport', 'fuel_type', e.target.value)}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select</option>
                      <option value="petrol">Petrol</option>
                      <option value="diesel">Diesel</option>
                      <option value="cng">CNG</option>
                      <option value="electric">Electric</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Average km/month</label>
                  <input
                    type="number"
                    min="0"
                    value={categoryPrefs.Transport.avg_km_per_month || 0}
                    onChange={(e) => updateCategoryPref('Transport', 'avg_km_per_month', parseFloat(e.target.value) || 0)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </>
            )}

            {(categoryPrefs.Transport.mode === 'public_transport' || categoryPrefs.Transport.mode === 'mixed') && (
              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-700">Public Transport Usage</p>

                <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer">
                  <input
                    type="checkbox"
                    checked={categoryPrefs.Transport.public_transport?.uses_metro || false}
                    onChange={(e) => updateCategoryPref('Transport', 'public_transport', {
                      ...categoryPrefs.Transport.public_transport,
                      uses_metro: e.target.checked
                    })}
                    className="w-5 h-5 text-blue-600 rounded"
                  />
                  <span>I use Metro</span>
                </label>

                {categoryPrefs.Transport.public_transport?.uses_metro && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Metro Monthly Cost (Rs.)</label>
                    <input
                      type="number"
                      min="0"
                      value={categoryPrefs.Transport.public_transport?.metro_monthly_cost || 0}
                      onChange={(e) => updateCategoryPref('Transport', 'public_transport', {
                        ...categoryPrefs.Transport.public_transport,
                        metro_monthly_cost: parseFloat(e.target.value) || 0
                      })}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}

                <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer">
                  <input
                    type="checkbox"
                    checked={categoryPrefs.Transport.public_transport?.uses_bus || false}
                    onChange={(e) => updateCategoryPref('Transport', 'public_transport', {
                      ...categoryPrefs.Transport.public_transport,
                      uses_bus: e.target.checked
                    })}
                    className="w-5 h-5 text-blue-600 rounded"
                  />
                  <span>I use Bus</span>
                </label>

                {categoryPrefs.Transport.public_transport?.uses_bus && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Bus Monthly Cost (Rs.)</label>
                    <input
                      type="number"
                      min="0"
                      value={categoryPrefs.Transport.public_transport?.bus_monthly_cost || 0}
                      onChange={(e) => updateCategoryPref('Transport', 'public_transport', {
                        ...categoryPrefs.Transport.public_transport,
                        bus_monthly_cost: parseFloat(e.target.value) || 0
                      })}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}
              </div>
            )}
          </div>

          <button
            onClick={() => handleSaveCategoryPrefs('Transport')}
            disabled={saving}
            className="w-full py-3 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-300 disabled:to-gray-300 transition-all flex items-center justify-center gap-2"
          >
            <Save className="w-5 h-5" />
            {saving ? 'Saving...' : 'Save Transport Preferences'}
          </button>
        </div>
      )}

      {/* Entertainment Section */}
      {activeSection === 'entertainment' && (
        <div className="bg-white rounded-xl shadow-sm p-6 space-y-6">
          <h3 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <span className="text-2xl">🎬</span>
            Entertainment Preferences
          </h3>

          <div className="space-y-6">
            {/* Streaming Services */}
            <div>
              <p className="text-sm font-medium text-gray-700 mb-3">Streaming Subscriptions</p>
              <div className="grid grid-cols-2 gap-3">
                {STREAMING_SERVICES.map(service => {
                  const isSelected = (categoryPrefs.Entertainment.subscriptions || []).includes(service.id)

                  return (
                    <button
                      key={service.id}
                      onClick={() => toggleSubscription(service.id)}
                      className={`p-4 rounded-lg border-2 transition text-left ${
                        isSelected
                          ? 'border-purple-600 bg-white shadow-md'
                          : 'border-gray-200 bg-white hover:border-purple-300'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-gray-800 text-sm">{service.name}</span>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          className="w-4 h-4 text-purple-600 rounded"
                        />
                      </div>
                      <span className="text-xs text-gray-500">₹{service.typical_cost}/month</span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Activities */}
            <div>
              <p className="text-sm font-medium text-gray-700 mb-3">Entertainment Activities</p>

              {/* Default Activities */}
              <div className="space-y-3 mb-4">
                {DEFAULT_ACTIVITY_TYPES.map(activity => (
                  <label
                    key={activity.id}
                    className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition"
                  >
                    <input
                      type="checkbox"
                      checked={categoryPrefs.Entertainment.activities?.[activity.id] || false}
                      onChange={() => toggleActivity(activity.id)}
                      className="w-5 h-5 text-purple-600 rounded"
                    />
                    <span className="text-2xl">{activity.icon}</span>
                    <span className="font-medium text-gray-800">{activity.name}</span>
                  </label>
                ))}
              </div>

              {/* Custom Activities */}
              {customActivities.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-medium text-purple-600 mb-2 uppercase">Your Custom Activities</p>
                  <div className="space-y-2">
                    {customActivities.map(activity => (
                      <div
                        key={activity.id}
                        className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg border-2 border-purple-200"
                      >
                        <input
                          type="checkbox"
                          checked={categoryPrefs.Entertainment.activities?.[activity.id] || false}
                          onChange={() => toggleActivity(activity.id)}
                          className="w-5 h-5 text-purple-600 rounded"
                        />
                        <span className="text-2xl">{activity.icon}</span>
                        <span className="font-medium text-gray-800 flex-1">{activity.name}</span>
                        <button
                          onClick={() => removeCustomActivity(activity.id)}
                          className="text-red-500 hover:text-red-700 text-sm font-medium"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Add Custom Activity */}
              <div className="mt-4 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border-2 border-dashed border-purple-300">
                <p className="text-sm font-medium text-purple-700 mb-2">Add Your Own Activity</p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={customActivity}
                    onChange={(e) => setCustomActivity(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addCustomActivity()}
                    placeholder="e.g., Bowling, Go-Karting, Paintball..."
                    className="flex-1 px-3 py-2 border-2 border-purple-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  <button
                    onClick={addCustomActivity}
                    disabled={!customActivity.trim()}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
                  >
                    Add
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Add activities like Bowling, Go-Karting, Paintball, Rock Climbing, etc.
                </p>
              </div>
            </div>

            {/* Monthly Budget */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Monthly Entertainment Budget (Rs.)
              </label>
              <input
                type="number"
                min="0"
                value={categoryPrefs.Entertainment.monthly_entertainment_budget || 0}
                onChange={(e) => updateCategoryPref('Entertainment', 'monthly_entertainment_budget', parseFloat(e.target.value) || 0)}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500"
                placeholder="2000"
              />
            </div>
          </div>

          <button
            onClick={() => handleSaveCategoryPrefs('Entertainment')}
            disabled={saving}
            className="w-full py-3 px-6 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 disabled:from-gray-300 disabled:to-gray-300 transition-all flex items-center justify-center gap-2"
          >
            <Save className="w-5 h-5" />
            {saving ? 'Saving...' : 'Save Entertainment Preferences'}
          </button>
        </div>
      )}

      {/* Bills Section */}
      {activeSection === 'bills' && (
        <div className="bg-white rounded-xl shadow-sm p-6 space-y-6">
          <h3 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <span className="text-2xl">🏠</span>
            Rent & Bills
          </h3>

          <div className="space-y-4">
            {/* Rent */}
            <label className="flex items-center gap-3 mb-4 cursor-pointer">
              <input
                type="checkbox"
                checked={categoryPrefs.Bills.has_rent || false}
                onChange={(e) => updateCategoryPref('Bills', 'has_rent', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded"
              />
              <span className="font-medium text-gray-800">I pay rent</span>
            </label>

            {categoryPrefs.Bills.has_rent && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Monthly Rent (Rs.)</label>
                <input
                  type="number"
                  min="0"
                  value={categoryPrefs.Bills.rent || 0}
                  onChange={(e) => updateCategoryPref('Bills', 'rent', parseFloat(e.target.value) || 0)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500"
                  placeholder="10000"
                />
              </div>
            )}

            {/* Utilities */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Electricity (Rs.)</label>
                <input
                  type="number"
                  min="0"
                  value={categoryPrefs.Bills.electricity || 0}
                  onChange={(e) => updateCategoryPref('Bills', 'electricity', parseFloat(e.target.value) || 0)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Water (Rs.)</label>
                <input
                  type="number"
                  min="0"
                  value={categoryPrefs.Bills.water || 0}
                  onChange={(e) => updateCategoryPref('Bills', 'water', parseFloat(e.target.value) || 0)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Internet (Rs.)</label>
                <input
                  type="number"
                  min="0"
                  value={categoryPrefs.Bills.internet || 0}
                  onChange={(e) => updateCategoryPref('Bills', 'internet', parseFloat(e.target.value) || 0)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Gas (Rs.)</label>
                <input
                  type="number"
                  min="0"
                  value={categoryPrefs.Bills.gas || 0}
                  onChange={(e) => updateCategoryPref('Bills', 'gas', parseFloat(e.target.value) || 0)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Phone (Rs.)</label>
                <input
                  type="number"
                  min="0"
                  value={categoryPrefs.Bills.phone || 0}
                  onChange={(e) => updateCategoryPref('Bills', 'phone', parseFloat(e.target.value) || 0)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Other Bills (Rs.)</label>
                <input
                  type="number"
                  min="0"
                  value={categoryPrefs.Bills.other_bills || 0}
                  onChange={(e) => updateCategoryPref('Bills', 'other_bills', parseFloat(e.target.value) || 0)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>
          </div>

          <button
            onClick={() => handleSaveCategoryPrefs('Bills')}
            disabled={saving}
            className="w-full py-3 px-6 bg-gradient-to-r from-orange-600 to-red-600 text-white rounded-lg font-semibold hover:from-orange-700 hover:to-red-700 disabled:from-gray-300 disabled:to-gray-300 transition-all flex items-center justify-center gap-2"
          >
            <Save className="w-5 h-5" />
            {saving ? 'Saving...' : 'Save Bills & Rent'}
          </button>
        </div>
      )}
    </div>
  )
}
