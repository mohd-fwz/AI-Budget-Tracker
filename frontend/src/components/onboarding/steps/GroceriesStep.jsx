import { useState } from 'react'

export default function GroceriesStep({ data, onNext }) {
  const [formData, setFormData] = useState({
    diet_type: data.diet_type || 'vegetarian',
    consumption_items: data.consumption_items || {
      rice_kg_per_month: 10,
      wheat_kg_per_month: 5,
      vegetables_kg_per_week: 7,
      dairy_liters_per_week: 14,
      // Individual meat types (optional)
      chicken_kg_per_week: 0,
      mutton_kg_per_week: 0,
      fish_kg_per_week: 0,
      eggs_dozen_per_week: 0
    },
    shopping_frequency: data.shopping_frequency || 'weekly'
  })

  const updateConsumption = (field, value) => {
    setFormData({
      ...formData,
      consumption_items: {
        ...formData.consumption_items,
        [field]: parseFloat(value) || 0
      }
    })
  }

  const handleDietChange = (newDietType) => {
    setFormData({
      ...formData,
      diet_type: newDietType,
      // Reset meat consumption if switching to vegetarian/vegan
      consumption_items: {
        ...formData.consumption_items,
        chicken_kg_per_week: newDietType === 'vegetarian' || newDietType === 'vegan' ? 0 : formData.consumption_items.chicken_kg_per_week,
        mutton_kg_per_week: newDietType === 'vegetarian' || newDietType === 'vegan' ? 0 : formData.consumption_items.mutton_kg_per_week,
        fish_kg_per_week: newDietType === 'vegetarian' || newDietType === 'vegan' ? 0 : formData.consumption_items.fish_kg_per_week,
        eggs_dozen_per_week: newDietType === 'vegetarian' || newDietType === 'vegan' ? 0 : formData.consumption_items.eggs_dozen_per_week
      }
    })
  }

  const handleContinue = () => {
    onNext(formData)
  }

  const handleSkip = () => {
    // Skip groceries - useful for students/hostelers who eat at mess/canteen
    onNext({})
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2 flex items-center gap-2">
          <span>🛒</span>
          Groceries Preferences (Optional)
        </h2>
        <p className="text-gray-600">
          Tell us about your food and grocery needs. This helps us calculate realistic monthly budgets based on market prices in your city.
        </p>
        <p className="text-sm text-purple-600 mt-2">
          💡 Students/hostelers: If you eat at mess/canteen, you can skip this step!
        </p>
      </div>

      {/* Diet Type */}
      <div>
        <label className="block font-semibold text-gray-800 mb-3">
          Dietary Preference
        </label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: 'vegetarian', label: 'Vegetarian', icon: '🥗', desc: 'No meat or fish' },
            { value: 'non_vegetarian', label: 'Non-Vegetarian', icon: '🍗', desc: 'Includes meat' },
            { value: 'vegan', label: 'Vegan', icon: '🌱', desc: 'Plant-based only' }
          ].map((diet) => (
            <button
              key={diet.value}
              onClick={() => handleDietChange(diet.value)}
              className={`p-4 border-2 rounded-xl transition transform hover:scale-105 ${
                formData.diet_type === diet.value
                  ? 'border-green-600 bg-green-50 shadow-lg'
                  : 'border-gray-200 bg-white hover:border-green-300'
              }`}
            >
              <div className="text-3xl mb-2">{diet.icon}</div>
              <div className="text-sm font-semibold text-gray-800">{diet.label}</div>
              <div className="text-xs text-gray-600 mt-1">{diet.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Consumption Items */}
      <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200">
        <label className="block font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <span>📊</span>
          Monthly Consumption Estimates
        </label>
        <p className="text-sm text-gray-600 mb-4">
          Approximate quantities your household consumes. Don't worry about exact numbers - rough estimates work great!
        </p>

        <div className="grid grid-cols-2 gap-4">
          {/* Rice */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <span>🍚</span>
              Rice (kg/month)
            </label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={formData.consumption_items.rice_kg_per_month}
              onChange={(e) => updateConsumption('rice_kg_per_month', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
              placeholder="10"
            />
            <p className="text-xs text-gray-500 mt-1">Typical: 5-15 kg for 2-4 people</p>
          </div>

          {/* Wheat/Atta */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <span>🌾</span>
              Wheat/Atta (kg/month)
            </label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={formData.consumption_items.wheat_kg_per_month}
              onChange={(e) => updateConsumption('wheat_kg_per_month', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
              placeholder="5"
            />
            <p className="text-xs text-gray-500 mt-1">Typical: 3-10 kg for 2-4 people</p>
          </div>

          {/* Vegetables */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <span>🥬</span>
              Vegetables (kg/week)
            </label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={formData.consumption_items.vegetables_kg_per_week}
              onChange={(e) => updateConsumption('vegetables_kg_per_week', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
              placeholder="7"
            />
            <p className="text-xs text-gray-500 mt-1">Typical: 5-10 kg per week</p>
          </div>

          {/* Dairy */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <span>🥛</span>
              Dairy (liters/week)
            </label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={formData.consumption_items.dairy_liters_per_week}
              onChange={(e) => updateConsumption('dairy_liters_per_week', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
              placeholder="14"
            />
            <p className="text-xs text-gray-500 mt-1">Milk, curd, etc. Typical: 10-20 liters</p>
          </div>

          {/* Non-Veg Items (only if non-vegetarian) */}
          {formData.diet_type === 'non_vegetarian' && (
            <>
              <div className="col-span-2">
                <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-4 mb-3">
                  <p className="text-sm font-semibold text-orange-800 mb-1 flex items-center gap-2">
                    <span>🍗</span>
                    Non-Vegetarian Items (All Optional)
                  </p>
                  <p className="text-xs text-orange-700">
                    Fill in only what you consume. Leave others at 0 if you don't eat them.
                  </p>
                </div>
              </div>

              {/* Chicken */}
              <div className="bg-white p-4 rounded-lg shadow-sm border-2 border-orange-100">
                <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <span>🍗</span>
                  Chicken (kg/week)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.25"
                  value={formData.consumption_items.chicken_kg_per_week}
                  onChange={(e) => updateConsumption('chicken_kg_per_week', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition"
                  placeholder="0"
                />
                <p className="text-xs text-gray-500 mt-1">Optional: 0.5-2 kg typical</p>
              </div>

              {/* Mutton */}
              <div className="bg-white p-4 rounded-lg shadow-sm border-2 border-orange-100">
                <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <span>🥩</span>
                  Mutton/Lamb (kg/week)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.25"
                  value={formData.consumption_items.mutton_kg_per_week}
                  onChange={(e) => updateConsumption('mutton_kg_per_week', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition"
                  placeholder="0"
                />
                <p className="text-xs text-gray-500 mt-1">Optional: 0.5-1.5 kg typical</p>
              </div>

              {/* Fish */}
              <div className="bg-white p-4 rounded-lg shadow-sm border-2 border-orange-100">
                <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <span>🐟</span>
                  Fish/Seafood (kg/week)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.25"
                  value={formData.consumption_items.fish_kg_per_week}
                  onChange={(e) => updateConsumption('fish_kg_per_week', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition"
                  placeholder="0"
                />
                <p className="text-xs text-gray-500 mt-1">Optional: 0.5-2 kg typical</p>
              </div>

              {/* Eggs */}
              <div className="bg-white p-4 rounded-lg shadow-sm border-2 border-orange-100">
                <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <span>🥚</span>
                  Eggs (dozen/week)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={formData.consumption_items.eggs_dozen_per_week}
                  onChange={(e) => updateConsumption('eggs_dozen_per_week', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition"
                  placeholder="0"
                />
                <p className="text-xs text-gray-500 mt-1">Optional: 1-3 dozen typical</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Shopping Frequency */}
      <div>
        <label className="block font-semibold text-gray-800 mb-3">
          How often do you shop for groceries?
        </label>
        <select
          value={formData.shopping_frequency}
          onChange={(e) => setFormData({ ...formData, shopping_frequency: e.target.value })}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
        >
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="bi_weekly">Bi-weekly (Every 2 weeks)</option>
          <option value="monthly">Monthly</option>
        </select>
        <p className="text-xs text-gray-500 mt-2">
          This helps us understand your shopping patterns and bulk-buying habits
        </p>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
        <div className="flex items-start gap-3">
          <span className="text-xl">💡</span>
          <div className="text-sm text-blue-800">
            <p className="font-medium">How we use this information:</p>
            <p className="mt-1">
              We'll multiply your consumption quantities by current market prices in your city
              (rice, wheat, vegetables, etc.) to calculate a realistic monthly grocery budget.
              Then we'll compare it with your actual spending history!
            </p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleSkip}
          className="flex-1 bg-gray-100 text-gray-700 font-semibold py-4 px-6 rounded-lg hover:bg-gray-200 transition border-2 border-gray-300"
        >
          Skip (I eat at mess/canteen)
        </button>
        <button
          onClick={handleContinue}
          className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-green-700 hover:to-emerald-700 transition shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
        >
          Continue with Details
        </button>
      </div>
    </div>
  )
}
