import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Check, Clock, AlertCircle, XCircle, Shield } from 'lucide-react'
import { api } from '../services/api' 
import { useNavigate } from 'react-router-dom'

const AGENT_STEPS = [
  { key: 'validator', name: 'Validator', desc: 'Checking repository...' },
  { key: 'scanner', name: 'Scanner', desc: 'Analyzing code...' },
  { key: 'grader', name: 'Grader', desc: 'Assessing SFIA level...' },
  { key: 'auditor', name: 'Auditor', desc: 'Reality check...' },
  { key: 'reporter', name: 'Reporter', desc: 'Finalizing credits...' }
]

export default function AnalysisPage({ jobId, onComplete, onError }) {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [validationError, setValidationError] = useState(null)

  useEffect(() => {
    if (!jobId) return

    const pollStatus = async () => {
      try {
        // Updated: Use the centralized API service
        const data = await api.checkStatus(jobId)
        
        setStatus(data)

        // Handle validation failure (e.g. Private repo, invalid URL)
        if (data.status === 'failed' && data.validation) {
          setValidationError(data.validation)
          clearInterval(interval)
        } 
        // Handle complete
        else if (data.status === 'complete') {
          clearInterval(interval)
          // Pass the Job ID back to the parent (App.jsx) to handle history & navigation
          onComplete(jobId)
        } 
        // Handle server error
        else if (data.status === 'error') {
          setError(data.errors?.[0] || 'Analysis failed')
          clearInterval(interval)
        }
      } catch (err) {
        console.error('Poll error:', err)
        setError('Failed to fetch status')
      }
    }

    // Poll every 2 seconds
    const interval = setInterval(pollStatus, 2000)
    pollStatus()

    return () => clearInterval(interval)
  }, [jobId, onComplete])

  // --- CONDITIONAL RENDERING STATES ---

  // 1. Show Validation Errors (User input issues)
  if (validationError) {
    return <ValidationErrorView 
      validation={validationError} 
      onRetry={() => window.location.reload()} 
    />
  }

  // 2. Show System Errors (Server/Network issues)
  if (error) {
    return <ErrorView error={error} onRetry={() => window.location.reload()} />
  }

  // 3. Show Loading State (Before first status fetch)
  if (!status) {
    return <LoadingView />
  }

  // 4. Show Analysis Progress (Main View)
  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="max-w-4xl w-full">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold text-white mb-4">
            Analyzing Your Repository
          </h1>
          <p className="text-gray-400">
            Our AI agents are working together to verify your skills
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-slate-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-8 mb-8"
        >
          {/* Progress Bar */}
          <div className="mb-6">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-400">Overall Progress</span>
              <span className="text-white font-semibold">{status.progress}%</span>
            </div>
            <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${status.progress}%` }}
                transition={{ duration: 0.5 }}
                className="h-full bg-gradient-to-r from-blue-500 to-purple-600 rounded-full"
              />
            </div>
          </div>

          {/* Agent Steps List */}
          <div className="space-y-4">
            {AGENT_STEPS.map((step, index) => {
              const isActive = status.current_step === step.key
              const isComplete = AGENT_STEPS.findIndex(s => s.key === status.current_step) > index

              return (
                <motion.div
                  key={step.key}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`flex items-center gap-4 p-4 rounded-xl transition-all ${
                    isActive
                      ? 'bg-blue-500/10 border border-blue-500/30'
                      : isComplete
                      ? 'bg-green-500/10 border border-green-500/30'
                      : 'bg-slate-800/30 border border-white/5'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    isActive
                      ? 'bg-blue-500/20'
                      : isComplete
                      ? 'bg-green-500/20'
                      : 'bg-slate-700/50'
                  }`}>
                    {isComplete ? (
                      <Check className="w-5 h-5 text-green-400" />
                    ) : isActive ? (
                      <div className="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Clock className="w-5 h-5 text-gray-500" />
                    )}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className={`font-semibold ${
                        isActive || isComplete ? 'text-white' : 'text-gray-500'
                      }`}>
                        {step.name}
                      </h3>
                      {isActive && (
                        <span className="text-xs text-blue-400 font-medium">
                          In Progress
                        </span>
                      )}
                    </div>
                    <p className={`text-sm ${
                      isActive || isComplete ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                      {step.desc}
                    </p>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </motion.div>
      </div>
    </div>
  )
}

