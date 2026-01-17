import { useState } from 'react'
import { profileAPI } from '../../services/api'
import BasicInfoStep from './steps/BasicInfoStep'
import CategorySelectionStep from './steps/CategorySelectionStep'
import GroceriesStep from './steps/GroceriesStep'
import TransportStep from './steps/TransportStep'
import EntertainmentStep from './steps/EntertainmentStep'
import BillsStep from './steps/BillsStep'
import ReviewStep from './steps/ReviewStep'

const STEPS = {
  BASIC_INFO: 1,
  CATEGORY_SELECTION: 2,
  GROCERIES: 3,
  TRANSPORT: 4,
  ENTERTAINMENT: 5,
  BILLS: 6,
  REVIEW: 7
}

// Order of category processing
const CATEGORY_ORDER = ['Groceries', 'Transport', 'Entertainment', 'Bills']

export default function OnboardingWizard({ onComplete }) {
  const [currentStep, setCurrentStep] = useState(STEPS.BASIC_INFO)
  const [selectedCategories, setSelectedCategories] = useState([])
  const [formData, setFormData] = useState({
    basicInfo: {},
    groceries: {},
    transport: {},
    entertainment: {},
    bills: {}
  })

  const handleBasicInfoNext = (data) => {
    setFormData({ ...formData, basicInfo: data })
    setCurrentStep(STEPS.CATEGORY_SELECTION)
  }

  const getNextCategoryStep = (currentCategory) => {
    // Find next category after current
    const currentIndex = CATEGORY_ORDER.indexOf(currentCategory)
    for (let i = currentIndex + 1; i < CATEGORY_ORDER.length; i++) {
      if (selectedCategories.includes(CATEGORY_ORDER[i])) {
        return getCategoryStep(CATEGORY_ORDER[i])
      }
    }
    return STEPS.REVIEW
  }

  const getCategoryStep = (category) => {
    const stepMap = {
      'Groceries': STEPS.GROCERIES,
      'Transport': STEPS.TRANSPORT,
      'Entertainment': STEPS.ENTERTAINMENT,
      'Bills': STEPS.BILLS
    }
    return stepMap[category]
  }

  const handleCategorySelect = (categories) => {
    setSelectedCategories(categories)

    if (categories.length === 0) {
      setCurrentStep(STEPS.REVIEW)
      return
    }

    // Go to first selected category in order
    for (const category of CATEGORY_ORDER) {
      if (categories.includes(category)) {
        setCurrentStep(getCategoryStep(category))
        return
      }
    }
  }

  const handleGroceriesNext = (data) => {
    setFormData({ ...formData, groceries: data })
    setCurrentStep(getNextCategoryStep('Groceries'))
  }

  const handleTransportNext = (data) => {
    setFormData({ ...formData, transport: data })
    setCurrentStep(getNextCategoryStep('Transport'))
  }

  const handleEntertainmentNext = (data) => {
    setFormData({ ...formData, entertainment: data })
    setCurrentStep(getNextCategoryStep('Entertainment'))
  }

  const handleBillsNext = (data) => {
    setFormData({ ...formData, bills: data })
    setCurrentStep(getNextCategoryStep('Bills'))
  }

  const getPreviousCategoryStep = (currentCategory) => {
    const currentIndex = CATEGORY_ORDER.indexOf(currentCategory)
    for (let i = currentIndex - 1; i >= 0; i--) {
      if (selectedCategories.includes(CATEGORY_ORDER[i])) {
        return getCategoryStep(CATEGORY_ORDER[i])
      }
    }
    return STEPS.CATEGORY_SELECTION
  }

  const handleBack = () => {
    switch (currentStep) {
      case STEPS.CATEGORY_SELECTION:
        setCurrentStep(STEPS.BASIC_INFO)
        break
      case STEPS.GROCERIES:
        setCurrentStep(STEPS.CATEGORY_SELECTION)
        break
      case STEPS.TRANSPORT:
        setCurrentStep(getPreviousCategoryStep('Transport'))
        break
      case STEPS.ENTERTAINMENT:
        setCurrentStep(getPreviousCategoryStep('Entertainment'))
        break
      case STEPS.BILLS:
        setCurrentStep(getPreviousCategoryStep('Bills'))
        break
      case STEPS.REVIEW:
        // Go back to last selected category
        for (let i = CATEGORY_ORDER.length - 1; i >= 0; i--) {
          if (selectedCategories.includes(CATEGORY_ORDER[i])) {
            setCurrentStep(getCategoryStep(CATEGORY_ORDER[i]))
            return
          }
        }
        setCurrentStep(STEPS.CATEGORY_SELECTION)
        break
      default:
        break
    }
  }

  const handleFinalSubmit = async () => {
    try {
      // Save basic info
      await profileAPI.updateFinancialProfile(formData.basicInfo)

      // Save location
      if (formData.basicInfo.state && formData.basicInfo.city) {
        await profileAPI.updateLocation(formData.basicInfo.state, formData.basicInfo.city)
      }

      // Save category preferences
      for (const category of selectedCategories) {
        const categoryData = formData[category.toLowerCase()]
        if (categoryData && Object.keys(categoryData).length > 0) {
          await profileAPI.updateCategoryPreferences(category, categoryData)
        }
      }

      onComplete()
    } catch (error) {
      console.error('Failed to save onboarding data:', error)
      throw error
    }
  }

  const getStepNumber = () => {
    const totalSteps = 2 + selectedCategories.length + 1
    let currentStepNumber = 0

    if (currentStep === STEPS.BASIC_INFO) currentStepNumber = 1
    else if (currentStep === STEPS.CATEGORY_SELECTION) currentStepNumber = 2
    else if (currentStep === STEPS.REVIEW) currentStepNumber = totalSteps
    else {
      // Count how many selected categories come before current step
      currentStepNumber = 3
      for (const category of CATEGORY_ORDER) {
        const categoryStep = getCategoryStep(category)
        if (categoryStep === currentStep) break
        if (selectedCategories.includes(category)) currentStepNumber++
      }
    }

    return { current: currentStepNumber, total: totalSteps }
  }

  const renderStep = () => {
    switch (currentStep) {
      case STEPS.BASIC_INFO:
        return <BasicInfoStep data={formData.basicInfo} onNext={handleBasicInfoNext} />

      case STEPS.CATEGORY_SELECTION:
        return (
          <CategorySelectionStep
            selected={selectedCategories}
            onNext={handleCategorySelect}
          />
        )

      case STEPS.GROCERIES:
        return <GroceriesStep data={formData.groceries} onNext={handleGroceriesNext} />

      case STEPS.TRANSPORT:
        return <TransportStep data={formData.transport} onNext={handleTransportNext} />

      case STEPS.ENTERTAINMENT:
        return <EntertainmentStep data={formData.entertainment} onNext={handleEntertainmentNext} />

      case STEPS.BILLS:
        return <BillsStep data={formData.bills} onNext={handleBillsNext} />

      case STEPS.REVIEW:
        return (
          <ReviewStep
            data={formData}
            selectedCategories={selectedCategories}
            onSubmit={handleFinalSubmit}
          />
        )

      default:
        return null
    }
  }

  const stepInfo = getStepNumber()

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-3xl w-full">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Welcome to Budget Planner</h1>
          <p className="text-gray-600">Let's set up your personalized budget profile</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              Step {stepInfo.current} of {stepInfo.total}
            </span>
            <span className="text-sm text-gray-500">
              {Math.round((stepInfo.current / stepInfo.total) * 100)}% Complete
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-600 to-blue-600 transition-all duration-500 ease-out"
              style={{ width: `${(stepInfo.current / stepInfo.total) * 100}%` }}
            />
          </div>
        </div>

        {/* Step Content */}
        <div className="min-h-[400px]">
          {renderStep()}
        </div>

        {/* Back Button */}
        {currentStep > STEPS.BASIC_INFO && (
          <div className="mt-6 pt-6 border-t">
            <button
              onClick={handleBack}
              className="text-gray-600 hover:text-gray-800 font-medium flex items-center gap-2 transition"
            >
              <span>←</span>
              Back
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
