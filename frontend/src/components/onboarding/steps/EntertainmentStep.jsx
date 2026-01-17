import { useState } from 'react'

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

export default function EntertainmentStep({ data, onNext }) {
  const [formData, setFormData] = useState({
    subscriptions: data.subscriptions || [],
    activities: data.activities || {},
    custom_activities: data.custom_activities || [],
    monthly_entertainment_budget: data.monthly_entertainment_budget || 0
  })

  const [customActivity, setCustomActivity] = useState('')

  const toggleSubscription = (serviceId) => {
    if (formData.subscriptions.includes(serviceId)) {
      setFormData({
        ...formData,
        subscriptions: formData.subscriptions.filter(s => s !== serviceId)
      })
    } else {
      setFormData({
        ...formData,
        subscriptions: [...formData.subscriptions, serviceId]
      })
    }
  }

  const updateActivity = (activityId, enabled) => {
    setFormData({
      ...formData,
      activities: {
        ...formData.activities,
        [activityId]: enabled
      }
    })
  }

  const addCustomActivity = () => {
    if (!customActivity.trim()) return

    const activityId = customActivity.toLowerCase().replace(/[^a-z0-9]/g, '_')

    // Check if activity already exists
    const exists = formData.custom_activities.some(a => a.id === activityId)
    if (exists) return

    const newActivity = {
      id: activityId,
      name: customActivity.trim(),
      icon: '🎯', // Default icon for custom activities
      custom: true
    }

    // Add to custom activities list
    const updatedCustomActivities = [...formData.custom_activities, newActivity]

    // Automatically select the new activity
    const updatedActivities = {
      ...formData.activities,
      [activityId]: true
    }

    setFormData({
      ...formData,
      custom_activities: updatedCustomActivities,
      activities: updatedActivities
    })

    setCustomActivity('')
  }

  const removeCustomActivity = (activityId) => {
    // Remove from custom activities list
    const updatedCustomActivities = formData.custom_activities.filter(a => a.id !== activityId)

    // Remove from selected activities
    const updatedActivities = { ...formData.activities }
    delete updatedActivities[activityId]

    setFormData({
      ...formData,
      custom_activities: updatedCustomActivities,
      activities: updatedActivities
    })
  }

  const handleContinue = () => {
    // Calculate estimated cost from subscriptions
    const subscriptionCost = formData.subscriptions.reduce((sum, serviceId) => {
      const service = STREAMING_SERVICES.find(s => s.id === serviceId)
      return sum + (service?.typical_cost || 0)
    }, 0)

    onNext({
      ...formData,
      estimated_subscription_cost: subscriptionCost
    })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2 flex items-center gap-2">
          <span>🎬</span>
          Entertainment Preferences
        </h2>
        <p className="text-gray-600">
          Help us understand your entertainment expenses like subscriptions and activities.
        </p>
      </div>

      {/* Streaming Subscriptions */}
      <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-xl border border-purple-200">
        <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <span>📺</span>
          Streaming Subscriptions
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Select the subscriptions you currently have
        </p>

        <div className="grid grid-cols-2 gap-3">
          {STREAMING_SERVICES.map((service) => {
            const isSelected = formData.subscriptions.includes(service.id)

            return (
              <button
                key={service.id}
                onClick={() => toggleSubscription(service.id)}
                className={`p-4 rounded-lg border-2 transition transform hover:scale-105 text-left ${
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

        {formData.subscriptions.length > 0 && (
          <div className="mt-4 p-3 bg-white rounded-lg border border-purple-200">
            <p className="text-sm font-medium text-gray-700">
              Estimated Subscription Cost:{' '}
              <span className="text-purple-600">
                ₹{formData.subscriptions.reduce((sum, serviceId) => {
                  const service = STREAMING_SERVICES.find(s => s.id === serviceId)
                  return sum + (service?.typical_cost || 0)
                }, 0)}/month
              </span>
            </p>
          </div>
        )}
      </div>

      {/* Other Activities */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
        <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <span>🎯</span>
          Entertainment Activities
        </h3>

        {/* Default Activities */}
        <div className="space-y-3 mb-4">
          <p className="text-xs font-medium text-gray-600 mb-2 uppercase">Popular Activities</p>
          {DEFAULT_ACTIVITY_TYPES.map((activity) => (
            <label
              key={activity.id}
              className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200 cursor-pointer hover:border-blue-300 transition"
            >
              <input
                type="checkbox"
                checked={formData.activities[activity.id] || false}
                onChange={(e) => updateActivity(activity.id, e.target.checked)}
                className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
              />
              <span className="text-2xl">{activity.icon}</span>
              <span className="font-medium text-gray-800">{activity.name}</span>
            </label>
          ))}
        </div>

        {/* Custom Activities - Selected */}
        {formData.custom_activities.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-purple-600 mb-2 uppercase">Your Custom Activities</p>
            <div className="space-y-2">
              {formData.custom_activities.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg border-2 border-purple-200"
                >
                  <input
                    type="checkbox"
                    checked={formData.activities[activity.id] || false}
                    onChange={(e) => updateActivity(activity.id, e.target.checked)}
                    className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                  />
                  <span className="text-2xl">{activity.icon}</span>
                  <span className="font-medium text-gray-800 flex-1">{activity.name}</span>
                  <button
                    onClick={() => removeCustomActivity(activity.id)}
                    className="text-red-500 hover:text-red-700 text-sm font-medium px-2 py-1 rounded hover:bg-red-50 transition"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Add Custom Activity */}
      <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-xl border-2 border-dashed border-purple-300">
        <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
          <span>✨</span>
          Add Your Own Activity
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Add custom activities like Paintball, Rock Climbing, Ice Skating, etc.
        </p>

        <div className="flex gap-2">
          <input
            type="text"
            value={customActivity}
            onChange={(e) => setCustomActivity(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addCustomActivity()}
            placeholder="e.g., Paintball, Ice Skating, Trampoline Park..."
            className="flex-1 px-4 py-3 border-2 border-purple-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-400 transition"
          />
          <button
            onClick={addCustomActivity}
            disabled={!customActivity.trim()}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Add
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          💡 Custom activities will appear above with a purple highlight
        </p>
      </div>

      {/* Optional Budget Input */}
      <div className="bg-green-50 p-6 rounded-xl border border-green-200">
        <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <span>💰</span>
          Monthly Entertainment Budget (Optional)
        </h3>
        <p className="text-sm text-gray-600 mb-3">
          If you have a specific budget in mind for entertainment
        </p>
        <div className="relative">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
          <input
            type="number"
            min="0"
            step="500"
            value={formData.monthly_entertainment_budget}
            onChange={(e) => setFormData({
              ...formData,
              monthly_entertainment_budget: parseInt(e.target.value) || 0
            })}
            className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
            placeholder="2000"
          />
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Leave as 0 to calculate based on your actual spending
        </p>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
        <div className="flex items-start gap-3">
          <span className="text-xl">💡</span>
          <div className="text-sm text-blue-800">
            <p className="font-medium">How we use this:</p>
            <p className="mt-1">
              We'll factor in your subscription costs and typical spending on activities
              to create a realistic entertainment budget that aligns with your lifestyle.
            </p>
          </div>
        </div>
      </div>

      {/* Continue Button */}
      <button
        onClick={handleContinue}
        className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
      >
        Continue
      </button>
    </div>
  )
}
