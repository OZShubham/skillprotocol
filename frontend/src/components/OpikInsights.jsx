
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, AreaChart, Area } from 'recharts'
import { 
  Activity, TrendingUp, Shield, Zap, ExternalLink, 
  CheckCircle2, AlertTriangle, Target, BrainCircuit, 
  Award, ThumbsUp, ThumbsDown, BarChart3, Microscope, ChevronRight
} from 'lucide-react'
import { api } from '../services/api'

export default function OpikInsights({ result, onAgentSelect }) {
  const [metrics, setMetrics] = useState(null)
  const [dashboardStats, setDashboardStats] = useState(null)
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [showAgentDetails, setShowAgentDetails] = useState(false)

  useEffect(() => {
    // 1. Fetch Global Stats
    const loadGlobalStats = async () => {
      const stats = await api.getOpikStats()
      if (stats) setDashboardStats(stats)
    }
    loadGlobalStats()

    // 2. Parse Local Result
    if (result) {
      const confidence = result?.sfia_result?.confidence || 0.85
      const realityCheck = result?.audit_result?.reality_check_passed || false
      const validation = result?.validation_result || result?.sfia_result?.bayesian_validation

      setMetrics({
        confidence_score: confidence,
        reality_check: realityCheck,
        bayesian_validation: validation ? {
          confidence: validation.confidence || 0,
          bayesian_best: validation.bayesian_best_estimate || validation.bayesian_best,
          alert: validation.alert || false,
          reasoning: validation.reasoning || 'Statistical analysis indicates alignment.',
          expected_range: validation.expected_range || []
        } : null,
        agent_health: {
          validator: 1.0,
          scanner: result.scan_metrics ? 1.0 : 0.0,
          grader: confidence,
          judge: result.sfia_result?.judge_intervened ? 0.8 : 1.0,
          auditor: realityCheck ? 1.0 : 0.5
        }
      })
    }
  }, [result])

  // Handle agent click
  const handleAgentClick = (agentName) => {
    setSelectedAgent(agentName)
    setShowAgentDetails(true)
    if (onAgentSelect) onAgentSelect(agentName)
  }

  // Loading State
  if (!metrics) return (
    <div className="h-64 flex flex-col items-center justify-center space-y-4 animate-pulse p-8 border border-white/5 rounded-xl bg-white/5">
      <div className="w-12 h-12 bg-white/10 rounded-full"></div>
      <div className="text-text-dim text-sm font-mono tracking-widest">SYNCING OPIK TELEMETRY...</div>
    </div>
  )

  const bVal = metrics.bayesian_validation

  return (
    <div className="space-y-6">
      
      {/* --- HERO: OPTIMIZATION ENGINE STATUS --- */}
      {dashboardStats && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-[#0F172A] to-[#1E1B4B] border border-blue-500/20 rounded-xl p-6 relative overflow-hidden group"
        >
          {/* Animated Background */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:20px_20px] opacity-20" />
          <div className="absolute -right-10 -top-10 w-40 h-40 bg-blue-500/20 rounded-full blur-[50px] group-hover:bg-blue-500/30 transition-all duration-1000" />

          <div className="relative z-10 flex justify-between items-end">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="px-2 py-0.5 rounded bg-blue-500/20 border border-blue-500/30 text-blue-400 text-[10px] font-mono tracking-widest uppercase flex items-center gap-2">
                  <Award className="w-3 h-3" />
                  Opik Optimizer
                </div>
                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-green-900/30 border border-green-500/30 text-green-400 text-[10px] font-mono">
                  <span className="relative flex h-1.5 w-1.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-green-500"></span>
                  </span>
                  ONLINE
                </div>
              </div>
              
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold text-white tracking-tighter">
                  +{dashboardStats.improvement_percentage.toFixed(1)}%
                </span>
                <span className="text-sm text-text-muted mb-1 font-mono uppercase tracking-wide">Accuracy Gain</span>
              </div>
            </div>

            <div className="text-right hidden sm:block">
              <div className="text-xs text-text-dim font-mono mb-1 uppercase tracking-wider">Current Accuracy</div>
              <div className="text-2xl font-bold text-green-400 font-mono-nums">
                {(dashboardStats.current_accuracy * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* --- ANALYSIS METRICS GRID --- */}
      <div className="grid grid-cols-3 gap-3">
        <MetricCard 
          value={`${((metrics?.confidence_score ?? 0) * 100).toFixed(0)}%`}
          label="LLM Certainty"
          status={metrics.confidence_score >= 0.85 ? 'good' : 'warning'}
          icon={<BrainCircuit className="w-4 h-4" />}
          delay={0.1}
        />
        <MetricCard 
          value={bVal ? (bVal.alert ? "REVIEW" : "VERIFIED") : "N/A"}
          label="Bayesian Guard"
          status={bVal ? (bVal.alert ? 'error' : 'good') : 'neutral'}
          icon={<Target className="w-4 h-4" />}
          delay={0.2}
          subValue={bVal?.confidence ? `${((bVal?.confidence ?? 0) * 100).toFixed(0)}% Prob.` : null}
        />
        <MetricCard 
          value={metrics.reality_check ? "PASS" : "FAIL"}
          label="Reality Check"
          status={metrics.reality_check ? 'good' : 'error'}
          icon={<Shield className="w-4 h-4" />}
          delay={0.3}
        />
      </div>

      {/* --- INTERACTIVE AGENT BREAKDOWN (FIXED) --- */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-text-muted uppercase tracking-wider flex items-center gap-2">
            <Microscope className="w-4 h-4" />
            Agent Diagnostics
          </h4>
          {selectedAgent && (
            <button 
              onClick={() => setShowAgentDetails(!showAgentDetails)}
              className="text-xs text-primary hover:text-yellow-400 transition-colors flex items-center gap-1"
            >
              {showAgentDetails ? 'Hide Details' : 'Show Details'}
              <ChevronRight className={`w-3 h-3 transition-transform ${showAgentDetails ? 'rotate-90' : ''}`} />
            </button>
          )}
        </div>

        {/* Agent Bars */}
        <div className="grid grid-cols-1 gap-2">
          {Object.entries(metrics.agent_health).map(([agent, health]) => (
            <AgentHealthBar 
              key={agent} 
              agent={agent} 
              health={health} 
              onClick={() => handleAgentClick(agent)}
              isSelected={selectedAgent === agent}
            />
          ))}
        </div>

        {/* Agent Details Panel */}
        <AnimatePresence>
          {showAgentDetails && selectedAgent && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-void border border-dashed border-border rounded-xl p-6 overflow-hidden"
            >
              <AgentDetailsView agent={selectedAgent} result={result} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* --- LIVE CHARTS --- */}
      {dashboardStats && (
        <div className="grid grid-cols-1 gap-4">
          
          {/* A/B Test Results */}
          {dashboardStats.ab_test_results?.experiment_name && (
            <div className="bg-[#0A0A0A] border border-white/10 rounded-xl p-5">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-text-muted" />
                  <span className="text-xs font-bold text-text-muted uppercase tracking-wider">Live A/B Experiment</span>
                </div>
                <span className="text-[10px] bg-green-500/10 text-green-400 px-2 py-0.5 rounded border border-green-500/20 font-mono">
                  WINNER: {dashboardStats.ab_test_results.winner === 'b' ? 'VARIANT B' : 'BASELINE'}
                </span>
              </div>
              
              <div className="space-y-4">
                <ABBar 
                  label="Baseline (Prompt V1)" 
                  value={dashboardStats.ab_test_results.variant_a.success_rate} 
                  winner={dashboardStats.ab_test_results.winner === 'a'}
                />
                <ABBar 
                  label="Bayesian Anchored (Prompt V2)" 
                  value={dashboardStats.ab_test_results.variant_b.success_rate} 
                  winner={dashboardStats.ab_test_results.winner === 'b'} 
                  color="bg-blue-500"
                />
              </div>
            </div>
          )}

          {/* Quality Trend Chart */}
          {dashboardStats.quality_trend?.length > 0 && (
            <div className="bg-[#0A0A0A] border border-white/10 rounded-xl p-5 h-48">
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="w-4 h-4 text-text-muted" />
                <span className="text-xs font-bold text-text-muted uppercase tracking-wider">Quality Trend (24h)</span>
              </div>
              <ResponsiveContainer width="100%" height="80%">
                <AreaChart data={dashboardStats.quality_trend}>
                  <defs>
                    <linearGradient id="colorAccuracy" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#121212', border: '1px solid #333', borderRadius: '8px', fontSize: '12px', color: '#fff' }}
                    itemStyle={{ color: '#10B981' }}
                    labelStyle={{ color: '#666' }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="accuracy" 
                    stroke="#10B981" 
                    fillOpacity={1} 
                    fill="url(#colorAccuracy)" 
                    strokeWidth={2}
                    animationDuration={1500}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* --- FOOTER LINK --- */}
      {result?.opik_trace_url && (
        <a 
          href={result.opik_trace_url}
          target="_blank"
          rel="noopener noreferrer"
          className="group flex items-center justify-center gap-2 w-full py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-mono text-text-muted hover:text-white transition-all duration-300"
        >
          <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
          INSPECT FULL TRACE IN OPIK
        </a>
      )}
    </div>
  )
}

// --- NEW: AGENT DETAILS VIEW ---
function AgentDetailsView({ agent, result }) {
  const getAgentInfo = () => {
    switch(agent) {
      case 'validator':
        return {
          thought: result.validation?.is_valid 
            ? `✓ Repository validated: ${result.validation?.size_kb}KB, ${result.validation?.language}`
            : '✗ Validation failed',
          data: result.validation
        }
      case 'scanner':
        return {
          thought: `Parsed ${result.scan_metrics?.ncrf?.files_scanned || 0} files. SLOC: ${result.scan_metrics?.ncrf?.total_sloc || 0}`,
          data: result.scan_metrics
        }
      case 'grader':
        return {
          thought: result.sfia_result?.reasoning || 'Assessment in progress',
          data: result.sfia_result
        }
      case 'judge':
        return {
          thought: result.sfia_result?.judge_intervened 
            ? `⚖️ Intervened: ${result.sfia_result?.judge_ruling}` 
            : '✓ Verdict affirmed',
          data: result.sfia_result
        }
      case 'auditor':
        return {
          thought: result.audit_result?.reality_check_passed 
            ? '✓ GitHub Actions passing' 
            : '✗ CI/CD checks failed',
          data: result.audit_result
        }
      default:
        return { thought: 'No data available', data: {} }
    }
  }

  const info = getAgentInfo()

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
          <span className="text-primary text-sm font-bold uppercase">{agent[0]}</span>
        </div>
        <div>
          <div className="text-sm font-bold text-white uppercase tracking-wide">{agent} Agent</div>
          <div className="text-xs text-text-dim">Internal reasoning trace</div>
        </div>
      </div>

      <div className="bg-black/30 border border-white/5 rounded-lg p-4">
        <div className="text-xs font-mono text-text-muted mb-2">THOUGHT PROCESS:</div>
        <div className="text-sm text-white leading-relaxed">{info.thought}</div>
      </div>

      <details className="group">
        <summary className="cursor-pointer text-xs text-text-dim hover:text-white transition-colors flex items-center gap-2">
          <ChevronRight className="w-3 h-3 group-open:rotate-90 transition-transform" />
          View Raw Data
        </summary>
        <pre className="mt-2 p-3 bg-black/50 border border-white/5 rounded text-xs text-text-dim overflow-x-auto">
          {JSON.stringify(info.data, null, 2)}
        </pre>
      </details>
    </div>
  )
}

// --- SUB COMPONENTS ---

function MetricCard({ value, label, status, icon, delay, subValue }) {
  const styles = {
    good: 'border-green-500/20 bg-green-500/5 text-green-400',
    warning: 'border-yellow-500/20 bg-yellow-500/5 text-yellow-400',
    error: 'border-red-500/20 bg-red-500/5 text-red-400',
    neutral: 'border-white/10 bg-white/5 text-text-muted'
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={`border rounded-xl p-4 flex flex-col items-center justify-center text-center ${styles[status]}`}
    >
      <div className="mb-2 opacity-80 p-2 bg-black/20 rounded-full">{icon}</div>
      <div className="text-xl font-bold font-mono-nums tracking-tight">{value}</div>
      {subValue && <div className="text-[10px] opacity-70 font-mono mt-0.5">{subValue}</div>}
      <div className="text-[10px] opacity-60 uppercase tracking-widest mt-1 font-semibold">{label}</div>
    </motion.div>
  )
}

function ABBar({ label, value, winner, color = "bg-white" }) {
  return (
    <div>
      <div className="flex justify-between text-[10px] mb-1.5 uppercase font-bold tracking-wider">
        <span className={winner ? "text-white" : "text-text-dim"}>
          {label} {winner && "👑"}
        </span>
        <span className="font-mono text-text-muted">{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${value * 100}%` }}
          transition={{ duration: 1, delay: 0.5 }}
          className={`h-full rounded-full ${winner ? color : 'bg-text-dim'}`}
        />
      </div>
    </div>
  )
}

function AgentHealthBar({ agent, health, onClick, isSelected }) {
  const healthPercentage = health * 100
  let barColor = 'bg-green-500'
  if (health < 0.9) barColor = 'bg-yellow-500'
  if (health < 0.7) barColor = 'bg-red-500'

  return (
    <button 
      onClick={onClick}
      className={`w-full bg-surface hover:bg-white/5 border rounded-lg p-2 transition-all group text-left ${
        isSelected ? 'border-primary/50 bg-primary/5' : 'border-border'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className={`text-xs font-mono uppercase ${isSelected ? 'text-primary' : 'text-white group-hover:text-primary'} transition-colors`}>
          {agent}
        </span>
        <span className="text-xs font-mono text-text-muted">{healthPercentage.toFixed(0)}%</span>
      </div>
      <div className="h-1 bg-void rounded-full overflow-hidden">
        <div className={`h-full ${barColor} rounded-full`} style={{ width: `${healthPercentage}%` }} />
      </div>
    </button>
  )
}