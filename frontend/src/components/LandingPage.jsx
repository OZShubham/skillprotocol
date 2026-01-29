import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { 
  ArrowRight, Github, ShieldCheck, Database, Search, 
  Cpu, Lock, Code2, Scale, Terminal, CheckCircle2, 
  Workflow, Zap, Binary, Layers, BookOpen, TrendingUp,
  GitBranch
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
  const navigate = useNavigate()

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
    <div className="relative overflow-hidden min-h-[calc(100vh-4rem)] bg-void transition-colors duration-300">
      
      {/* Background Decor - Adaptive to Theme */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-primary opacity-5 blur-[80px] rounded-full pointer-events-none" />

      {/* Hero Section */}
      <motion.section 
        className="relative max-w-6xl mx-auto px-6 pt-20 pb-16 text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <motion.div 
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full text-sm text-primary mb-6 border border-primary/20"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Workflow className="w-4 h-4" />
          <span className="font-medium">Orchestrator-Worker Architecture</span>
        </motion.div>

        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-text-main mb-6 leading-tight">
          Proof of <span className="text-text-main">Work.</span><br />
          <span className="text-primary">Verified.</span>
        </h1>
        
        <p className="text-xl text-text-muted mb-4 max-w-3xl mx-auto leading-relaxed">
          Advanced workflow combining <span className="text-text-main font-semibold">deterministic code analysis workers</span> with{' '}
          <span className="text-text-main font-semibold">AI reasoning agents</span> for comprehensive skill evaluation.
        </p>

        <p className="text-base text-text-dim mb-10 max-w-2xl mx-auto">
          Powered by <span className="font-mono text-xs bg-surface border border-border px-2 py-1 rounded">Tree-sitter AST</span>, 
          <span className="font-mono text-xs bg-surface border border-border px-2 py-1 rounded mx-1">Llama 3.3</span>, 
          <span className="font-mono text-xs bg-surface border border-border px-2 py-1 rounded">Gemini 3 Flash</span>, and 
          <span className="font-mono text-xs bg-surface border border-border px-2 py-1 rounded mx-1">LangGraph</span>
        </p>

        {/* Input Section */}
        <div className="max-w-2xl mx-auto space-y-4 mb-24">
          <div className="flex gap-3 relative group">
            {/* Input Glow */}
            <div className="absolute -inset-1 bg-gradient-to-r from-primary/30 to-blue-500/30 rounded-xl opacity-20 group-hover:opacity-40 blur transition duration-500"></div>
            
            <div className="relative flex-1">
              <Github className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-dim" />
              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                placeholder="https://github.com/username/repository"
                className="w-full pl-12 pr-4 py-4 bg-panel border border-border text-text-main rounded-xl focus:outline-none focus:border-primary/50 transition-all placeholder:text-text-dim/50"
                disabled={loading}
              />
            </div>
            <motion.button
              onClick={handleAnalyze}
              disabled={loading}
              className="relative px-8 py-4 bg-primary hover:brightness-110 text-bg-main rounded-xl font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg shadow-primary/20"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {loading ? (
                <>
                  <motion.div
                    className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  />
                  <span>Analyzing</span>
                </>
              ) : (
                <>
                  <span>Start</span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </motion.button>
          </div>

          {showTokenInput && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="relative"
            >
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-primary" />
              <input
                type="password"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="GitHub Personal Access Token (for private repos)"
                className="w-full pl-12 pr-4 py-4 bg-panel border border-primary/30 text-text-main rounded-xl focus:outline-none focus:border-primary"
              />
            </motion.div>
          )}

          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="p-4 bg-error/10 border border-error/20 rounded-lg text-error text-sm font-medium flex items-center gap-2"
            >
              <ShieldCheck className="w-4 h-4" /> {error}
            </motion.div>
          )}
        </div>

        {/* --- METHODOLOGY SECTION (Replaces Formula) --- */}
        <div className="max-w-6xl mx-auto text-left mb-24">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-bold text-text-main flex items-center gap-3">
              <BookOpen className="w-8 h-8 text-primary" />
              Verification Methodology
            </h2>
            <button 
              onClick={() => navigate('/methodology')}
              className="text-sm font-mono text-text-muted hover:text-primary transition-colors flex items-center gap-2"
            >
              Full Technical Report <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            <MethodologyCard 
              step="01"
              title="Deterministic Scan"
              icon={Terminal}
              desc="We parse the AST (Abstract Syntax Tree) to calculate NCrF complexity, SLOC, and structural patterns without using AI."
              color="text-green-500"
              bg="bg-green-500/10"
              border="border-green-500/20"
            />
            <MethodologyCard 
              step="02"
              title="AI Assessment"
              icon={Scale}
              desc="The Grader Agent (Llama 3.3) analyzes code semantics against the SFIA framework rubric to assign a capability level."
              color="text-primary"
              bg="bg-primary/10"
              border="border-primary/20"
            />
            <MethodologyCard 
              step="03"
              title="Bayesian Check"
              icon={Database}
              desc="The Judge Agent compares the AI's grade against a statistical prior derived from the code metrics. It arbitrates conflicts."
              color="text-purple-400"
              bg="bg-purple-500/10"
              border="border-purple-500/20"
            />
            <MethodologyCard 
              step="04"
              title="Reality Audit"
              icon={CheckCircle2}
              desc="The Auditor Worker verifies CI/CD build logs. Code that fails to compile receives a strict 50% value penalty."
              color="text-blue-400"
              bg="bg-blue-500/10"
              border="border-blue-500/20"
            />
          </div>
        </div>

        {/* --- SYSTEM ARCHITECTURE --- */}
        <motion.div 
          className="max-w-5xl mx-auto bg-panel border border-border rounded-2xl p-8 shadow-xl"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <div className="flex items-center justify-center gap-3 mb-8">
            <Layers className="w-6 h-6 text-text-dim" />
            <h3 className="text-2xl font-bold text-text-main">System Architecture</h3>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8 text-left">
            
            {/* Workers */}
            <div className="space-y-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-green-500/10 rounded-lg">
                  <Binary className="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <h4 className="font-bold text-text-main">Deterministic Workers</h4>
                  <p className="text-xs text-text-muted">High reliability, zero hallucination</p>
                </div>
              </div>
              <div className="pl-4 border-l-2 border-border space-y-3">
                <TechItem name="Validator" desc="GitHub API verification" />
                <TechItem name="Scanner" desc="Tree-sitter AST parsing" />
                <TechItem name="Auditor" desc="CI/CD status checks" />
              </div>
            </div>

            {/* Agents */}
            <div className="space-y-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Cpu className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h4 className="font-bold text-text-main">Reasoning Agents</h4>
                  <p className="text-xs text-text-muted">Semantic understanding & tool use</p>
                </div>
              </div>
              <div className="pl-4 border-l-2 border-border space-y-3">
                <TechItem name="Grader" desc="Llama 3.3 SFIA assessment" />
                <TechItem name="Judge" desc="Gemini 3 Bayesian arbitration" />
                <TechItem name="Mentor" desc="Growth plan generation" />
              </div>
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-border flex items-center justify-center gap-2 text-sm text-text-dim">
            <Workflow className="w-4 h-4" />
            <span>Orchestrated by <strong>LangGraph</strong> state machine with conditional routing</span>
          </div>
        </motion.div>

      </motion.section>

      {/* Advanced Patterns */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-text-main mb-4">Advanced Workflow Patterns</h2>
          <p className="text-text-muted max-w-2xl mx-auto">
            Built on proven LangGraph architectural patterns for reliability and scalability
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <WorkflowPatternCard
            icon={<GitBranch className="w-6 h-6" />}
            title="Routing Workflow"
            description="Validator routes to specialized code paths — Scanner for public repos, token verification for private access."
            color="text-blue-400"
          />
          <WorkflowPatternCard
            icon={<Layers className="w-6 h-6" />}
            title="Orchestrator-Worker"
            description="LangGraph orchestrates parallel AST scanning, sequential AI grading, and dynamic Judge arbitration."
            color="text-purple-400"
          />
          <WorkflowPatternCard
            icon={<Zap className="w-6 h-6" />}
            title="Evaluator-Optimizer"
            description="Judge evaluates Grader outputs — conflicts trigger re-evaluation loops until consensus emerges."
            color="text-primary"
          />
        </div>
      </section>

      {/* Footer Tech Stack */}
      <section className="max-w-6xl mx-auto px-6 py-12 border-t border-border mt-12">
        <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-text-dim font-mono">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4" /> Tree-sitter
          </div>
          <div className="w-px h-4 bg-border" />
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4" /> Groq Llama 3.3
          </div>
          <div className="w-px h-4 bg-border" />
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4" /> Gemini 3 Flash
          </div>
          <div className="w-px h-4 bg-border" />
          <div className="flex items-center gap-2">
            <Workflow className="w-4 h-4" /> LangGraph
          </div>
          <div className="w-px h-4 bg-border" />
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4" /> Opik Tracing
          </div>
        </div>
      </section>
    </div>
  )
}

