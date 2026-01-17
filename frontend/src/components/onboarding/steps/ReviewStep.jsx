import { useState } from 'react'

export default function ReviewStep({ data, selectedCategories, onSubmit }) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    setSaving(true)
    setError('')

    try {
      await onSubmit()
    } catch (err) {
      console.error('Failed to save preferences:', err)
      setError('Failed to save your preferences. Please try again.')
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Review Your Preferences</h2>
        <p className="text-gray-600">
          Please review your information before completing setup. You can always update these later from your profile settings.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Basic Info Summary */}
      <div className="bg-gradient-to-br from-purple-50 to-blue-50 p-6 rounded-xl border border-purple-200">
        <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <span>👤</span>
          Basic Information
        </h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="bg-white p-3 rounded-lg">
            <span className="text-gray-600 block text-xs mb-1">Location</span>
            <span className="font-medium text-gray-800">
              {data.basicInfo.city}, {data.basicInfo.state}
            </span>
          </div>

          <div className="bg-white p-3 rounded-lg">
            <span className="text-gray-600 block text-xs mb-1">Family Size</span>
            <span className="font-medium text-gray-800">
              {data.basicInfo.family_size} {data.basicInfo.family_size === 1 ? 'person' : 'people'}
            </span>
          </div>

          {data.basicInfo.monthly_income && (
            <div className="bg-white p-3 rounded-lg">
              <span className="text-gray-600 block text-xs mb-1">Monthly Income</span>
              <span className="font-medium text-gray-800">₹{parseFloat(data.basicInfo.monthly_income).toLocaleString()}</span>
            </div>
          )}

          {data.basicInfo.savings_goal && (
            <div className="bg-white p-3 rounded-lg">
              <span className="text-gray-600 block text-xs mb-1">Savings Goal</span>
              <span className="font-medium text-gray-800">₹{parseFloat(data.basicInfo.savings_goal).toLocaleString()}/month</span>
            </div>
          )}

          {data.basicInfo.age_group && (
            <div className="bg-white p-3 rounded-lg">
              <span className="text-gray-600 block text-xs mb-1">Age Group</span>
              <span className="font-medium text-gray-800">{data.basicInfo.age_group} years</span>
            </div>
          )}

          {data.basicInfo.occupation && (
            <div className="bg-white p-3 rounded-lg">
              <span className="text-gray-600 block text-xs mb-1">Occupation</span>
              <span className="font-medium text-gray-800">{data.basicInfo.occupation}</span>
            </div>
          )}
        </div>
      </div>

      {/* Groceries Summary */}
      {selectedCategories.includes('Groceries') && data.groceries && Object.keys(data.groceries).length > 0 && (
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span>🛒</span>
            Groceries Preferences
          </h3>
          <div className="space-y-3">
            <div className="bg-white p-3 rounded-lg">
              <span className="text-gray-600 text-xs block mb-1">Dietary Preference</span>
              <span className="font-medium text-gray-800 capitalize">
                {data.groceries.diet_type?.replace('_', ' ')}
              </span>
            </div>

            <div className="bg-white p-3 rounded-lg">
              <span className="text-gray-600 text-xs block mb-1">Shopping Frequency</span>
              <span className="font-medium text-gray-800 capitalize">
                {data.groceries.shopping_frequency?.replace('_', ' ')}
              </span>
            </div>

            {data.groceries.consumption_items && (
              <div className="bg-white p-3 rounded-lg">
                <span className="text-gray-600 text-xs block mb-2">Monthly Consumption</span>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {data.groceries.consumption_items.rice_kg_per_month > 0 && (
                    <div>
                      <span className="text-gray-600">Rice:</span>
                      <span className="ml-2 font-medium">{data.groceries.consumption_items.rice_kg_per_month} kg/month</span>
                    </div>
                  )}
                  {data.groceries.consumption_items.wheat_kg_per_month > 0 && (
                    <div>
                      <span className="text-gray-600">Wheat:</span>
                      <span className="ml-2 font-medium">{data.groceries.consumption_items.wheat_kg_per_month} kg/month</span>
                    </div>
                  )}
                  {data.groceries.consumption_items.vegetables_kg_per_week > 0 && (
                    <div>
                      <span className="text-gray-600">Vegetables:</span>
                      <span className="ml-2 font-medium">{data.groceries.consumption_items.vegetables_kg_per_week} kg/week</span>
                    </div>
                  )}
                  {data.groceries.consumption_items.dairy_liters_per_week > 0 && (
                    <div>
                      <span className="text-gray-600">Dairy:</span>
                      <span className="ml-2 font-medium">{data.groceries.consumption_items.dairy_liters_per_week} L/week</span>
                    </div>
                  )}
                  {data.groceries.consumption_items.meat_kg_per_week > 0 && (
                    <div>
                      <span className="text-gray-600">Meat/Fish:</span>
                      <span className="ml-2 font-medium">{data.groceries.consumption_items.meat_kg_per_week} kg/week</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Transport Summary */}
      {selectedCategories.includes('Transport') && data.transport && Object.keys(data.transport).length > 0 && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span>🚗</span>
            Transport Preferences
          </h3>
          <div className="space-y-3">
            <div className="bg-white p-3 rounded-lg">
              <span className="text-gray-600 text-xs block mb-1">Primary Mode</span>
              <span className="font-medium text-gray-800 capitalize">
                {data.transport.mode?.replace('_', ' ')}
              </span>
            </div>

            {(data.transport.mode === 'own_vehicle' || data.transport.mode === 'mixed') && (
              <div className="bg-white p-3 rounded-lg">
                <span className="text-gray-600 text-xs block mb-2">Personal Vehicle</span>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">Type:</span>
                    <span className="ml-2 font-medium capitalize">{data.transport.vehicle_type}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Fuel:</span>
                    <span className="ml-2 font-medium capitalize">{data.transport.fuel_type}</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-gray-600">Monthly Distance:</span>
                    <span className="ml-2 font-medium">{data.transport.avg_km_per_month} km</span>
                  </div>
                </div>
              </div>
            )}

            {(data.transport.mode === 'public_transport' || data.transport.mode === 'mixed') && (
              <div className="bg-white p-3 rounded-lg">
                <span className="text-gray-600 text-xs block mb-2">Public Transport</span>
                <div className="space-y-1 text-sm">
                  {data.transport.public_transport?.uses_metro && (
                    <div>
                      <span className="text-gray-600">Metro:</span>
                      <span className="ml-2 font-medium">
                        ₹{data.transport.public_transport.metro_monthly_cost}/month
                      </span>
                    </div>
                  )}
                  {data.transport.public_transport?.uses_bus && (
                    <div>
                      <span className="text-gray-600">Bus:</span>
                      <span className="ml-2 font-medium">
                        ₹{data.transport.public_transport.bus_monthly_cost}/month
                      </span>
                    </div>
                  )}
                  {!data.transport.public_transport?.uses_metro && !data.transport.public_transport?.uses_bus && (
                    <span className="text-gray-500 italic">Not configured</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Entertainment Summary */}
      {selectedCategories.includes('Entertainment') && data.entertainment && Object.keys(data.entertainment).length > 0 && (
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-xl border border-purple-200">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span>🎬</span>
            Entertainment Preferences
          </h3>
          <div className="space-y-3">
            {data.entertainment.subscriptions && data.entertainment.subscriptions.length > 0 && (
              <div className="bg-white p-3 rounded-lg">
                <span className="text-gray-600 text-xs block mb-2">Subscriptions</span>
                <div className="flex flex-wrap gap-2">
                  {data.entertainment.subscriptions.map(sub => (
                    <span key={sub} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium capitalize">
                      {sub.replace('_', ' ')}
                    </span>
                  ))}
                </div>
                {data.entertainment.estimated_subscription_cost > 0 && (
                  <p className="text-sm text-gray-600 mt-2">
                    Estimated: ₹{data.entertainment.estimated_subscription_cost}/month
                  </p>
                )}
              </div>
            )}

            {data.entertainment.activities && Object.keys(data.entertainment.activities).some(k => data.entertainment.activities[k]) && (
              <div className="bg-white p-3 rounded-lg">
                <span className="text-gray-600 text-xs block mb-2">Activities</span>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(data.entertainment.activities).map(([key, enabled]) =>
                    enabled && (
                      <span key={key} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium capitalize">
                        {key.replace('_', ' ')}
                      </span>
                    )
                  )}
                </div>
              </div>
            )}

            {data.entertainment.monthly_entertainment_budget > 0 && (
              <div className="bg-white p-3 rounded-lg">
                <span className="text-gray-600 text-xs block mb-1">Monthly Budget</span>
                <span className="font-medium text-gray-800">₹{data.entertainment.monthly_entertainment_budget.toLocaleString()}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Bills Summary */}
      {selectedCategories.includes('Bills') && data.bills && Object.keys(data.bills).length > 0 && (
        <div className="bg-gradient-to-br from-orange-50 to-red-50 p-6 rounded-xl border border-orange-200">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span>🏠</span>
            Rent & Bills
          </h3>
          <div className="space-y-3">
            <div className="bg-white p-3 rounded-lg">
              <span className="text-gray-600 text-xs block mb-2">Monthly Expenses</span>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {data.bills.has_rent && data.bills.rent > 0 && (
                  <div>
                    <span className="text-gray-600">Rent:</span>
                    <span className="ml-2 font-medium">₹{data.bills.rent.toLocaleString()}</span>
                  </div>
                )}
                {data.bills.electricity > 0 && (
                  <div>
                    <span className="text-gray-600">Electricity:</span>
                    <span className="ml-2 font-medium">₹{data.bills.electricity.toLocaleString()}</span>
                  </div>
                )}
                {data.bills.water > 0 && (
                  <div>
                    <span className="text-gray-600">Water:</span>
                    <span className="ml-2 font-medium">₹{data.bills.water.toLocaleString()}</span>
                  </div>
                )}
                {data.bills.internet > 0 && (
                  <div>
                    <span className="text-gray-600">Internet:</span>
                    <span className="ml-2 font-medium">₹{data.bills.internet.toLocaleString()}</span>
                  </div>
                )}
                {data.bills.gas > 0 && (
                  <div>
                    <span className="text-gray-600">Gas:</span>
                    <span className="ml-2 font-medium">₹{data.bills.gas.toLocaleString()}</span>
                  </div>
                )}
                {data.bills.phone > 0 && (
                  <div>
                    <span className="text-gray-600">Phone:</span>
                    <span className="ml-2 font-medium">₹{data.bills.phone.toLocaleString()}</span>
                  </div>
                )}
                {data.bills.other_bills > 0 && (
                  <div>
                    <span className="text-gray-600">Other:</span>
                    <span className="ml-2 font-medium">₹{data.bills.other_bills.toLocaleString()}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* No Categories Selected Message */}
      {selectedCategories.length === 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
          <p className="text-sm text-yellow-800">
            You didn't configure any categories. You can add them later from your profile settings to get personalized AI budget recommendations.
          </p>
        </div>
      )}

      {/* Success Message */}
      <div className="bg-gradient-to-r from-purple-100 to-blue-100 p-6 rounded-xl border border-purple-300">
        <div className="flex items-start gap-3">
          <span className="text-3xl">🎉</span>
          <div>
            <h4 className="font-semibold text-gray-800 mb-1">You're all set!</h4>
            <p className="text-sm text-gray-700">
              Click "Complete Setup" to start using Budget Planner. Our AI will use your preferences and local market prices to create personalized budget recommendations.
            </p>
          </div>
        </div>
      </div>

      {/* Complete Button */}
      <button
        onClick={handleSubmit}
        disabled={saving}
        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-purple-700 hover:to-blue-700 transition shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
      >
        {saving ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Saving Your Preferences...
          </span>
        ) : (
          'Complete Setup'
        )}
      </button>

      <p className="text-xs text-gray-500 text-center">
        You can update all of these preferences anytime from your profile settings
      </p>
    </div>
  )
}
