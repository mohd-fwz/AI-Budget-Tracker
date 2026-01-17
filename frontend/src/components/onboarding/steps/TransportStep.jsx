import { useState } from 'react'

export default function TransportStep({ data, onNext }) {
  const [formData, setFormData] = useState({
    mode: data.mode || 'own_vehicle',
    vehicle_type: data.vehicle_type || 'bike',
    fuel_type: data.fuel_type || 'petrol',
    avg_km_per_month: data.avg_km_per_month || 500,
    public_transport: data.public_transport || {
      uses_metro: false,
      metro_monthly_cost: 0,
      uses_bus: false,
      bus_monthly_cost: 0
    }
  })

  const handleModeChange = (newMode) => {
    setFormData({ ...formData, mode: newMode })
  }

  const updatePublicTransport = (field, value) => {
    setFormData({
      ...formData,
      public_transport: {
        ...formData.public_transport,
        [field]: value
      }
    })
  }

  const handleContinue = () => {
    onNext(formData)
  }

  const handleSkip = () => {
    // Skip transport - useful for students who walk/bike short distances
    onNext({})
  }

  const showOwnVehicle = formData.mode === 'own_vehicle' || formData.mode === 'mixed'
  const showPublicTransport = formData.mode === 'public_transport' || formData.mode === 'mixed'

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2 flex items-center gap-2">
          <span>🚗</span>
          Transport Preferences (Optional)
        </h2>
        <p className="text-gray-600">
          Help us understand your commute and travel patterns to calculate accurate transport costs.
        </p>
        <p className="text-sm text-blue-600 mt-2">
          💡 Students: If you walk/bike short distances or have minimal transport costs, you can skip this!
        </p>
      </div>

      {/* Primary Mode */}
      <div>
        <label className="block font-semibold text-gray-800 mb-3">
          Primary Transport Mode
        </label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: 'own_vehicle', label: 'Own Vehicle', icon: '🚗', desc: 'Bike, car, or scooter' },
            { value: 'public_transport', label: 'Public Transport', icon: '🚌', desc: 'Metro, bus, etc.' },
            { value: 'mixed', label: 'Mixed', icon: '🚗🚌', desc: 'Both personal & public' }
          ].map((mode) => (
            <button
              key={mode.value}
              onClick={() => handleModeChange(mode.value)}
              className={`p-4 border-2 rounded-xl transition transform hover:scale-105 ${
                formData.mode === mode.value
                  ? 'border-blue-600 bg-blue-50 shadow-lg'
                  : 'border-gray-200 bg-white hover:border-blue-300'
              }`}
            >
              <div className="text-3xl mb-2">{mode.icon}</div>
              <div className="text-sm font-semibold text-gray-800">{mode.label}</div>
              <div className="text-xs text-gray-600 mt-1">{mode.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Own Vehicle Details */}
      {showOwnVehicle && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200 space-y-4">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2">
            <span>🚗</span>
            Personal Vehicle Details
          </h3>

          {/* Vehicle Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Vehicle Type
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'bike', label: 'Bike', icon: '🏍️' },
                { value: 'scooter', label: 'Scooter', icon: '🛵' },
                { value: 'car', label: 'Car', icon: '🚗' }
              ].map((vehicle) => (
                <button
                  key={vehicle.value}
                  onClick={() => setFormData({ ...formData, vehicle_type: vehicle.value })}
                  className={`p-3 border-2 rounded-lg transition ${
                    formData.vehicle_type === vehicle.value
                      ? 'border-blue-600 bg-white shadow-md'
                      : 'border-gray-200 bg-white hover:border-blue-300'
                  }`}
                >
                  <div className="text-2xl mb-1">{vehicle.icon}</div>
                  <div className="text-xs font-medium text-gray-800">{vehicle.label}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Fuel Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Fuel Type
            </label>
            <select
              value={formData.fuel_type}
              onChange={(e) => setFormData({ ...formData, fuel_type: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            >
              <option value="petrol">Petrol</option>
              <option value="diesel">Diesel</option>
              <option value="electric">Electric</option>
              <option value="cng">CNG</option>
            </select>
          </div>

          {/* Average KM per month */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Average Kilometers per Month
            </label>
            <input
              type="number"
              min="0"
              step="50"
              value={formData.avg_km_per_month}
              onChange={(e) => setFormData({ ...formData, avg_km_per_month: parseInt(e.target.value) || 0 })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              placeholder="500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Typical commute: 300-1000 km/month
            </p>
          </div>

          {/* Quick calculation preview */}
          {formData.avg_km_per_month > 0 && (
            <div className="bg-white p-3 rounded-lg border border-blue-200">
              <p className="text-xs font-medium text-gray-700">Quick Estimate:</p>
              <p className="text-sm text-gray-600 mt-1">
                ~{Math.round(formData.avg_km_per_month / 30)} km per day
              </p>
            </div>
          )}
        </div>
      )}

      {/* Public Transport Details */}
      {showPublicTransport && (
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200 space-y-4">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2">
            <span>🚌</span>
            Public Transport Usage
          </h3>

          {/* Metro */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <label className="flex items-center gap-3 mb-3 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.public_transport.uses_metro}
                onChange={(e) => updatePublicTransport('uses_metro', e.target.checked)}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <div className="flex items-center gap-2 flex-1">
                <span className="text-2xl">🚇</span>
                <div>
                  <span className="font-medium text-gray-800">Metro</span>
                  <p className="text-xs text-gray-600">I use metro for commuting</p>
                </div>
              </div>
            </label>

            {formData.public_transport.uses_metro && (
              <div className="ml-8 mt-3">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Monthly Metro Recharge/Pass Cost
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    value={formData.public_transport.metro_monthly_cost}
                    onChange={(e) => updatePublicTransport('metro_monthly_cost', parseInt(e.target.value) || 0)}
                    className="w-full pl-8 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                    placeholder="1000"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Average metro pass: ₹800-2000/month
                </p>
              </div>
            )}
          </div>

          {/* Bus */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <label className="flex items-center gap-3 mb-3 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.public_transport.uses_bus}
                onChange={(e) => updatePublicTransport('uses_bus', e.target.checked)}
                className="w-5 h-5 text-green-600 border-gray-300 rounded focus:ring-green-500"
              />
              <div className="flex items-center gap-2 flex-1">
                <span className="text-2xl">🚌</span>
                <div>
                  <span className="font-medium text-gray-800">Bus</span>
                  <p className="text-xs text-gray-600">I use bus for commuting</p>
                </div>
              </div>
            </label>

            {formData.public_transport.uses_bus && (
              <div className="ml-8 mt-3">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Monthly Bus Pass/Ticket Cost
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    value={formData.public_transport.bus_monthly_cost}
                    onChange={(e) => updatePublicTransport('bus_monthly_cost', parseInt(e.target.value) || 0)}
                    className="w-full pl-8 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
                    placeholder="500"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Average bus pass: ₹500-1500/month
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
        <div className="flex items-start gap-3">
          <span className="text-xl">💡</span>
          <div className="text-sm text-blue-800">
            <p className="font-medium">How we calculate your transport budget:</p>
            <p className="mt-1">
              {showOwnVehicle && "We'll use your vehicle type, monthly kilometers, and current fuel prices in your city to estimate fuel costs. "}
              {showPublicTransport && "We'll factor in your metro/bus usage based on the costs you provided. "}
              We'll also compare this with your historical transport spending to give you the most accurate recommendations!
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
          Skip (Minimal transport costs)
        </button>
        <button
          onClick={handleContinue}
          className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
        >
          Continue with Details
        </button>
      </div>
    </div>
  )
}