// --- SUB-COMPONENTS (INCLUDED) ---

function ValidationErrorView({ validation, onRetry }) {
  const navigate = useNavigate() // Hook for navigation

  const handleRetryWithToken = () => {
    // Navigate back to home, but pass state to open the token input immediately
    navigate('/', { 
      state: { 
        repoUrl: validation.repo_name ? `${validation.owner}/${validation.repo_name}` : '', 
        requestToken: true 
      } 
    })
  }


  const errorMessages = {
    'INVALID_URL': {
      title: 'Invalid GitHub URL',
      message: 'Please enter a valid GitHub repository URL',
      icon: <XCircle className="w-12 h-12 text-red-400" />,
      action: 'Try Again'
    },
    'PRIVATE_REPO': {
      title: 'Private Repository Detected',
      message: 'This repository is private or not found. We need your permission to access it.',
      icon: <Shield className="w-12 h-12 text-yellow-400" />,
      action: 'Enter Access Token', // Changed label
      showTokenHelp: true,
      customAction: handleRetryWithToken // Use our new handler
    },
    'TOKEN_INVALID': {
      title: 'Invalid Access Token',
      message: 'The provided GitHub token is invalid or lacks required permissions.',
      icon: <XCircle className="w-12 h-12 text-red-400" />,
      action: 'Update Token'
    },
    'SIZE_EXCEEDED': {
      title: 'Repository Too Large',
      message: `Repository size (${validation.size_kb} KB) exceeds maximum limit.`,
      icon: <AlertCircle className="w-12 h-12 text-orange-400" />,
      action: 'Try Smaller Repo'
    },
    'EMPTY_REPO': {
      title: 'Empty Repository',
      message: 'This repository appears to be empty. Add some code first!',
      icon: <AlertCircle className="w-12 h-12 text-yellow-400" />,
      action: 'Go Back'
    },
    'RATE_LIMIT': {
      title: 'Rate Limit Exceeded',
      message: 'GitHub API rate limit reached. Please try again in a few minutes.',
      icon: <Clock className="w-12 h-12 text-orange-400" />,
      action: 'Try Later'
    }
  }

  const errorType = validation.error_type || 'UNKNOWN'
  const errorConfig = errorMessages[errorType] || {
    title: 'Validation Failed',
    message: validation.error || 'Unknown error occurred',
    icon: <AlertCircle className="w-12 h-12 text-red-400" />,
    action: 'Try Again'
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-slate-900/50 backdrop-blur-xl border border-red-500/30 rounded-2xl p-8 max-w-md"
      >
        <div className="text-center">
          {errorConfig.icon}
          
          <h2 className="text-2xl font-semibold text-white mt-4 mb-2">
            {errorConfig.title}
          </h2>
          
          <p className="text-gray-400 mb-6">
            {errorConfig.message}
          </p>

          {errorConfig.showTokenHelp && (
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-6 text-left">
              <p className="text-sm text-gray-300 mb-2">
                <strong>How to get a token:</strong>
              </p>
              <ol className="text-sm text-gray-400 space-y-1 list-decimal list-inside">
                <li>Go to GitHub Settings → Developer settings</li>
                <li>Generate new token (classic)</li>
                <li>Select 'repo' scope</li>
                <li>Copy and paste in the form</li>
              </ol>
              <a
                href="https://github.com/settings/tokens/new"
                target="_blank"
                rel="noopener noreferrer"
                className="text-yellow-400 hover:text-yellow-300 text-sm underline mt-2 inline-block"
              >
                Create Token →
              </a>
            </div>
          )}

          <button
            onClick={errorConfig.customAction || onRetry} // Use custom action if defined
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-colors"
          >
            {errorConfig.action}
          </button>
        </div>
      </motion.div>
    </div>
  )
}

function ErrorView({ error, onRetry }) {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-red-500/10 border border-red-500/30 rounded-2xl p-8 max-w-md"
      >
        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-white text-center mb-2">
          Analysis Failed
        </h2>
        <p className="text-gray-400 text-center mb-4">{error}</p>
        <button
          onClick={onRetry}
          className="w-full bg-slate-800 hover:bg-slate-700 text-white py-2 rounded-lg transition-colors"
        >
          Try Again
        </button>
      </motion.div>
    </div>
  )
}

function LoadingView() {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-400">Connecting to analysis engine...</p>
      </div>
    </div>
  )
}