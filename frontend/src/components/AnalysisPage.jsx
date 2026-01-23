import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, Clock, AlertCircle, XCircle, Shield, Terminal, CheckCircle2, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { api } from '../services/api' 
import { useNavigate } from 'react-router-dom'

const AGENT_STEPS = [
  { key: 'validator', name: 'Validator', desc: 'Checking repository...', icon: Shield },
  { key: 'scanner', name: 'Scanner', desc: 'Analyzing code...', icon: Terminal },
  { key: 'grader', name: 'Grader', desc: 'Assessing SFIA level...', icon: CheckCircle2 },
  { key: 'judge', name: 'Judge', desc: 'Deliberating verdict...', icon: Shield },
  { key: 'auditor', name: 'Auditor', desc: 'Reality check...', icon: CheckCircle2 },
  { key: 'reporter', name: 'Reporter', desc: 'Finalizing credits...', icon: Check }
]

export default function AnalysisPage({ jobId, onComplete, onError }) {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [validationError, setValidationError] = useState(null)
  const [liveLogs, setLiveLogs] = useState([])
  const [expandedAgent, setExpandedAgent] = useState(null)

  // Polling for status
  useEffect(() => {
    if (!jobId) return

    const pollStatus = async () => {
      try {
        const data = await api.checkStatus(jobId)
        setStatus(data)

        if (data.status === 'failed' && data.validation) {
          setValidationError(data.validation)
          clearInterval(interval)
        } 
        else if (data.status === 'complete') {
          clearInterval(interval)
          onComplete(jobId)
        } 
        else if (data.status === 'error') {
          setError(data.errors?.[0] || 'Analysis failed')
          clearInterval(interval)
        }
      } catch (err) {
        console.error('Poll error:', err)
        setError('Failed to fetch status')
      }
    }

    const interval = setInterval(pollStatus, 2000)
    pollStatus()

    return () => clearInterval(interval)
  }, [jobId, onComplete])

  // SSE for live logs
  useEffect(() => {
    if (!jobId || status?.status === 'complete') return

    const eventSource = new EventSource(`http://localhost:8000/api/stream/${jobId}`)

    eventSource.onmessage = (event) => {
      try {
        const newLog = JSON.parse(event.data)
        setLiveLogs((prev) => [newLog, ...prev].slice(0, 100))
      } catch (err) {
        console.error("SSE Parse Error:", err)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
    }

    return () => eventSource.close()
  }, [jobId, status?.status])

  if (validationError) {
    return <ValidationErrorView 
      validation={validationError} 
      onRetry={() => window.location.reload()} 
    />
  }

  if (error) {
    return <ErrorView error={error} onRetry={() => window.location.reload()} />
  }

  if (!status) {
    return <LoadingView />
  }

  // Group logs by agent
  const logsByAgent = liveLogs.reduce((acc, log) => {
    if (!acc[log.agent]) acc[log.agent] = []
    acc[log.agent].push(log)
    return acc
  }, {})

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

          {/* Agent Steps with Expandable Activity */}
          <div className="space-y-3">
            {AGENT_STEPS.map((step, index) => {
              const isActive = status.current_step === step.key
              const isComplete = AGENT_STEPS.findIndex(s => s.key === status.current_step) > index
              const agentLogs = logsByAgent[step.name.toLowerCase()] || []
              const Icon = step.icon

              return (
                <div key={step.key}>
                  <motion.button
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    onClick={() => setExpandedAgent(expandedAgent === step.key ? null : step.key)}
                    className={`w-full flex items-center gap-4 p-4 rounded-xl transition-all ${
                      isActive
                        ? 'bg-blue-500/10 border border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.1)]'
                        : isComplete
                        ? 'bg-green-500/10 border border-green-500/30'
                        : 'bg-slate-800/30 border border-white/5 opacity-50'
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
                        <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                      ) : (
                        <Clock className="w-5 h-5 text-gray-500" />
                      )}
                    </div>

                    <div className="flex-1 text-left">
                      <div className="flex items-center gap-2 mb-1">
                        <Icon className="w-4 h-4" />
                        <h3 className={`font-semibold ${
                          isActive || isComplete ? 'text-white' : 'text-gray-500'
                        }`}>
                          {step.name}
                        </h3>
                        {isActive && (
                          <span className="text-[10px] bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded uppercase tracking-widest font-bold animate-pulse">
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

                    {agentLogs.length > 0 && (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">{agentLogs.length} activities</span>
                        {expandedAgent === step.key ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                      </div>
                    )}
                  </motion.button>

                  {/* Expandable Activity Log */}
                  <AnimatePresence>
                    {expandedAgent === step.key && agentLogs.length > 0 && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-2 ml-14 p-4 bg-black/30 border border-white/5 rounded-lg space-y-2">
                          {agentLogs.slice(0, 5).map((log, i) => (
                            <div key={i} className="text-xs font-mono flex gap-2">
                              <span className="text-gray-600">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                              <span className={`${log.status === 'error' ? 'text-red-400' : 'text-green-400'}`}>
                                {log.thought}
                              </span>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )
            })}
          </div>
        </motion.div>
      </div>
    </div>
  )
}

// Sub-components remain the same...
function ValidationErrorView({ validation, onRetry }) {
  const navigate = useNavigate()

  const handleRetryWithToken = () => {
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
      action: 'Enter Access Token',
      showTokenHelp: true,
      customAction: handleRetryWithToken
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
          <p className="text-gray-400 mb-6">{errorConfig.message}</p>
          {errorConfig.showTokenHelp && (
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-6 text-left">
              <p className="text-sm text-gray-300 mb-2"><strong>How to get a token:</strong></p>
              <ol className="text-sm text-gray-400 space-y-1 list-decimal list-inside">
                <li>Go to Settings → Developer settings</li>
                <li>Generate new token (classic)</li>
                <li>Select 'repo' scope</li>
                <li>Copy and paste in the form</li>
              </ol>
            </div>
          )}
          <button
            onClick={errorConfig.customAction || onRetry}
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
        <h2 className="text-xl font-semibold text-white text-center mb-2">Analysis Failed</h2>
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