import { useState } from 'react'

/**
 * Date Range Picker Component
 * Allows users to select a date range from suggested options or custom dates
 */
export default function DateRangePicker({ dateRange, onSelect, onCancel, loading = false }) {
  const [selectedRangeIndex, setSelectedRangeIndex] = useState(0)
  const [customMode, setCustomMode] = useState(false)
  const [customStart, setCustomStart] = useState('')
  const [customEnd, setCustomEnd] = useState('')

  const handleQuickSelect = (index) => {
    setSelectedRangeIndex(index)
    setCustomMode(false)
  }

  const handleCustomMode = () => {
    setCustomMode(true)
    setCustomStart(dateRange.min_date)
    setCustomEnd(dateRange.max_date)
  }

  const handleSubmit = () => {
    if (customMode) {
      if (customStart && customEnd) {
        onSelect(customStart, customEnd)
      }
    } else {
      const selected = dateRange.suggested_ranges[selectedRangeIndex]
      onSelect(selected.start_date, selected.end_date)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl w-full">
      {/* Header */}
      <div className="flex items-center mb-6">
        <svg
          className="w-8 h-8 text-blue-500 mr-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <div>
          <h3 className="text-xl font-semibold text-gray-900">Select Date Range</h3>
          <p className="text-sm text-gray-600">
            Full range: {dateRange.min_date} to {dateRange.max_date} ({dateRange.total_days} days)
          </p>
        </div>
      </div>

      {/* Quick Select Options */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Suggested Ranges</h4>
        <div className="space-y-2">
          {dateRange.suggested_ranges.map((range, index) => (
            <button
              key={index}
              onClick={() => handleQuickSelect(index)}
              className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                selectedRangeIndex === index && !customMode
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <div className="flex justify-between items-center">
                <div>
                  <div className="font-medium text-gray-900">{range.label}</div>
                  <div className="text-sm text-gray-600">
                    {range.start_date} to {range.end_date}
                  </div>
                </div>
                <div className="text-sm text-gray-500">{range.days} days</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Custom Range */}
      <div className="mb-6">
        <button
          onClick={handleCustomMode}
          className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
            customMode
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300 bg-white'
          }`}
        >
          <div className="font-medium text-gray-900 mb-2">Custom Range</div>
          {customMode && (
            <div className="grid grid-cols-2 gap-4 mt-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <input
                  type="date"
                  value={customStart}
                  onChange={(e) => setCustomStart(e.target.value)}
                  min={dateRange.min_date}
                  max={dateRange.max_date}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  value={customEnd}
                  onChange={(e) => setCustomEnd(e.target.value)}
                  min={dateRange.min_date}
                  max={dateRange.max_date}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}
        </button>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={onCancel}
          disabled={loading}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={loading || (customMode && (!customStart || !customEnd))}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>Processing...</span>
            </>
          ) : (
            'Apply Filter'
          )}
        </button>
      </div>
    </div>
  )
}
