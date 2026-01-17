import { useState } from 'react'

const CATEGORIES = [
  {
    id: 'Groceries',
    icon: '🛒',
    title: 'Groceries',
    description: 'Food and daily essentials',
    details: 'Track diet preferences, consumption quantities, and shopping patterns'
  },
  {
    id: 'Transport',
    icon: '🚗',
    title: 'Transport',
    description: 'Commute and travel expenses',
    details: 'Vehicle type, fuel costs, public transport usage, and monthly kilometers'
  },
  {
    id: 'Entertainment',
    icon: '🎬',
    title: 'Entertainment',
    description: 'Subscriptions and activities',
    details: 'Netflix, Spotify, dining out, movies, gym memberships, and hobbies'
  },
  {
    id: 'Bills',
    icon: '🏠',
    title: 'Rent & Bills',
    description: 'Housing and utilities',
    details: 'Rent, electricity, water, internet, gas, phone, and other fixed expenses'
  }
]

export default function CategorySelectionStep({ selected, onNext }) {
  const [selectedCategories, setSelectedCategories] = useState(selected || [])

  const toggleCategory = (categoryId) => {
    if (selectedCategories.includes(categoryId)) {
      setSelectedCategories(selectedCategories.filter((c) => c !== categoryId))
    } else {
      setSelectedCategories([...selectedCategories, categoryId])
    }
  }

  const handleContinue = () => {
    onNext(selectedCategories)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Customize Your Budget Categories
        </h2>
        <p className="text-gray-600">
          Select categories you'd like to configure in detail. You can skip this and configure
          later, but providing information now will give you more accurate AI budget recommendations.
        </p>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
        <div className="flex items-start">
          <span className="text-2xl mr-3">💡</span>
          <div>
            <p className="text-sm font-medium text-blue-800">Why configure categories?</p>
            <p className="text-sm text-blue-700 mt-1">
              The AI uses your detailed preferences (like diet type, vehicle usage) combined with
              real market prices in your city to calculate realistic budgets. The more you share,
              the better your recommendations!
            </p>
          </div>
        </div>
      </div>

      {/* Category Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {CATEGORIES.map((category) => {
          const isSelected = selectedCategories.includes(category.id)

          return (
            <button
              key={category.id}
              onClick={() => toggleCategory(category.id)}
              className={`p-6 border-2 rounded-xl text-left transition transform hover:scale-105 ${
                isSelected
                  ? 'border-purple-600 bg-purple-50 shadow-lg'
                  : 'border-gray-200 bg-white hover:border-purple-300 hover:shadow-md'
              }`}
            >
              {/* Icon and Title */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="text-4xl">{category.icon}</span>
                  <div>
                    <h3 className="font-semibold text-lg text-gray-800">{category.title}</h3>
                    <p className="text-sm text-gray-600">{category.description}</p>
                  </div>
                </div>

                {/* Checkbox */}
                <div
                  className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition ${
                    isSelected
                      ? 'border-purple-600 bg-purple-600'
                      : 'border-gray-300 bg-white'
                  }`}
                >
                  {isSelected && (
                    <svg
                      className="w-4 h-4 text-white"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path d="M5 13l4 4L19 7"></path>
                    </svg>
                  )}
                </div>
              </div>

              {/* Details */}
              <p className="text-sm text-gray-500 mt-2">{category.details}</p>

              {/* Selected Badge */}
              {isSelected && (
                <div className="mt-3 inline-block">
                  <span className="text-xs font-medium px-3 py-1 bg-purple-600 text-white rounded-full">
                    Selected
                  </span>
                </div>
              )}
            </button>
          )
        })}
      </div>

      {/* Selection Summary */}
      {selectedCategories.length > 0 && (
        <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
          <p className="text-sm font-medium text-green-800">
            ✓ {selectedCategories.length} {selectedCategories.length === 1 ? 'category' : 'categories'} selected
          </p>
          <p className="text-sm text-green-700 mt-1">
            You'll provide detailed preferences for: {selectedCategories.join(', ')}
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleContinue}
          className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-purple-700 hover:to-blue-700 transition shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
        >
          {selectedCategories.length > 0 ? (
            <>Continue with Selected Categories</>
          ) : (
            <>Skip for Now</>
          )}
        </button>
      </div>

      {selectedCategories.length === 0 && (
        <p className="text-xs text-gray-500 text-center">
          You can always add category preferences later from your profile settings
        </p>
      )}
    </div>
  )
}
