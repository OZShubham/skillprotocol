import { motion } from 'framer-motion'
import { Award, ExternalLink, Download, Share2, CheckCircle, Code, Shield, MessageSquare, ThumbsUp, ThumbsDown, AlertCircle, CheckCircle2 } from 'lucide-react'
import confetti from 'canvas-confetti'
import { useEffect, useState } from 'react'
import { api } from '../services/api'
import AgentDiagnostics from './AgentDiagnostics' // The new robust component

export default function CreditCertificate({ result, onViewDashboard }) {
  
  useEffect(() => {
    // Fire confetti on load
    confetti({
      particleCount: 150,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#F59E0B', '#FFFFFF', '#10B981']
    })
  }, [])

  // Dynamic colors based on SFIA level
  const sfiaLevelColors = {
    1: 'text-text-muted border-border',
    2: 'text-blue-400 border-blue-500/50',
    3: 'text-success border-success/50',
    4: 'text-primary border-primary/50',
    5: 'text-purple-400 border-purple-500/50'
  }

  const levelColorClass = sfiaLevelColors[result.sfia_level] || 'text-primary border-primary/50'

  // Download JSON logic
  const handleDownload = () => {
    const dataStr = JSON.stringify(result, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    const exportFileDefaultName = `skillprotocol-certificate-${result.verification_id}.json`
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  // Share logic
  const handleShare = async () => {
    const shareData = {
      title: 'SkillProtocol Certificate',
      text: `I just earned ${result.final_credits} verified skill credits at SFIA Level ${result.sfia_level}!`,
      url: window.location.href
    }
    try {
      if (navigator.share) {
        await navigator.share(shareData)
      } else {
        await navigator.clipboard.writeText(`${shareData.text}\n${shareData.url}`)
        alert('Link copied to clipboard!')
      }
    } catch (err) {
      console.error('Share failed:', err)
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="max-w-5xl w-full">
        
        {/* Success Message */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="w-16 h-16 bg-success/10 border border-success/30 rounded-full flex items-center justify-center mx-auto mb-6"
          >
            <CheckCircle className="w-8 h-8 text-success" />
          </motion.div>
          <h1 className="text-4xl font-bold text-text-main mb-3 tracking-tight">
            Verification Complete
          </h1>
          <p className="text-text-muted max-w-lg mx-auto">
            Repository analysis finished successfully. Skill credits have been minted and cryptographically signed.
          </p>
        </motion.div>

        {/* Certificate Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="bg-panel border border-border rounded-2xl overflow-hidden shadow-2xl relative"
        >
          <div className="h-1 w-full bg-gradient-to-r from-void via-primary to-void opacity-50" />

          {/* Certificate Header */}
          <div className="p-8 md:p-10 border-b border-border bg-surface/30">
            <div className="flex flex-col md:flex-row justify-between items-start gap-6">
              <div className="flex items-center gap-5">
                <div className="w-16 h-16 bg-surface border border-border rounded-xl flex items-center justify-center">
                  <Award className="w-8 h-8 text-text-main" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-text-main mb-1">Verified Skill Credits</h2>
                  <div className="flex items-center gap-2 text-sm text-text-muted font-mono">
                    <span>ID: {result.verification_id?.slice(0, 12)}...</span>
                    <span className="w-1 h-1 bg-text-dim rounded-full" />
                    <span>{new Date(result.started_at || Date.now()).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
              
              <div className="text-right bg-surface border border-border px-6 py-4 rounded-xl">
                <div className="text-5xl font-bold text-text-main font-mono-nums tracking-tighter">
                  {result.final_credits?.toFixed(2)}
                </div>
                <div className="text-xs text-text-muted font-mono uppercase tracking-widest mt-1">Total Credits</div>
              </div>
            </div>
          </div>

          {/* Certificate Body */}
          <div className="p-8 md:p-10 space-y-10">
            
            {/* SFIA Assessment */}
            <div>
              <h3 className="text-sm font-mono text-text-muted uppercase tracking-wider mb-6 flex items-center gap-2">
                <Shield className="w-4 h-4 text-primary" />
                SFIA Assessment
              </h3>
              <div className="grid md:grid-cols-3 gap-6">
                <div className={`col-span-1 bg-surface border rounded-xl p-6 flex flex-col justify-center items-center text-center ${levelColorClass}`}>
                  <div className="text-6xl font-bold font-mono mb-2">{result.sfia_level}</div>
                  <div className="text-lg font-medium text-text-main">{result.sfia_level_name}</div>
                  <div className="text-xs text-text-dim uppercase mt-1 tracking-widest">Proficiency Level</div>
                </div>
                
                <div className="col-span-2 bg-surface border border-border rounded-xl p-6 flex items-center">
                  <div>
                    <div className="text-sm text-text-dim font-mono mb-2">ASSESSMENT CRITERIA</div>
                    <div className="text-text-muted leading-relaxed">
                      {getLevelDescription(result.sfia_level)}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Code Analysis Metrics */}
            <div>
              <h3 className="text-sm font-mono text-text-muted uppercase tracking-wider mb-6 flex items-center gap-2">
                <Code className="w-4 h-4 text-primary" />
                Code Analysis
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard 
                  label="Total SLOC" 
                  value={result.scan_metrics?.ncrf?.total_sloc?.toLocaleString() || 'N/A'} 
                  sub="Lines of Code"
                />
                <MetricCard 
                  label="Learning Hours" 
                  value={result.scan_metrics?.ncrf?.estimated_learning_hours || 'N/A'} 
                  sub="NCrF Standard"
                />
                <MetricCard 
                  label="Files Scanned" 
                  value={result.scan_metrics?.ncrf?.files_scanned || 'N/A'} 
                  sub="Code Files" 
                  highlight
                />
                <MetricCard 
                  label="Reality Check" 
                  value={
                    result.audit_result?.has_ci_cd === false 
                      ? "N/A" 
                      : (result.audit_result?.reality_check_passed ? "PASS" : "FAIL")
                  } 
                  sub={
                    result.audit_result?.has_ci_cd === false 
                      ? "No CI/CD" 
                      : "GitHub Actions"
                  }
                  isSuccess={
                    result.audit_result?.has_ci_cd === false 
                      ? null 
                      : result.audit_result?.reality_check_passed
                  }
                />
              </div>
            </div>

            {/* Language Breakdown (Kept from original) */}
            {result.scan_metrics?.ncrf?.language_stats && (
              <div>
                <h3 className="text-sm font-mono text-text-muted uppercase tracking-wider mb-4 flex items-center gap-2">
                  <Code className="w-4 h-4 text-primary" />
                  Language Composition
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(result.scan_metrics.ncrf.language_stats)
                    .sort((a, b) => b[1].sloc - a[1].sloc)
                    .map(([lang, stats]) => (
                      <div key={lang} className="bg-surface border border-border rounded-lg p-3">
                        <div className="text-xs text-text-dim uppercase mb-1">{lang}</div>
                        <div className="text-xl font-bold text-text-main font-mono-nums">
                          {((stats.sloc / result.scan_metrics.ncrf.total_sloc) * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-text-muted">{stats.sloc} SLOC</div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Evidence Badges (Kept from original) */}
            <div className="p-6 bg-surface border border-border rounded-xl">
              <div className="text-xs text-text-dim font-mono mb-4 uppercase">Detected Markers</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(result.scan_metrics?.markers || {}).map(([key, value]) => {
                  if (key === 'code_samples') return null
                  return <EvidenceBadge key={key} label={formatMarkerName(key)} present={value} />
                })}
              </div>
            </div>

            {/* NEW: Agent Diagnostics / Evidence Chain */}
            <div className="bg-surface/30 border border-border rounded-xl p-6">
               <AgentDiagnostics result={result} />
            </div>

            {/* Feedback Section (Kept and Styled) */}
            <FeedbackSection jobId={result.verification_id || result.job_id || result.id} />

            {/* Proof Links */}
            {result.opik_trace_url && (
              <div className="flex justify-center">
                <a 
                  href={result.opik_trace_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-text-muted hover:text-primary transition-colors border border-border px-4 py-2 rounded-lg bg-surface hover:bg-panel"
                >
                  <ExternalLink className="w-4 h-4" />
                  View Immutable Trace in Opik
                </a>
              </div>
            )}

            {/* Actions Footer */}
            <div className="flex flex-col sm:flex-row gap-4 pt-6 border-t border-border">
              <button 
                onClick={onViewDashboard}
                className="flex-1 bg-primary hover:brightness-110 text-black font-bold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/20"
              >
                Go to Dashboard
              </button>
              <button 
                onClick={handleDownload}
                className="bg-surface hover:bg-border text-text-main border border-border font-medium py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <Download className="w-4 h-4" />
                Download JSON
              </button>
              <button 
                onClick={handleShare}
                className="bg-surface hover:bg-border text-text-main border border-border font-medium py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <Share2 className="w-4 h-4" />
                Share
              </button>
            </div>

          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-6 text-center"
        >
          <p className="text-text-muted text-sm font-mono">
            Repository: <span className="text-text-main">{result.repo_url}</span>
          </p>
        </motion.div>
      </div>
    </div>
  )
}

// --- SUBCOMPONENTS (METRIC CARDS, BADGES, FEEDBACK) ---

function FeedbackSection({ jobId }) {
  const [status, setStatus] = useState('idle')
  const [selectedScore, setSelectedScore] = useState(null)

  const handleSubmit = async (score) => {
    if (status === 'submitting' || status === 'success') return
    setStatus('submitting')
    setSelectedScore(score)

    try {
      await api.submitFeedback(
        jobId,
        score,
        score === 1 ? "Verified by user" : "Disputed by user"
      )
      setTimeout(() => setStatus('success'), 800)
    } catch (e) {
      console.error('Feedback error:', e)
      setStatus('error')
      setTimeout(() => setStatus('idle'), 3000)
    }
  }

  if (status === 'success') {
    return (
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="p-6 bg-success/10 border border-success/20 rounded-xl flex items-center justify-center gap-3 text-success"
      >
        <CheckCircle className="w-5 h-5" />
        <span className="font-medium">Feedback recorded. Thank you.</span>
      </motion.div>
    )
  }

  return (
    <div className="bg-surface border border-border rounded-xl p-6 relative overflow-hidden">
      <div className="flex flex-col md:flex-row items-center justify-between gap-6 relative z-10">
        <div>
          <h3 className="text-sm font-bold text-text-main flex items-center gap-2 mb-1">
            <MessageSquare className="w-4 h-4 text-primary" />
            Human Verification
          </h3>
          <p className="text-xs text-text-muted">
            Do you agree with the AI Judge's assessment?
          </p>
        </div>

        <div className="flex gap-3">
          <button 
            onClick={() => handleSubmit(1)}
            disabled={status === 'submitting'}
            className="group flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-panel hover:border-success/50 hover:bg-success/5 transition-all"
          >
            <ThumbsUp className={`w-4 h-4 ${selectedScore === 1 ? 'text-success fill-success' : 'text-text-muted group-hover:text-success'}`} />
            <span className="text-sm font-medium text-text-muted group-hover:text-text-main">Agree</span>
          </button>

          <button 
            onClick={() => handleSubmit(0)}
            disabled={status === 'submitting'}
            className="group flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-panel hover:border-error/50 hover:bg-error/5 transition-all"
          >
            <ThumbsDown className={`w-4 h-4 ${selectedScore === 0 ? 'text-error fill-error' : 'text-text-muted group-hover:text-error'}`} />
            <span className="text-sm font-medium text-text-muted group-hover:text-text-main">Disagree</span>
          </button>
        </div>
      </div>
    </div>
  )
}

function MetricCard({ label, value, sub, highlight, isSuccess }) {
  let valueColor = 'text-text-main'
  if (highlight) valueColor = 'text-primary'
  if (isSuccess === true) valueColor = 'text-success'
  if (isSuccess === false) valueColor = 'text-error'

  return (
    <div className="bg-surface border border-border p-4 rounded-xl">
      <div className="text-xs text-text-dim font-mono uppercase mb-2">{label}</div>
      <div className={`text-2xl font-bold font-mono-nums ${valueColor}`}>{value}</div>
      <div className="text-xs text-text-muted mt-1">{sub}</div>
    </div>
  )
}

function EvidenceBadge({ label, present }) {
  return (
    <div className={`px-3 py-1.5 rounded text-xs font-mono border transition-all flex items-center gap-2 ${
      present
        ? 'bg-success/10 text-success border-success/30'
        : 'bg-panel text-text-dim border-border opacity-50'
    }`}>
      {present ? <CheckCircle2 className="w-3 h-3" /> : <div className="w-3 h-3 rounded-full border border-text-dim" />}
      {label}
    </div>
  )
}

function getLevelDescription(level) {
  const descriptions = {
    1: "Basic syntax understanding. Can run simple scripts but lacks structural knowledge.",
    2: "Assist level. Can modify code and write simple functions but needs guidance.",
    3: "Professional baseline. Modular code, basic testing, and documentation. Works independently.",
    4: "Enable level. Uses advanced patterns (OOP, Async), writes unit tests, and handles errors robustly.",
    5: "Ensure level. Production-ready architecture with CI/CD, Containerization, and scalability patterns."
  }
  return descriptions[level] || descriptions[3]
}

function formatMarkerName(key) {
  return key.replace('has_', '').replace('uses_', '').replace(/_/g, ' ').toLowerCase()
}