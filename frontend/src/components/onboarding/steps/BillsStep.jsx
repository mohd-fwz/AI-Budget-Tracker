import { useState } from 'react'

export default function BillsStep({ data, onNext }) {
  const [formData, setFormData] = useState({
    rent: data.rent || 0,
    electricity: data.electricity || 0,
    water: data.water || 0,
    internet: data.internet || 0,
    gas: data.gas || 0,
    phone: data.phone || 0,
    other_bills: data.other_bills || 0,
    has_rent: data.has_rent !== undefined ? data.has_rent : false
  })

  const handleContinue = () => {
    onNext(formData)
  }

  const calculateTotal = () => {
    return (formData.has_rent ? formData.rent : 0) +
      formData.electricity +
      formData.water +
      formData.internet +
      formData.gas +
      formData.phone +
      formData.other_bills
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2 flex items-center gap-2">
          <span>🏠</span>
          Rent & Bills
        </h2>
        <p className="text-gray-600">
          Tell us about your monthly fixed expenses for housing and utilities.
        </p>
      </div>

      {/* Rent */}
      <div className="bg-gradient-to-br from-orange-50 to-red-50 p-6 rounded-xl border border-orange-200">
        <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <span>🏡</span>
          Rent/Housing
        </h3>

        <label className="flex items-center gap-3 mb-4 cursor-pointer">
          <input
            type="checkbox"
            checked={formData.has_rent}
            onChange={(e) => setFormData({ ...formData, has_rent: e.target.checked })}
            className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
          />
          <span className="font-medium text-gray-800">I pay rent</span>
        </label>

        {formData.has_rent && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Monthly Rent
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
              <input
                type="number"
                min="0"
                step="1000"
                value={formData.rent}
                onChange={(e) => setFormData({ ...formData, rent: parseInt(e.target.value) || 0 })}
                className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition"
                placeholder="10000"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Typical rent: ₹5,000-50,000 depending on city and property
            </p>
          </div>
        )}
      </div>

      {/* Utilities */}
      <div className="bg-gradient-to-br from-green-50 to-teal-50 p-6 rounded-xl border border-green-200">
        <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <span>⚡</span>
          Utilities & Services
        </h3>

        <div className="grid grid-cols-2 gap-4">
          {/* Electricity */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <span>💡</span>
              Electricity
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">₹</span>
              <input
                type="number"
                min="0"
                step="100"
                value={formData.electricity}
                onChange={(e) => setFormData({ ...formData, electricity: parseInt(e.target.value) || 0 })}
                className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
                placeholder="1000"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Typical: ₹500-3000</p>
          </div>

          {/* Water */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <span>💧</span>
              Water
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">₹</span>
              <input
                type="number"
                min="0"
                step="50"
                value={formData.water}
                onChange={(e) => setFormData({ ...formData, water: parseInt(e.target.value) || 0 })}
                className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
                placeholder="200"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Typical: ₹100-500</p>
          </div>

          {/* Internet */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <span>📡</span>
              Internet/WiFi
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">₹</span>
              <input
                type="number"
                min="0"
                step="100"
                value={formData.internet}
                onChange={(e) => setFormData({ ...formData, internet: parseInt(e.target.value) || 0 })}
                className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
                placeholder="600"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Typical: ₹400-1500</p>
          </div>

          {/* Gas */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <span>🔥</span>
              Gas/LPG
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">₹</span>
              <input
                type="number"
                min="0"
                step="100"
                value={formData.gas}
                onChange={(e) => setFormData({ ...formData, gas: parseInt(e.target.value) || 0 })}
                className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
                placeholder="300"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Typical: ₹200-800</p>
          </div>

          {/* Phone */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <span>📱</span>
              Mobile/Phone
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">₹</span>
              <input
                type="number"
                min="0"
                step="50"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: parseInt(e.target.value) || 0 })}
                className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
                placeholder="300"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Typical: ₹200-1000</p>
          </div>

          {/* Other Bills */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <span>📄</span>
              Other Bills
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">₹</span>
              <input
                type="number"
                min="0"
                step="100"
                value={formData.other_bills}
                onChange={(e) => setFormData({ ...formData, other_bills: parseInt(e.target.value) || 0 })}
                className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
                placeholder="500"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Society fees, etc.</p>
          </div>
        </div>
      </div>

      {/* Total Summary */}
      {calculateTotal() > 0 && (
        <div className="bg-gradient-to-r from-blue-100 to-purple-100 p-6 rounded-xl border border-blue-300">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">Total Monthly Bills</p>
              <p className="text-xs text-gray-600 mt-1">
                {formData.has_rent ? 'Including rent' : 'Excluding rent'}
              </p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-purple-600">
                ₹{calculateTotal().toLocaleString()}
              </p>
              <p className="text-xs text-gray-600 mt-1">per month</p>
            </div>
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
        <div className="flex items-start gap-3">
          <span className="text-xl">💡</span>
          <div className="text-sm text-blue-800">
            <p className="font-medium">Why we collect this:</p>
            <p className="mt-1">
              Fixed bills are predictable expenses. Knowing these helps us create accurate
              budgets and identify where you can potentially save money.
            </p>
          </div>
        </div>
      </div>

      {/* Continue Button */}
      <button
        onClick={handleContinue}
        className="w-full bg-gradient-to-r from-green-600 to-teal-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-green-700 hover:to-teal-700 transition shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
      >
        Continue
      </button>
    </div>
  )
}
