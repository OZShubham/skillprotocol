import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, Clock, AlertCircle, XCircle, Shield, Terminal, CheckCircle2, BookOpen, Loader2, ChevronDown, ChevronUp, Eye } from 'lucide-react'
import { api } from '../services/api' 
import { useNavigate } from 'react-router-dom'

const AGENT_STEPS = [
  { key: 'validator', name: 'Validator', desc: 'Checking repository...', icon: Shield },
  { key: 'scanner', name: 'Scanner', desc: 'Analyzing code...', icon: Terminal },
 
  { key: 'grader', name: 'Grader', desc: 'Assessing SFIA level...', icon: CheckCircle2 },
  { key: 'judge', name: 'Judge', desc: 'Deliberating verdict...', icon: Shield },
  { key: 'auditor', name: 'Auditor', desc: 'Reality check...', icon: CheckCircle2 },
  { key: 'mentor', name: 'Mentor', desc: 'Creating growth plan...', icon: BookOpen },
  { key: 'reporter', name: 'Reporter', desc: 'Finalizing credits...', icon: Check }
]

export default function AnalysisPage({ jobId, onComplete, onError }) {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [validationError, setValidationError] = useState(null)
  const [liveLogs, setLiveLogs] = useState([])
  const [expandedAgent, setExpandedAgent] = useState(null)
  const [streamClosed, setStreamClosed] = useState(false)

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
          setStreamClosed(true) // Mark stream as should be closed
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

  // SSE for live logs - ENHANCED with proper closure
  useEffect(() => {
    if (!jobId || status?.status === 'complete' || streamClosed) return

    const eventSource = new EventSource(`http://localhost:8000/api/stream/${jobId}`)
    let reconnectAttempts = 0
    const maxReconnects = 3

    eventSource.onmessage = (event) => {
      try {
        const newLog = JSON.parse(event.data)
        
        // ✅ CRITICAL FIX: Close stream when complete event received
        if (newLog.event === 'complete') {
          console.log('✅ Stream completion event received')
          eventSource.close()
          setStreamClosed(true)
          return
        }

        setLiveLogs((prev) => [newLog, ...prev].slice(0, 100))
        
        // Auto-expand active agent
        if (newLog.agent && !expandedAgent) {
          setExpandedAgent(newLog.agent)
        }

        // Auto-collapse previous agent when new one starts
        if (newLog.agent && expandedAgent && newLog.agent !== expandedAgent) {
          setExpandedAgent(newLog.agent)
        }
      } catch (err) {
        console.error("SSE Parse Error:", err)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE Error:', error)
      
      // Don't reconnect if already complete
      if (status?.status === 'complete' || streamClosed) {
        eventSource.close()
        return
      }

      // Limit reconnection attempts
      reconnectAttempts++
      if (reconnectAttempts >= maxReconnects) {
        console.log('Max reconnection attempts reached')
        eventSource.close()
      }
    }

    return () => {
      console.log('Cleaning up SSE connection')
      eventSource.close()
    }
  }, [jobId, status?.status, streamClosed, expandedAgent])

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
          <h1 className="text-4xl font-bold text-text-main mb-4">
            Analyzing Your Repository
          </h1>
          <p className="text-text-muted">
            Our AI agents are working together to verify your skills
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-panel/80 backdrop-blur-xl border border-border rounded-2xl p-8 mb-8 shadow-2xl"
        >
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-text-muted font-mono uppercase tracking-wider">Overall Progress</span>
              <span className="text-primary font-bold font-mono">{status.progress}%</span>
            </div>
            <div className="h-3 bg-surface rounded-full overflow-hidden border border-border">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${status.progress}%` }}
                transition={{ duration: 0.5 }}
                className="h-full bg-primary rounded-full shadow-[0_0_10px_var(--color-primary)]"
              />
            </div>
          </div>

          {/* Agent Steps with Expandable Activity */}
          <div className="space-y-3">
            {AGENT_STEPS.map((step, index) => {
              const isActive = status.current_step === step.key
              const isComplete = AGENT_STEPS.findIndex(s => s.key === status.current_step) > index
              const agentLogs = logsByAgent[step.key] || []
              const Icon = step.icon

              return (
                <div key={step.key}>
                  <motion.button
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    onClick={() => setExpandedAgent(expandedAgent === step.key ? null : step.key)}
                    className={`w-full flex items-center gap-4 p-4 rounded-xl transition-all border ${
                      isActive
                        ? 'bg-primary/5 border-primary/30 shadow-[0_0_15px_rgba(245,158,11,0.1)]'
                        : isComplete
                        ? 'bg-success/5 border-success/30'
                        : 'bg-surface/50 border-border opacity-60'
                    }`}
                  >
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${
                      isActive
                        ? 'bg-primary/10 border-primary/20'
                        : isComplete
                        ? 'bg-success/10 border-success/20'
                        : 'bg-surface border-border'
                    }`}>
                      {isComplete ? (
                        <Check className="w-5 h-5 text-success" />
                      ) : isActive ? (
                        <Loader2 className="w-5 h-5 text-primary animate-spin" />
                      ) : (
                        <Clock className="w-5 h-5 text-text-dim" />
                      )}
                    </div>

                    <div className="flex-1 text-left">
                      <div className="flex items-center gap-2 mb-1">
                        <Icon className={`w-4 h-4 ${isActive ? 'text-primary' : 'text-text-muted'}`} />
                        <h3 className={`font-semibold ${
                          isActive || isComplete ? 'text-text-main' : 'text-text-dim'
                        }`}>
                          {step.name}
                        </h3>
                        {isActive && (
                          <span className="text-[10px] bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded uppercase tracking-widest font-bold animate-pulse">
                            Processing
                          </span>
                        )}
                      </div>
                      <p className={`text-sm ${
                        isActive || isComplete ? 'text-text-muted' : 'text-text-dim'
                      }`}>
                        {step.desc}
                      </p>
                    </div>

                    {agentLogs.length > 0 && (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-text-dim font-mono">{agentLogs.length} logs</span>
                        {expandedAgent === step.key ? <ChevronUp className="w-4 h-4 text-text-muted" /> : <ChevronDown className="w-4 h-4 text-text-muted" />}
                      </div>
                    )}
                  </motion.button>

                  {/* Expandable Activity Log (Terminal Look) */}
                  <AnimatePresence>
                    {expandedAgent === step.key && agentLogs.length > 0 && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-2 ml-14 p-4 bg-void border border-border rounded-lg space-y-2 font-mono text-xs shadow-inner max-h-64 overflow-y-auto">
                          {agentLogs.slice(0, 15).map((log, i) => (
                            <div key={i} className="flex gap-3">
                              <span className="text-text-dim shrink-0">
                                [{new Date(log.timestamp).toLocaleTimeString([], {hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit'})}]
                              </span>
                              <span className={`${log.status === 'error' ? 'text-error' : 'text-success'}`}>
                                &gt; {log.thought}
                              </span>
                            </div>
                          ))}
                          {agentLogs.length > 15 && (
                            <div className="text-text-dim italic pt-2 border-t border-border">
                              +{agentLogs.length - 15} more logs
                            </div>
                          )}
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

// --- SUBCOMPONENTS (Theme Adjusted) ---

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
      icon: <XCircle className="w-12 h-12 text-error" />,
      action: 'Try Again'
    },
    'PRIVATE_REPO': {
      title: 'Private Repository',
      message: 'This repository is private. We need a token to access it.',
      icon: <Shield className="w-12 h-12 text-primary" />,
      action: 'Enter Access Token',
      showTokenHelp: true,
      customAction: handleRetryWithToken
    },
    'SIZE_EXCEEDED': {
      title: 'Repo Too Large',
      message: `Repository size (${validation.size_kb} KB) exceeds the limit.`,
      icon: <AlertCircle className="w-12 h-12 text-primary" />,
      action: 'Try Smaller Repo'
    },
    'EMPTY_REPO': {
      title: 'Empty Repository',
      message: 'This repository has no code.',
      icon: <AlertCircle className="w-12 h-12 text-text-muted" />,
      action: 'Go Back'
    },
    'RATE_LIMIT': {
      title: 'Rate Limit',
      message: 'GitHub API limits reached. Try again later.',
      icon: <Clock className="w-12 h-12 text-primary" />,
      action: 'Try Later'
    }
  }

  const errorType = validation.error_type || 'UNKNOWN'
  const errorConfig = errorMessages[errorType] || {
    title: 'Validation Failed',
    message: validation.error || 'Unknown error occurred',
    icon: <AlertCircle className="w-12 h-12 text-error" />,
    action: 'Try Again'
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-panel border border-error/30 rounded-2xl p-8 max-w-md shadow-2xl"
      >
        <div className="text-center">
          {errorConfig.icon}
          <h2 className="text-2xl font-bold text-text-main mt-4 mb-2">
            {errorConfig.title}
          </h2>
          <p className="text-text-muted mb-6">{errorConfig.message}</p>
          
          {errorConfig.showTokenHelp && (
            <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mb-6 text-left">
              <p className="text-sm text-text-main mb-2 font-bold">How to get a token:</p>
              <ol className="text-sm text-text-muted space-y-1 list-decimal list-inside">
                <li>GitHub Settings → Developer settings</li>
                <li>Generate new token (Classic)</li>
                <li>Select 'repo' scope</li>
                <li>Paste in the input field</li>
              </ol>
            </div>
          )}
          
          <button
            onClick={errorConfig.customAction || onRetry}
            className="w-full bg-primary hover:brightness-110 text-black font-bold py-3 rounded-lg transition-all"
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
        className="bg-panel border border-error/30 rounded-2xl p-8 max-w-md shadow-xl"
      >
        <AlertCircle className="w-12 h-12 text-error mx-auto mb-4" />
        <h2 className="text-xl font-bold text-text-main text-center mb-2">Analysis Failed</h2>
        <p className="text-text-muted text-center mb-6">{error}</p>
        <button
          onClick={onRetry}
          className="w-full bg-surface border border-border hover:bg-panel text-text-main font-medium py-2 rounded-lg transition-colors"
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
        <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
        <p className="text-text-muted font-mono animate-pulse">Connecting to Agent Swarm...</p>
      </div>
    </div>
  )
}