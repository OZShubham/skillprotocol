import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { 
  ArrowRight, Github, ShieldCheck, Database, Search, 
  Cpu, Lock, Code2, Scale, Terminal, CheckCircle2, 
  Workflow, Zap, Binary, Layers 
} from 'lucide-react'
import { motion } from 'framer-motion'
import { api } from '../services/api'

export default function LandingPage({ onStartAnalysis, onUserDetected }) {
  const [repoUrl, setRepoUrl] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [showTokenInput, setShowTokenInput] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const location = useLocation()

  useEffect(() => {
    if (location.state?.requestToken) {
      setShowTokenInput(true)
      setError('Private repository detected. Token required.')
    }
    if (location.state?.repoUrl) {
      setRepoUrl(location.state.repoUrl)
    }
  }, [location.state])

  const extractOwner = (url) => {
    try {
      const clean = url.replace(/^https?:\/\/(www\.)?github\.com\//, '').replace(/^github\.com\//, '')
      const parts = clean.split('/')
      return parts[0] || null
    } catch (e) {
      return null
    }
  }

  const handleAnalyze = async () => {
    if (!repoUrl) {
      setError('Repository URL required')
      return
    }

    const owner = extractOwner(repoUrl)
    
    if (owner) {
      onUserDetected(owner) 
    } else {
      setError('Invalid GitHub URL')
      return
    }

    setLoading(true)
    setError('')

    try {
      const tokenToSend = githubToken.trim() || null
      const data = await api.analyzeRepo(repoUrl, owner, tokenToSend)
      onStartAnalysis(data.job_id)
    } catch (err) {
      const errorMsg = err.message || 'Analysis failed'
      if (errorMsg.toLowerCase().includes('private') || errorMsg.toLowerCase().includes('not found')) {
        setError(`Private repo detected. Access token needed for ${owner}.`)
        setShowTokenInput(true)
      } else {
        setError(errorMsg)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative overflow-hidden min-h-[calc(100vh-4rem)]">
      
      {/* Tighter Background Decor */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-primary/5 blur-[80px] rounded-full pointer-events-none" />

      <div className="max-w-6xl mx-auto px-4 py-12 relative z-10">
        
        {/* --- COMPACT HERO --- */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          
          <motion.div 
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md border border-primary/20 bg-primary/5 text-[10px] text-primary mb-4 font-mono font-bold tracking-tight uppercase"
          >
            <Zap className="w-3 h-3" />
            V2.0 STABLE
          </motion.div>
          
          <motion.h1 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-4xl md:text-6xl font-bold tracking-tight text-text-main mb-4 leading-tight"
          >
            Code to Credits. <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-orange-600">Mathematically Verified.</span>
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-base md:text-lg text-text-muted mb-8 leading-relaxed max-w-xl mx-auto"
          >
            The first <strong>Agentic Auditor</strong>. We parse your AST, anchor results with Bayesian statistics, and mint SFIA-standard credits backed by immutable proof traces.
          </motion.p>

          {/* COMPACT INPUT */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="flex flex-col gap-2 max-w-md mx-auto relative"
          >
            <div className="flex bg-panel border border-border p-1 rounded-lg shadow-lg shadow-primary/5 focus-within:border-primary/50 transition-all items-center">
              <div className="flex items-center pl-3 text-text-dim">
                <Github className="w-4 h-4" />
              </div>
              <input 
                type="text" 
                placeholder="github.com/username/repo"
                className="flex-1 bg-transparent border-none text-text-main px-3 py-2 focus:outline-none font-mono text-xs md:text-sm placeholder:text-text-dim"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
              />
              <button 
                onClick={handleAnalyze}
                disabled={loading}
                className="bg-primary hover:bg-orange-600 text-white font-bold px-4 py-1.5 rounded-md transition-colors flex items-center gap-1.5 disabled:opacity-50 text-xs shadow-sm"
              >
                {loading ? (
                  <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>Verify <ArrowRight className="w-3 h-3" /></>
                )}
              </button>
            </div>

            {/* Private Token Field */}
            {showTokenInput && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="bg-panel border border-primary/30 p-3 rounded-lg text-left shadow-sm"
              >
                <div className="flex items-center gap-2 mb-1.5 text-primary text-[10px] font-bold uppercase tracking-wide">
                  <Lock className="w-3 h-3" /> Private Access
                </div>
                <input 
                  type="password"
                  placeholder="ghp_... (Personal Access Token)"
                  className="w-full bg-surface border border-border text-text-main px-3 py-1.5 rounded focus:outline-none focus:border-primary/50 font-mono text-xs"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                />
              </motion.div>
            )}

            {error && (
              <div className="text-error text-[10px] font-mono bg-error/5 border border-error/20 p-2 rounded text-left flex items-center gap-2">
                <ShieldCheck className="w-3 h-3" /> {error}
              </div>
            )}
          </motion.div>
        </div>

        {/* --- THE AGENT SWARM (Grid) --- */}
        <div className="mb-16">
          <div className="flex items-center gap-4 mb-6">
            <div className="h-px bg-border flex-1" />
            <span className="text-[10px] font-mono text-text-dim uppercase tracking-widest bg-panel px-2 border border-border rounded">The Verification Chain</span>
            <div className="h-px bg-border flex-1" />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <AgentCard 
              name="Scanner" 
              role="Forensic Extraction" 
              desc="Clones repo, builds AST, counts SLOC & complexity nodes." 
              icon={Terminal} 
            />
            <AgentCard 
              name="Reviewer" 
              role="Semantic Analysis" 
              desc="Identifies architectural patterns (CQRS, MVC) & code smells." 
              icon={Search} 
            />
            <AgentCard 
              name="Grader" 
              role="SFIA Assessment" 
              desc="Maps technical metrics to SFIA Levels 1-5 capability scale." 
              icon={Scale} 
            />
            <AgentCard 
              name="Judge" 
              role="Arbitration" 
              desc="Resolves conflicts between statistical priors & agent findings." 
              icon={ShieldCheck} 
            />
            <AgentCard 
              name="Auditor" 
              role="Reality Check" 
              desc="Verifies GitHub Actions/CI logs to ensure code builds." 
              icon={CheckCircle2} 
            />
            <AgentCard 
              name="Reporter" 
              role="Minting" 
              desc="Calculates final credits & commits immutable Opik trace." 
              icon={Database} 
            />
          </div>
        </div>

        {/* --- LOGIC KERNEL (Terminal View) --- */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          {/* Left: The Math */}
          <div className="md:col-span-2 bg-panel border border-border rounded-xl p-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Binary className="w-32 h-32 text-text-dim" />
            </div>
            <h3 className="text-sm font-bold text-text-main mb-4 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-primary" />
              Scoring Logic
            </h3>
            <div className="font-mono text-[10px] md:text-xs text-text-dim bg-surface border border-border p-4 rounded-lg leading-relaxed">
              <span className="text-primary">// 1. NCrF Calculation</span><br/>
              base_credits = (sloc * complexity_weight) / 30_hours<br/><br/>
              <span className="text-primary">// 2. Multiplier Pipeline</span><br/>
              final_score = base<br/>
              &nbsp;&nbsp;* <span className="text-text-main">sfia_mult[level]</span> &nbsp;&nbsp;&nbsp;<span className="opacity-50"># 0.5x - 1.7x</span><br/>
              &nbsp;&nbsp;* <span className="text-text-main">quality_mult</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="opacity-50"># Static Analysis</span><br/>
              &nbsp;&nbsp;* <span className="text-text-main">reality_mult</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="opacity-50"># CI/CD Status (0.5x if fail)</span><br/><br/>
              <span className="text-success">&gt; VERIFIED_HASH: 0x7f...3a9</span>
            </div>
          </div>

          {/* Right: Bayesian Logic */}
          <div className="bg-panel border border-border rounded-xl p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-bold text-text-main mb-2 flex items-center gap-2">
                <Workflow className="w-4 h-4 text-purple-400" />
                Bayesian Guard
              </h3>
              <p className="text-xs text-text-muted leading-relaxed">
                We anchor LLM hallucinations using statistical priors.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-border space-y-2">
              <div className="flex justify-between text-[10px] text-text-dim">
                <span>Metrics Input</span>
                <span>Prior Probability</span>
              </div>
              <div className="h-1.5 w-full bg-surface rounded-full overflow-hidden">
                <div className="h-full bg-purple-500 w-[80%]" />
              </div>
              <div className="text-[10px] font-mono text-text-muted text-right">
                Confidence: 92.4%
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
<div className="mt-24 pt-10 border-t border-border text-center">
  <div className="flex justify-center gap-6 mb-6">
    <span className="text-text-dim hover:text-text-main cursor-pointer transition-colors">Manifesto</span>
    
    {/* ADD LINK HERE */}
    <a href="/methodology" className="text-text-dim hover:text-text-main cursor-pointer transition-colors">
      Methodology
    </a>
    
    <span className="text-text-dim hover:text-text-main cursor-pointer transition-colors">Opik</span>
  </div>
  <p className="text-text-dim text-xs font-mono">
    SECURED BY SKILLPROTOCOL · OPIK OBSERVABILITY · Multi LLM 
  </p>
</div>
      </div>
    </div>
  )
}

// Compact Card Component
function AgentCard({ name, role, desc, icon: Icon }) {
  return (
    <div className="bg-surface border border-border p-4 rounded-lg hover:border-primary/30 transition-colors group">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-8 h-8 rounded bg-panel border border-border flex items-center justify-center text-text-muted group-hover:text-primary transition-colors">
          <Icon className="w-4 h-4" />
        </div>
        <div>
          <div className="text-xs font-bold text-text-main">{name}</div>
          <div className="text-[10px] font-mono text-text-dim uppercase">{role}</div>
        </div>
      </div>
      <p className="text-[11px] text-text-muted leading-snug">
        {desc}
      </p>
    </div>
  )
}