// --- SUBCOMPONENTS ---

function MethodologyCard({ step, title, icon: Icon, desc, color, bg, border }) {
  return (
    <motion.div 
      whileHover={{ y: -5 }}
      className={`bg-panel border ${border} p-6 rounded-xl relative overflow-hidden group`}
    >
      <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity`}>
        <Icon className={`w-24 h-24 ${color}`} />
      </div>
      
      <div className={`text-xs font-mono font-bold mb-3 ${color} ${bg} px-2 py-1 rounded inline-block`}>
        STEP {step}
      </div>
      
      <h3 className="text-lg font-bold text-text-main mb-3 flex items-center gap-2">
        <Icon className={`w-5 h-5 ${color}`} /> {title}
      </h3>
      
      <p className="text-sm text-text-muted leading-relaxed relative z-10">
        {desc}
      </p>
    </motion.div>
  )
}

function WorkflowPatternCard({ icon, title, description, color }) {
  return (
    <motion.div
      className="p-6 rounded-xl border border-border bg-panel hover:border-primary/30 transition-all shadow-sm hover:shadow-md"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
    >
      <div className={`mb-4 p-3 bg-surface rounded-lg w-fit ${color}`}>
        {icon}
      </div>
      <h3 className="text-lg font-bold mb-2 text-text-main">{title}</h3>
      <p className="text-sm text-text-muted leading-relaxed">{description}</p>
    </motion.div>
  )
}

function TechItem({ name, desc }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <div className="w-1.5 h-1.5 rounded-full bg-border" />
      <span className="font-medium text-text-main">{name}</span>
      <span className="text-text-muted">—</span>
      <span className="text-text-dim">{desc}</span>
    </div>
  )
}