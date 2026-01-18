import { useState } from 'react'
import { expenseAPI } from '../services/api'
import { Upload, FileText, CheckCircle, AlertCircle, Info, X, FileSpreadsheet, File } from 'lucide-react'
import PasswordDialog from './PasswordDialog'
import DateRangePicker from './DateRangePicker'

const CATEGORIES = [
  'Groceries',
  'Entertainment',
  'Rent',
  'Transport',
  'Bills',
  'Shopping',
  'Healthcare',
  'Income',
  'Other',
  'Uncategorized'
]

const FILE_TYPES = {
  csv: { icon: FileText, color: 'text-blue-500', label: 'CSV' },
  pdf: { icon: File, color: 'text-red-500', label: 'PDF' },
  excel_xlsx: { icon: FileSpreadsheet, color: 'text-green-500', label: 'Excel' },
  excel_xls: { icon: FileSpreadsheet, color: 'text-green-500', label: 'Excel (Legacy)' }
}

export default function UploadView({ onUploadComplete }) {
  // Phase tracking
  const [uploadPhase, setUploadPhase] = useState('upload') // 'upload' | 'password' | 'date_range' | 'clarify'

  // File state
  const [file, setFile] = useState(null)
  const [fileType, setFileType] = useState(null)

  // Upload state
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  // Session state
  const [sessionId, setSessionId] = useState(null)
  const [dateRange, setDateRange] = useState(null)
  const [preview, setPreview] = useState([])

  // Password state
  const [showPasswordDialog, setShowPasswordDialog] = useState(false)
  const [passwordError, setPasswordError] = useState('')

  // Date range state
  const [showDateRangePicker, setShowDateRangePicker] = useState(false)

  // Clarification state
  const [showClarificationDialog, setShowClarificationDialog] = useState(false)
  const [ambiguousItems, setAmbiguousItems] = useState([])
  const [clarifications, setClarifications] = useState({})
  const [processingClarifications, setProcessingClarifications] = useState(false)

  // Settings
  const [clearPrevious, setClearPrevious] = useState(true)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    const allowedExtensions = ['.csv', '.pdf', '.xlsx', '.xls']
    const fileExt = selectedFile?.name.toLowerCase().match(/\.[^.]+$/)?.[0]

    if (selectedFile && allowedExtensions.includes(fileExt)) {
      setFile(selectedFile)
      setError('')
      setResult(null)
      // Reset all states
      setUploadPhase('upload')
      setSessionId(null)
      setDateRange(null)
      setPreview([])
      setShowPasswordDialog(false)
      setShowDateRangePicker(false)
      setShowClarificationDialog(false)
      setAmbiguousItems([])
      setClarifications({})
    } else {
      setError('Please select a valid file (CSV, PDF, or Excel)')
      setFile(null)
    }
  }

  // Phase 1: Upload and Extract
  const handleUpload = async (password = null) => {
    if (!file) {
      setError('Please select a file first')
      return
    }

    setUploading(true)
    setError('')
    setPasswordError('')

    try {
      console.log('[Phase 1] Uploading and extracting transactions')
      const data = await expenseAPI.uploadStatement(file, password, clearPrevious)
      console.log('[Phase 1] Response:', data)

      // Check if password needed
      if (data.status === 'password_required') {
        console.log('[Phase 1] Password required')
        setShowPasswordDialog(true)
        setUploading(false)
        return
      }

      // Extract successful
      if (data.status === 'extracted') {
        console.log(`[Phase 1] Extracted ${data.transaction_count} transactions`)
        setSessionId(data.session_id)
        setFileType(data.file_type)
        setDateRange(data.date_range)
        setPreview(data.preview)
        setUploadPhase('date_range')
        setShowPasswordDialog(false)
        setShowDateRangePicker(true)
      }
    } catch (err) {
      console.error('[Phase 1] Upload failed:', err)
      const errorMessage = err.response?.data?.message || err.response?.data?.error || 'Failed to upload file'
      setError(errorMessage)
    } finally {
      setUploading(false)
    }
  }

  // Password dialog handlers
  const handlePasswordSubmit = (password) => {
    console.log('[Password] Retrying with password')
    handleUpload(password)
  }

  const handlePasswordCancel = () => {
    setShowPasswordDialog(false)
    setFile(null)
    document.getElementById('file-input').value = ''
  }

  // Phase 2: Date Range Selection
  const handleDateRangeSelect = async (startDate, endDate) => {
    setUploading(true)
    setError('')

    try {
      console.log(`[Phase 2] Filtering transactions: ${startDate} to ${endDate}`)
      const data = await expenseAPI.selectDateRange(sessionId, startDate, endDate)
      console.log('[Phase 2] Response:', data)

      if (data.needs_clarification) {
        console.log(`[Phase 2] Found ${data.ambiguous_count} ambiguous transactions`)
        setAmbiguousItems(data.ambiguous_items)

        // Initialize clarifications with AI suggestions
        const initialClarifications = {}
        data.ambiguous_items.forEach(item => {
          initialClarifications[item.index] = item.suggested_category
        })
        setClarifications(initialClarifications)

        setUploadPhase('clarify')
        setShowDateRangePicker(false)
        setShowClarificationDialog(true)
      } else {
        // All clear - proceed to import
        console.log('[Phase 2] All transactions clear, importing')
        await handleImport({})
      }
    } catch (err) {
      console.error('[Phase 2] Date range selection failed:', err)
      const errorMessage = err.response?.data?.message || err.response?.data?.error || 'Failed to filter date range'
      setError(errorMessage)
    } finally {
      setUploading(false)
    }
  }

  const handleDateRangeCancel = () => {
    setShowDateRangePicker(false)
    setFile(null)
    setSessionId(null)
    setDateRange(null)
    setUploadPhase('upload')
    document.getElementById('file-input').value = ''
  }

  // Phase 3: Import with Clarifications
  const handleClarificationChange = (index, category) => {
    setClarifications(prev => ({
      ...prev,
      [index]: category
    }))
  }

  const handleSubmitClarifications = async () => {
    await handleImport(clarifications)
  }

  const handleImport = async (clarificationsData) => {
    setProcessingClarifications(true)
    setError('')

    try {
      console.log('[Phase 3] Importing transactions with clarifications')
      const data = await expenseAPI.importTransactions(sessionId, clarificationsData)
      console.log('[Phase 3] Import successful:', data)

      setResult(data)
      setShowClarificationDialog(false)
      setAmbiguousItems([])
      setClarifications({})
      setSessionId(null)
      setFile(null)
      setUploadPhase('upload')
      document.getElementById('file-input').value = ''

      // Auto-navigate to expenses view after 2 seconds
      if (onUploadComplete && data.imported > 0) {
        setTimeout(() => {
          onUploadComplete()
        }, 2000)
      }
    } catch (err) {
      console.error('[Phase 3] Import failed:', err)
      const errorMessage = err.response?.data?.message || err.response?.data?.error || 'Failed to import transactions'
      setError(errorMessage)
    } finally {
      setProcessingClarifications(false)
    }
  }

  const handleCancelClarification = () => {
    setShowClarificationDialog(false)
    setAmbiguousItems([])
    setClarifications({})
    setSessionId(null)
    setFile(null)
    setUploadPhase('upload')
    document.getElementById('file-input').value = ''
  }

  const getConfidenceBadgeColor = (confidence) => {
    switch (confidence) {
      case 'high':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getFileIcon = () => {
    if (!fileType) return FileText
    return FILE_TYPES[fileType]?.icon || FileText
  }

  const getFileColor = () => {
    if (!fileType) return 'text-gray-500'
    return FILE_TYPES[fileType]?.color || 'text-gray-500'
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Upload Bank Statement</h2>
        <p className="text-gray-600 mt-1">Import transactions from CSV, PDF, or Excel files</p>
      </div>

      {/* Upload Card */}
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="max-w-2xl mx-auto">
          {/* Upload Area */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-primary-500 transition-colors">
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Upload Statement</h3>
            <p className="text-sm text-gray-600 mb-4">
              Supports CSV, PDF (encrypted/regular), and Excel files
            </p>

            <input
              id="file-input"
              type="file"
              accept=".csv,.pdf,.xlsx,.xls"
              onChange={handleFileChange}
              className="hidden"
            />

            <label
              htmlFor="file-input"
              className="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 cursor-pointer transition-colors"
            >
              <FileText className="w-4 h-4" />
              Select File
            </label>

            {file && (
              <div className="mt-4 flex items-center justify-center gap-2 text-sm">
                {(() => {
                  const Icon = getFileIcon()
                  return <Icon className={`w-5 h-5 ${getFileColor()}`} />
                })()}
                <span className="font-medium text-gray-900">{file.name}</span>
                <span className="text-gray-500">({(file.size / 1024).toFixed(2)} KB)</span>
              </div>
            )}
          </div>

          {/* Upload Button */}
          {file && uploadPhase === 'upload' && (
            <div className="mt-6 text-center">
              <button
                onClick={() => handleUpload()}
                disabled={uploading}
                className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {uploading ? 'Processing...' : 'Upload and Extract'}
              </button>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-medium text-red-900">Error</h4>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* Success Message */}
          {result && (
            <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-medium text-green-900">Import Successful!</h4>
                  <p className="text-sm text-green-700 mt-1">{result.message}</p>
                  <div className="mt-3 grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-900">{result.imported}</div>
                      <div className="text-xs text-green-700">Imported</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">{result.total}</div>
                      <div className="text-xs text-gray-700">Total</div>
                    </div>
                  </div>
                  {result.imported > 0 && (
                    <p className="text-sm text-green-600 mt-3 flex items-center gap-2">
                      <span className="animate-pulse">Redirecting to Expenses view...</span>
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Password Dialog */}
      <PasswordDialog
        isOpen={showPasswordDialog}
        onSubmit={handlePasswordSubmit}
        onCancel={handlePasswordCancel}
        error={passwordError}
        loading={uploading}
      />

      {/* Date Range Picker Modal */}
      {showDateRangePicker && dateRange && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <DateRangePicker
            dateRange={dateRange}
            onSelect={handleDateRangeSelect}
            onCancel={handleDateRangeCancel}
            loading={uploading}
          />
        </div>
      )}

      {/* Clarification Dialog */}
      {showClarificationDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Dialog Header */}
            <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-bold">Transaction Clarification Needed</h3>
                  <p className="text-orange-100 mt-1">
                    Found {ambiguousItems.length} transaction(s) that need your input
                  </p>
                </div>
                <button
                  onClick={handleCancelClarification}
                  className="text-white hover:bg-orange-600 rounded-lg p-2 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Dialog Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex items-start gap-3">
                <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium">AI couldn't confidently categorize these transactions</p>
                  <p className="mt-1">Please review and select the correct category for each transaction below.</p>
                </div>
              </div>

              <div className="space-y-4">
                {ambiguousItems.map((item) => (
                  <div key={item.index} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-gray-900">{item.description}</h4>
                          {item.transaction_count > 1 && (
                            <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
                              {item.transaction_count} transactions
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mt-1">
                          ₹{item.amount.toFixed(2)} • {new Date(item.date).toLocaleDateString()}
                        </p>
                      </div>
                      <span className={`px-3 py-1 text-xs font-medium border rounded-full ${getConfidenceBadgeColor(item.confidence)}`}>
                        {item.confidence} confidence
                      </span>
                    </div>

                    {/* AI Reasoning */}
                    <div className="bg-white rounded border border-gray-200 p-3 mb-3">
                      <p className="text-xs font-medium text-gray-500 mb-1">AI Analysis:</p>
                      <p className="text-sm text-gray-700">{item.reasoning}</p>
                      {item.alternatives.length > 0 && (
                        <p className="text-xs text-gray-500 mt-2">
                          Also considered: {item.alternatives.join(', ')}
                        </p>
                      )}
                    </div>

                    {/* Category Selector */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Select Category:
                      </label>
                      <select
                        value={clarifications[item.index] || item.suggested_category}
                        onChange={(e) => handleClarificationChange(item.index, e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      >
                        {CATEGORIES.map(category => (
                          <option key={category} value={category}>
                            {category}
                            {category === item.suggested_category ? ' (AI Suggestion)' : ''}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Dialog Footer */}
            <div className="border-t border-gray-200 p-6 bg-gray-50">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  {ambiguousItems.length} unique merchant(s) to categorize
                  {ambiguousItems.some(item => item.transaction_count > 1) && (
                    <span className="text-gray-500 ml-1">
                      ({ambiguousItems.reduce((sum, item) => sum + (item.transaction_count || 1), 0)} total transactions)
                    </span>
                  )}
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={handleCancelClarification}
                    className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSubmitClarifications}
                    disabled={processingClarifications}
                    className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {processingClarifications ? 'Importing...' : 'Confirm & Import'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-3">How It Works</h3>
        <ul className="space-y-2 text-sm text-blue-800">
          <li className="flex items-start gap-2">
            <span className="text-blue-600">1.</span>
            <span><strong>Upload:</strong> Select CSV, PDF (password-protected supported), or Excel file</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600">2.</span>
            <span><strong>Date Range:</strong> Choose which period to import (1 month, 3 months, etc.)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600">3.</span>
            <span><strong>Review:</strong> Clarify ambiguous transactions that AI couldn't confidently categorize</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600">4.</span>
            <span><strong>Import:</strong> Transactions are automatically categorized and added to your expenses</span>
          </li>
        </ul>

        <div className="mt-4 pt-4 border-t border-blue-300">
          <p className="text-sm text-blue-800 font-medium mb-2">Supported formats:</p>
          <div className="flex gap-4 text-xs">
            <div className="flex items-center gap-1">
              <FileText className="w-4 h-4 text-blue-500" />
              <span>CSV</span>
            </div>
            <div className="flex items-center gap-1">
              <File className="w-4 h-4 text-red-500" />
              <span>PDF</span>
            </div>
            <div className="flex items-center gap-1">
              <FileSpreadsheet className="w-4 h-4 text-green-500" />
              <span>Excel (.xlsx, .xls)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
