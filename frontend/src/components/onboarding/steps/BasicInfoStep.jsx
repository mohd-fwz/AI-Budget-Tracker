import { useState, useEffect } from 'react'
import { profileAPI } from '../../../services/api'

export default function BasicInfoStep({ data, onNext }) {
  const [formData, setFormData] = useState({
    state: data.state || '',
    city: data.city || '',
    monthly_income: data.monthly_income || '',
    family_size: data.family_size || 1,
    age_group: data.age_group || '',
    savings_goal: data.savings_goal || '',
    occupation: data.occupation || ''
  })

  const [states, setStates] = useState([])
  const [cities, setCities] = useState([])
  const [loadingCities, setLoadingCities] = useState(false)
  const [error, setError] = useState('')

  // Load states on mount
  useEffect(() => {
    const loadStates = async () => {
      try {
        const response = await profileAPI.getStates()
        setStates(response.states || [])
      } catch (error) {
        console.error('Failed to load states:', error)
        setError('Failed to load states. Please refresh the page.')
      }
    }
    loadStates()
  }, [])

  // Load cities when state changes
  useEffect(() => {
    const loadCities = async () => {
      if (!formData.state) {
        setCities([])
        return
      }

      setLoadingCities(true)
      try {
        const response = await profileAPI.getCities(formData.state)
        setCities(response.cities || [])
      } catch (error) {
        console.error('Failed to load cities:', error)
        setCities([])
      } finally {
        setLoadingCities(false)
      }
    }
    loadCities()
  }, [formData.state])

  const handleStateChange = (e) => {
    setFormData({
      ...formData,
      state: e.target.value,
      city: '' // Reset city when state changes
    })
  }

  const handleNext = () => {
    // Validate required fields
    if (!formData.state || !formData.city) {
      setError('Please select your state and city')
      return
    }

    if (!formData.family_size || formData.family_size < 1) {
      setError('Please enter a valid family size')
      return
    }

    setError('')
    onNext(formData)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Let's start with the basics</h2>
        <p className="text-gray-600">
          This information helps us provide personalized budget recommendations
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Location Section */}
      <div className="bg-purple-50 p-6 rounded-xl space-y-4">
        <h3 className="font-semibold text-gray-800 flex items-center gap-2">
          <span>📍</span>
          Location (Required)
        </h3>

        <div className="grid grid-cols-2 gap-4">
          {/* State Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              State *
            </label>
            <select
              value={formData.state}
              onChange={handleStateChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              required
            >
              <option value="">Select State</option>
              {states.map((state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
          </div>

          {/* City Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              City *
            </label>
            <select
              value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              disabled={!formData.state || loadingCities}
              required
            >
              <option value="">
                {loadingCities ? 'Loading cities...' : 'Select City'}
              </option>
              {cities.map((city) => (
                <option key={city} value={city}>
                  {city}
                </option>
              ))}
            </select>
          </div>
        </div>

        <p className="text-xs text-gray-500">
          We use your location to provide cost-of-living adjusted budget recommendations
        </p>
      </div>

      {/* Family Information */}
      <div className="bg-blue-50 p-6 rounded-xl space-y-4">
        <h3 className="font-semibold text-gray-800 flex items-center gap-2">
          <span>👨‍👩‍👧‍👦</span>
          Family Information
        </h3>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Family Size *
          </label>
          <input
            type="number"
            min="1"
            max="20"
            value={formData.family_size}
            onChange={(e) => setFormData({ ...formData, family_size: parseInt(e.target.value) || 1 })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            placeholder="Number of people in your household"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Including yourself and all dependents
          </p>
        </div>
      </div>

      {/* Financial Information (Optional) */}
      <div className="bg-green-50 p-6 rounded-xl space-y-4">
        <h3 className="font-semibold text-gray-800 flex items-center gap-2">
          <span>💰</span>
          Financial Information (Optional)
        </h3>

        <div className="grid grid-cols-2 gap-4">
          {/* Monthly Income */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Monthly Income
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
              <input
                type="number"
                min="0"
                step="1000"
                value={formData.monthly_income}
                onChange={(e) => setFormData({ ...formData, monthly_income: e.target.value })}
                className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
                placeholder="50,000"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Helps calculate savings potential
            </p>
          </div>

          {/* Savings Goal */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Monthly Savings Goal
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
              <input
                type="number"
                min="0"
                step="1000"
                value={formData.savings_goal}
                onChange={(e) => setFormData({ ...formData, savings_goal: e.target.value })}
                className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
                placeholder="10,000"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Target amount to save each month
            </p>
          </div>
        </div>

        {/* Age Group */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Age Group
          </label>
          <select
            value={formData.age_group}
            onChange={(e) => setFormData({ ...formData, age_group: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
          >
            <option value="">Select Age Group</option>
            <option value="18-25">18-25</option>
            <option value="26-35">26-35</option>
            <option value="36-50">36-50</option>
            <option value="50+">50+</option>
          </select>
        </div>

        {/* Occupation */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Occupation
          </label>
          <input
            type="text"
            value={formData.occupation}
            onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
            placeholder="Software Engineer, Teacher, Student, etc."
          />
        </div>
      </div>

      {/* Continue Button */}
      <button
        onClick={handleNext}
        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-purple-700 hover:to-blue-700 transition shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
      >
        Continue
      </button>

      <p className="text-xs text-gray-500 text-center">
        * Required fields
      </p>
    </div>
  )
}
