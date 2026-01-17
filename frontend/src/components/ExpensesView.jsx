import { useState, useEffect } from 'react'
import { expenseAPI } from '../services/api'
import { Plus, Trash2, Calendar, DollarSign, Tag, Filter, Edit2, Check, X } from 'lucide-react'
import { format } from 'date-fns'

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
]

export default function ExpensesView() {
  const [expenses, setExpenses] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [filterCategory, setFilterCategory] = useState('')

  // Edit category state
  const [editingExpenseId, setEditingExpenseId] = useState(null)
  const [editingCategory, setEditingCategory] = useState('')

  // Form state
  const [formData, setFormData] = useState({
    amount: '',
    category: '',
    date: format(new Date(), 'yyyy-MM-dd'),
    description: '',
  })

  useEffect(() => {
    fetchExpenses()
  }, [filterCategory])

  const fetchExpenses = async () => {
    try {
      setLoading(true)
      const params = filterCategory ? { category: filterCategory } : {}
      const data = await expenseAPI.getExpenses(params)
      setExpenses(data.expenses)
    } catch (error) {
      console.error('Error fetching expenses:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await expenseAPI.addExpense({
        ...formData,
        amount: parseFloat(formData.amount),
      })
      setFormData({
        amount: '',
        category: '',
        date: format(new Date(), 'yyyy-MM-dd'),
        description: '',
      })
      setShowAddForm(false)
      fetchExpenses()
    } catch (error) {
      console.error('Error adding expense:', error)
      alert('Failed to add expense: ' + (error.response?.data?.message || error.message))
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this expense?')) return

    try {
      await expenseAPI.deleteExpense(id)
      fetchExpenses()
    } catch (error) {
      console.error('Error deleting expense:', error)
      alert('Failed to delete expense')
    }
  }

  const handleStartEditCategory = (expense) => {
    setEditingExpenseId(expense.id)
    setEditingCategory(expense.category)
  }

  const handleCancelEditCategory = () => {
    setEditingExpenseId(null)
    setEditingCategory('')
  }

  const handleSaveCategory = async (expenseId) => {
    try {
      const result = await expenseAPI.updateExpenseCategory(expenseId, editingCategory)

      // Show success message with learning indicator
      if (result.learned) {
        alert(`✓ Category updated to "${editingCategory}"\n\nThis merchant will be automatically categorized as "${editingCategory}" in future imports!`)
      } else {
        alert(`✓ Category updated to "${editingCategory}"`)
      }

      setEditingExpenseId(null)
      setEditingCategory('')
      fetchExpenses()
    } catch (error) {
      console.error('Error updating category:', error)
      alert('Failed to update category: ' + (error.response?.data?.message || error.message))
    }
  }

  const getCategoryColor = (category) => {
    const colors = {
      Groceries: 'bg-green-100 text-green-800',
      Entertainment: 'bg-purple-100 text-purple-800',
      Rent: 'bg-blue-100 text-blue-800',
      Transport: 'bg-yellow-100 text-yellow-800',
      Bills: 'bg-red-100 text-red-800',
      Shopping: 'bg-pink-100 text-pink-800',
      Healthcare: 'bg-indigo-100 text-indigo-800',
      Income: 'bg-emerald-100 text-emerald-800',
      Other: 'bg-gray-100 text-gray-800',
    }
    return colors[category] || colors.Other
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">My Expenses</h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Add Expense
        </button>
      </div>

      {/* Add Expense Form */}
      {showAddForm && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Expense</h3>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Amount *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="0.00"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="">Auto-detect</option>
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date *
              </label>
              <input
                type="date"
                required
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="e.g., Walmart groceries"
              />
            </div>

            <div className="md:col-span-2 flex gap-3">
              <button
                type="submit"
                className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors"
              >
                Add Expense
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filter */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex items-center gap-3">
          <Filter className="w-5 h-5 text-gray-500" />
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="">All Categories</option>
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Expenses List */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading expenses...</div>
        ) : expenses.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No expenses yet. Add your first expense above!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {expenses.map((expense) => (
                  <tr key={expense.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {format(new Date(expense.date), 'MMM dd, yyyy')}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {expense.description || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {editingExpenseId === expense.id ? (
                        <div className="flex items-center gap-2">
                          <select
                            value={editingCategory}
                            onChange={(e) => setEditingCategory(e.target.value)}
                            className="px-2 py-1 text-xs border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            {CATEGORIES.map((cat) => (
                              <option key={cat} value={cat}>{cat}</option>
                            ))}
                          </select>
                          <button
                            onClick={() => handleSaveCategory(expense.id)}
                            className="text-green-600 hover:text-green-800"
                            title="Save"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                          <button
                            onClick={handleCancelEditCategory}
                            className="text-gray-600 hover:text-gray-800"
                            title="Cancel"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getCategoryColor(expense.category)}`}>
                            {expense.category}
                          </span>
                          <button
                            onClick={() => handleStartEditCategory(expense)}
                            className="text-blue-600 hover:text-blue-800"
                            title="Edit category"
                          >
                            <Edit2 className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                      ₹{expense.amount.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => handleDelete(expense.id)}
                        className="text-red-600 hover:text-red-800"
                        title="Delete expense"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Total */}
      {expenses.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex justify-between items-center">
            <span className="text-lg font-medium text-gray-700">Total Spending:</span>
            <span className="text-2xl font-bold text-gray-900">
              ₹{expenses.filter(exp => exp.category !== 'Income').reduce((sum, exp) => sum + exp.amount, 0).toFixed(2)}
            </span>
          </div>
          {expenses.some(exp => exp.category === 'Income') && (
            <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200">
              <span className="text-lg font-medium text-green-700">Total Income:</span>
              <span className="text-2xl font-bold text-green-600">
                ₹{expenses.filter(exp => exp.category === 'Income').reduce((sum, exp) => sum + exp.amount, 0).toFixed(2)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
