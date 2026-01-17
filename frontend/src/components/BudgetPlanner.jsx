import { useState, useEffect } from 'react'
import { budgetAPI, profileAPI } from '../services/api'
import { Sparkles, TrendingUp, TrendingDown, Minus, Save, RefreshCw, DollarSign, AlertCircle, MapPin } from 'lucide-react'

export default function BudgetPlanner() {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [recommendations, setRecommendations] = useState(null)
  const [budgets, setBudgets] = useState({})
  const [targetMonth, setTargetMonth] = useState('')
  const [message, setMessage] = useState({ type: '', text: '' })
  const [profile, setProfile] = useState(null)
  const [showComparison, setShowComparison] = useState(false)
  const [comparison, setComparison] = useState(null)

  useEffect(() => {
    // Set default target month to next month
    const nextMonth = new Date()
    nextMonth.setMonth(nextMonth.getMonth() + 1)
    const monthStr = nextMonth.toISOString().slice(0, 7)
    setTargetMonth(monthStr)

    // Load profile
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      const data = await profileAPI.getProfile()
      setProfile(data.profile)
    } catch (error) {
      console.error('Error loading profile:', error)
    }
  }

  const generateRecommendations = async () => {
    if (!targetMonth) {
      setMessage({ type: 'error', text: 'Please select a target month' })
      return
    }

    try {
      setLoading(true)
      setMessage({ type: '', text: '' })

      const data = await budgetAPI.generateRecommendations(targetMonth)
      setRecommendations(data)

      // Initialize budgets with AI recommendations
      const initialBudgets = {}
      data.recommendations.forEach((rec) => {
        initialBudgets[rec.category] = {
          amount: rec.suggested_amount,
          isAiSuggested: true,
          modified: false
        }
      })
      setBudgets(initialBudgets)
    } catch (error) {
      console.error('Error generating recommendations:', error)
      setMessage({ type: 'error', text: 'Failed to generate recommendations' })
    } finally {
      setLoading(false)
    }
  }

  const handleBudgetChange = (category, value) => {
    setBudgets((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        amount: parseFloat(value) || 0,
        modified: true,
        isAiSuggested: false
      }
    }))
  }

  const resetBudget = (category) => {
    const rec = recommendations?.recommendations.find((r) => r.category === category)
    if (rec) {
      setBudgets((prev) => ({
        ...prev,
        [category]: {
          amount: rec.suggested_amount,
          isAiSuggested: true,
          modified: false
        }
      }))
    }
  }

  const saveBudgets = async () => {
    try {
      setSaving(true)
      setMessage({ type: '', text: '' })

      // Convert budgets to API format
      const budgetsArray = Object.entries(budgets).map(([category, data]) => ({
        category,
        amount: data.amount,
        is_ai_suggested: data.isAiSuggested
      }))

      await budgetAPI.saveBudgets(targetMonth, budgetsArray)
      setMessage({ type: 'success', text: 'Budgets saved successfully!' })
    } catch (error) {
      console.error('Error saving budgets:', error)
      setMessage({ type: 'error', text: 'Failed to save budgets' })
    } finally {
      setSaving(false)
    }
  }

  const loadComparison = async () => {
    // Get current month for comparison
    const currentMonth = new Date().toISOString().slice(0, 7)
    try {
      const data = await budgetAPI.compareBudgetVsActual(currentMonth)
      setComparison(data)
      setShowComparison(true)
    } catch (error) {
      console.error('Error loading comparison:', error)
    }
  }

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUp className="w-4 h-4 text-red-500" />
      case 'decreasing':
        return <TrendingDown className="w-4 h-4 text-green-500" />
      default:
        return <Minus className="w-4 h-4 text-gray-500" />
    }
  }

  const getTrendColor = (trend) => {
    switch (trend) {
      case 'increasing':
        return 'text-red-600 bg-red-50'
      case 'decreasing':
        return 'text-green-600 bg-green-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const totalBudget = Object.values(budgets).reduce((sum, b) => sum + b.amount, 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl shadow-lg px-8 py-6 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-white/20 p-3 rounded-lg backdrop-blur-sm">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">AI Budget Planner</h2>
              <p className="text-purple-100 text-sm mt-1">
                Smart recommendations based on your spending patterns
              </p>
            </div>
          </div>
          {profile?.city && (
            <div className="flex items-center gap-2 bg-white/20 px-4 py-2 rounded-lg backdrop-blur-sm">
              <MapPin className="w-4 h-4" />
              <span className="text-sm font-medium">
                {profile.city}, {profile.state}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Location Warning */}
      {!profile?.city && (
        <div className="bg-yellow-50 border-2 border-yellow-200 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-yellow-900">
              <p className="font-semibold mb-1">Location not set</p>
              <p className="text-yellow-800">
                Set your location to get more personalized budget recommendations based on local market trends.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Target Month Selection */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <label className="block text-sm font-semibold text-gray-700 mb-3">
          Budget for Month
        </label>
        <div className="flex gap-4">
          <input
            type="month"
            value={targetMonth}
            onChange={(e) => setTargetMonth(e.target.value)}
            className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
          />
          <button
            onClick={generateRecommendations}
            disabled={loading || !targetMonth}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-pink-700 disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            <Sparkles className="w-5 h-5" />
            {loading ? 'Generating...' : 'Generate AI Recommendations'}
          </button>
        </div>
      </div>

      {/* Recommendations */}
      {recommendations && (
        <div className="space-y-4">
          {/* AI Reasoning Section - NEW */}
          {recommendations.ai_reasoning && recommendations.ai_reasoning.length > 0 && (
            <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6">
              <div className="flex items-start gap-3 mb-4">
                <Sparkles className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-lg font-semibold text-blue-900 mb-2">How AI Planned Your Budget</h3>
                  <div className="space-y-3">
                    {recommendations.ai_reasoning.map((reason, idx) => (
                      <div key={idx} className={`p-3 rounded-lg ${
                        reason.type === 'overspending_warning' ? 'bg-red-100 border border-red-300' :
                        reason.type === 'savings_possible' ? 'bg-green-100 border border-green-300' :
                        reason.type === 'income_constraint' ? 'bg-yellow-100 border border-yellow-300' :
                        'bg-white border border-blue-200'
                      }`}>
                        <p className="text-sm font-medium text-gray-900">{reason.message}</p>
                        {reason.confidence && (
                          <span className={`inline-block mt-2 px-2 py-1 rounded-full text-xs font-medium ${
                            reason.confidence === 'high' ? 'bg-green-200 text-green-800' :
                            reason.confidence === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                            'bg-gray-200 text-gray-800'
                          }`}>
                            {reason.confidence} confidence
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Income History Visualization */}
              {recommendations.income_history && recommendations.income_history.income_by_month && recommendations.income_history.income_by_month.length > 0 && (
                <div className="mt-4 pt-4 border-t border-blue-200">
                  <p className="text-sm font-medium text-blue-900 mb-2">Your Income Trend:</p>
                  <div className="flex items-end gap-2 h-20">
                    {recommendations.income_history.income_by_month.map((month, idx) => (
                      <div key={idx} className="flex-1 flex flex-col items-center">
                        <div
                          className="w-full bg-blue-400 rounded-t transition-all hover:bg-blue-500"
                          style={{
                            height: `${(month.amount / Math.max(...recommendations.income_history.income_by_month.map(m => m.amount))) * 100}%`
                          }}
                          title={`₹${month.amount.toLocaleString()}`}
                        />
                        <p className="text-xs text-gray-600 mt-1">
                          {new Date(month.year, month.month - 1).toLocaleDateString('en-US', { month: 'short' })}
                        </p>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-600 mt-2 text-center">
                    Income is {recommendations.income_history.trend} • Average: ₹{recommendations.income_history.average_income.toLocaleString()}/month
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Summary Card */}
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl shadow-sm p-6 border-2 border-purple-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Budget</p>
                <p className="text-3xl font-bold text-purple-600">₹{recommendations.total_suggested_budget.toLocaleString()}</p>
                {recommendations.budget_adjusted && (
                  <p className="text-xs text-orange-600 mt-1">⚠️ Adjusted to fit income</p>
                )}
              </div>

              {recommendations.predicted_income !== undefined && (
                <>
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      {recommendations.income_method === 'actual_income' ? 'Current Income' : 'Expected Income'}
                    </p>
                    <p className="text-2xl font-bold text-gray-800">₹{recommendations.predicted_income.toLocaleString()}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {recommendations.income_method === 'actual_income' ? 'Already received' :
                       recommendations.income_method === 'historical_average' ? 'Based on history' :
                       recommendations.income_method === 'profile_estimate' ? 'From profile' : 'Estimated'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Savings Potential</p>
                    <p className={`text-2xl font-bold ${recommendations.savings_potential > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ₹{recommendations.savings_potential?.toLocaleString() || 0}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      {recommendations.savings_rate?.toFixed(1)}% of income
                    </p>
                  </div>
                </>
              )}
            </div>

            {recommendations.savings_goal && (
              <div className={`mt-4 p-3 rounded-lg ${recommendations.meets_savings_goal ? 'bg-green-100 border border-green-300' : 'bg-yellow-100 border border-yellow-300'}`}>
                <p className="text-sm font-medium">
                  {recommendations.meets_savings_goal ? '✓' : '⚠'} Savings Goal: ₹{recommendations.savings_goal.toLocaleString()}/month
                </p>
                <p className="text-xs mt-1">
                  {recommendations.meets_savings_goal
                    ? 'You can meet your savings goal with this budget!'
                    : `You need to reduce spending by ₹${Math.abs(recommendations.savings_potential - recommendations.savings_goal).toLocaleString()} to meet your goal`}
                </p>
              </div>
            )}

            <p className="text-sm text-gray-700 mt-4">
              Based on {recommendations.analysis_period} months of spending
              {recommendations.location && ` in ${recommendations.location.city}`}
            </p>
          </div>

          {/* Category Budgets */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Category Budgets</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {recommendations.recommendations.map((rec) => (
                <div key={rec.category} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-gray-900">{rec.category}</h4>
                        {rec.confidence && (
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            rec.confidence === 'high' ? 'bg-green-100 text-green-700' :
                            rec.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {rec.confidence} confidence
                          </span>
                        )}
                      </div>
                      {rec.reasoning && (
                        <div className="text-sm text-gray-600 mt-2 whitespace-pre-line">
                          {rec.reasoning}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <label className="block text-xs font-medium text-gray-600 mb-2">
                        Monthly Budget (Rs.)
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="number"
                          value={budgets[rec.category]?.amount || 0}
                          onChange={(e) => handleBudgetChange(rec.category, e.target.value)}
                          step="100"
                          min="0"
                          className={`flex-1 px-4 py-2 border-2 rounded-lg focus:ring-2 focus:ring-purple-500 ${
                            budgets[rec.category]?.modified
                              ? 'border-orange-300 bg-orange-50'
                              : 'border-gray-200'
                          }`}
                        />
                        {budgets[rec.category]?.modified && (
                          <button
                            onClick={() => resetBudget(rec.category)}
                            className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                            title="Reset to AI suggestion"
                          >
                            <RefreshCw className="w-4 h-4 text-gray-600" />
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="text-right">
                      <p className="text-xs text-gray-600">AI Suggested</p>
                      <p className="text-lg font-bold text-purple-600">
                        Rs.{rec.suggested_amount.toFixed(2)}
                      </p>
                      {rec.breakdown && Object.keys(rec.breakdown).length > 0 && (
                        <div className="mt-2 text-xs text-gray-500">
                          <details className="cursor-pointer">
                            <summary className="hover:text-purple-600">View breakdown</summary>
                            <div className="mt-1 space-y-1">
                              {Object.entries(rec.breakdown).map(([key, value]) => (
                                <div key={key} className="flex justify-between">
                                  <span className="capitalize">{key.replace('_', ' ')}:</span>
                                  <span>₹{value}</span>
                                </div>
                              ))}
                            </div>
                          </details>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Comparison with historical */}
                  {rec.comparison_with_actual && (
                    <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="text-sm text-blue-900">{rec.comparison_with_actual}</p>
                    </div>
                  )}
                </div>
              ))}
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
              {message.type === 'success' ? (
                <Save className="w-5 h-5 text-green-500 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              )}
              <span className="font-medium">{message.text}</span>
            </div>
          )}

          {/* Save Button */}
          <button
            onClick={saveBudgets}
            disabled={saving}
            className="w-full py-4 px-6 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-pink-700 disabled:from-gray-300 disabled:to-gray-300 transition-all flex items-center justify-center gap-2"
          >
            <Save className="w-5 h-5" />
            {saving ? 'Saving...' : 'Save Budget Plan'}
          </button>
        </div>
      )}

      {/* Empty State */}
      {!recommendations && !loading && (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-8 h-8 text-purple-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Ready to plan your budget?
          </h3>
          <p className="text-gray-600 mb-6">
            Select a month and generate AI-powered budget recommendations based on your spending history.
          </p>
        </div>
      )}
    </div>
  )
}
