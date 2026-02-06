import { useState, useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { 
  ArrowRight, Github, ShieldCheck, Database, Search, 
  Cpu, Lock, Code2, Scale, Terminal, CheckCircle2, 
  Workflow, Zap, Binary, Layers, BookOpen, TrendingUp,
  GitBranch, Eye, Network, Server, Bot, BrainCircuit,
  Activity, Award, LockKeyhole, Sparkles, ChevronRight
} from 'lucide-react'
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion'
import { api } from '../services/api'

// --- CONSTANTS & CONFIG ---
const AGENT_COUNCIL = [
  {
    id: 'validator',
    name: 'Validator',
    role: 'Deterministic Gatekeeper',
    icon: ShieldCheck,
    color: 'text-blue-500',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    desc: 'Validates repository accessibility, enforces size limits (<500MB), checks privacy settings, and handles OAuth token exchange securely using GitHub API.'
  },
  {
    id: 'scanner',
    name: 'Scanner',
    role: 'Code Archaeologist',
    icon: Terminal,
    color: 'text-green-500',
    bg: 'bg-green-500/10',
    border: 'border-green-500/20',
    desc: 'Parses Abstract Syntax Trees (AST) for 15+ languages using Tree-sitter. Calculates SLOC, Cyclomatic Complexity, and NCrF base scores without hallucination.'
  },
  {
    id: 'math',
    name: 'Math Model',
    role: 'Statistical Oracle',
    icon: Binary,
    color: 'text-orange-500',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/20',
    desc: 'Calculates a Bayesian "Prior Probability" of skill level based purely on hard metrics (SLOC density, test presence). Anchors the AI to statistical reality.'
  },
  {
    id: 'grader',
    name: 'Grader',
    role: 'Semantic Evaluator',
    icon: Scale,
    color: 'text-purple-500',
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/20',
    desc: 'Llama 3.3 70B Agent using Tool Calling to verify architectural patterns (MVC, DI, Factory) against the SFIA framework rubric with evidence citations.'
  },
  {
    id: 'judge',
    name: 'Judge',
    role: 'Supreme Arbitrator',
    icon: Zap,
    color: 'text-red-500',
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
    desc: 'Gemini 3 Flash agent that resolves conflicts between AI Grading and Math Models. Prevents grade inflation by demanding concrete file-path evidence.'
  },
  {
    id: 'auditor',
    name: 'Auditor',
    role: 'Reality Checker',
    icon: CheckCircle2,
    color: 'text-teal-500',
    bg: 'bg-teal-500/10',
    border: 'border-teal-500/20',
    desc: 'Queries GitHub Actions API to verify if tests actually pass. Applies a strict 50% credit penalty for failing builds. Code must compile to count.'
  },
  {
    id: 'mentor',
    name: 'Mentor',
    role: 'Growth Coach',
    icon: TrendingUp,
    color: 'text-yellow-500',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/20',
    desc: 'Analyzes skill gaps between current and target levels. Generates a personalized, time-boxed growth roadmap with "Quick Wins" and resource links.'
  }
]

export default function LandingPage({ onStartAnalysis, onUserDetected }) {
  const [repoUrl, setRepoUrl] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [showTokenInput, setShowTokenInput] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const location = useLocation()
  const navigate = useNavigate()
  const containerRef = useRef(null)
  
  // Parallax Scroll Effect (Subtle)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  })
  
  const yHero = useTransform(scrollYProgress, [0, 0.2], [0, -20])
  const opacityHero = useTransform(scrollYProgress, [0, 0.2], [1, 0])

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
    <div ref={containerRef} className="relative overflow-hidden min-h-screen bg-void text-text-main transition-colors duration-300 pb-20 font-sans selection:bg-primary/20">
      
      {/* --- BACKGROUND FX (Adaptive) --- */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/5 blur-[120px] rounded-full mix-blend-multiply dark:mix-blend-screen" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-500/5 blur-[120px] rounded-full mix-blend-multiply dark:mix-blend-screen" />
      </div>

      {/* --- HERO SECTION (CAREER GROWTH FOCUSED) --- */}
      <motion.section 
        style={{ y: yHero, opacity: opacityHero }}
        className="relative max-w-4xl mx-auto px-6 pt-16 pb-12 text-center z-10"
      >
        <motion.div 
          className="inline-flex items-center gap-2 px-3 py-1 bg-surface border border-border rounded-full text-[10px] font-mono text-text-muted mb-6 shadow-sm"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Sparkles className="w-3 h-3 text-primary" />
          <span className="font-semibold text-text-main">LANGGRAPH v2.2</span>
          <span className="text-border">|</span>
          <span>OPIK OBSERVABILITY</span>
        </motion.div>

        <motion.h1 
          className="text-4xl md:text-5xl font-bold tracking-tight text-text-main mb-4 leading-tight"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          Your AI-Powered <br className="hidden md:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-orange-500">Career Growth Engine.</span>
        </motion.h1>
        
        <motion.p 
          className="text-base text-text-muted mb-8 max-w-xl mx-auto leading-relaxed"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          Turn GitHub repositories into verifiable skill metrics, personalized learning roadmaps, and professional growth.
        </motion.p>

        {/* --- INPUT MODULE (HIGH CONTRAST) --- */}
        <div className="max-w-xl mx-auto relative z-20 mb-8">
          <motion.div 
            className="flex gap-2 p-1.5 bg-surface border border-border rounded-xl shadow-xl relative group hover:border-primary/50 transition-colors"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <div className="relative flex-1 flex items-center">
              <Github className="absolute left-3 w-5 h-5 text-text-muted" />
              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                placeholder="github.com/username/repository"
                className="w-full pl-10 pr-3 py-2.5 bg-transparent border-none text-text-main text-sm placeholder:text-text-muted/50 focus:ring-0"
                disabled={loading}
              />
            </div>
            
            <motion.button
              onClick={handleAnalyze}
              disabled={loading}
              className="px-5 py-2.5 bg-primary hover:bg-primary/90 text-white dark:text-black rounded-lg font-bold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-md"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {loading ? (
                <>
                  <motion.div
                    className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  />
                  <span>Run</span>
                </>
              ) : (
                <>
                  <span>Verify</span>
                  <ArrowRight className="w-3 h-3" />
                </>
              )}
            </motion.button>
          </motion.div>

          {/* Token Input (Conditional) */}
          <AnimatePresence>
            {showTokenInput && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden mt-2"
              >
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-primary" />
                  <input
                    type="password"
                    value={githubToken}
                    onChange={(e) => setGithubToken(e.target.value)}
                    placeholder="GitHub Token (repo scope)"
                    className="w-full pl-9 pr-3 py-2 bg-surface border border-primary/30 text-text-main rounded-lg text-xs focus:outline-none focus:border-primary shadow-inner"
                  />
                </div>
              </motion.div>
            )}

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-3 p-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-600 text-xs font-medium flex items-center gap-2 justify-center"
              >
                <ShieldCheck className="w-3 h-3" /> 
                <span>{error}</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Tech Stack (Visible) */}
        <motion.div 
          className="flex flex-wrap justify-center gap-3 opacity-80"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.8 }}
          transition={{ delay: 0.6 }}
        >
          <TechPill icon={Cpu} label="Tree-sitter" />
          <TechPill icon={BrainCircuit} label="Bayesian" />
          <TechPill icon={Bot} label="Llama 3.3" />
          <TechPill icon={Eye} label="Opik" />
        </motion.div>
      </motion.section>

      {/* --- SECTION 2: INTELLIGENCE ARCHITECTURE --- */}
      <div className="max-w-6xl mx-auto text-left mb-24 px-6">
        <div className="flex items-center justify-between mb-8 border-b border-border pb-4">
          <h2 className="text-xl font-bold text-text-main flex items-center gap-2">
            <Network className="w-5 h-5 text-primary" />
            The 7-Agent Council
          </h2>
          <button 
            onClick={() => navigate('/methodology')}
            className="text-xs font-mono text-text-muted hover:text-primary transition-colors flex items-center gap-1"
          >
            Full Architecture <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {AGENT_COUNCIL.map((agent, i) => (
             <AgentGridCard key={agent.id} agent={agent} index={i} />
          ))}
        </div>
      </div>

      {/* --- SECTION 3: METHODOLOGY FLOW --- */}
      <section className="max-w-6xl mx-auto px-6 mb-24">
        <div className="text-center mb-10">
          <h2 className="text-xl font-bold text-text-main mb-2">Verification Pipeline</h2>
          <p className="text-sm text-text-muted">Rigorous 4-stage validation process.</p>
        </div>

        <div className="grid md:grid-cols-4 gap-4">
          <MethodologyCard 
            step="01"
            title="Scan"
            icon={Terminal}
            desc="We clone the repo and parse the AST (Abstract Syntax Tree) to calculate NCrF complexity, SLOC, and structural patterns without using AI."
            color="text-green-500"
            bg="bg-green-500/5"
            border="border-green-500/20"
          />
          <MethodologyCard 
            step="02"
            title="Assess"
            icon={Scale}
            desc="The Grader Agent (Llama 3.3) analyzes code semantics against the SFIA framework rubric to assign a level."
            color="text-primary"
            bg="bg-primary/5"
            border="border-primary/20"
          />
          <MethodologyCard 
            step="03"
            title="Check"
            icon={Database}
            desc="The Judge Agent compares the AI grade against statistical priors. It arbitrates conflicts."
            color="text-purple-500"
            bg="bg-purple-500/5"
            border="border-purple-500/20"
          />
          <MethodologyCard 
            step="04"
            title="Audit"
            icon={CheckCircle2}
            desc="The Auditor verifies CI/CD builds. Code that fails to compile receives a strict 50% penalty."
            color="text-blue-500"
            bg="bg-blue-500/5"
            border="border-blue-500/20"
          />
        </div>
      </section>

      {/* --- SECTION 4: OPIK OBSERVABILITY --- */}
      <section className="max-w-6xl mx-auto px-6 mb-24">
        <div className="bg-panel border border-border rounded-2xl p-8 relative overflow-hidden shadow-sm">
          {/* Subtle Glow */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-[80px] -z-10" />

          <div className="flex flex-col lg:flex-row gap-10 items-center">
            <div className="flex-1 text-left">
              <div className="flex items-center gap-2 mb-3">
                <Eye className="w-5 h-5 text-primary" />
                <h3 className="text-lg font-bold text-text-main">Self-Improving Architecture</h3>
              </div>
              <p className="text-sm text-text-muted mb-6 leading-relaxed">
                Powered by <strong>Opik</strong>, SkillProtocol learns from every analysis. 
                Our feedback flywheel automatically mines user verifications to optimize agent prompts.
              </p>
              
              <div className="grid grid-cols-2 gap-3">
                <FeatureRow icon={Search} text="Full Trace Observability" />
                <FeatureRow icon={Database} text="Golden Dataset Mining" />
                <FeatureRow icon={Cpu} text="Meta-Prompt Optimization" />
                <FeatureRow icon={ShieldCheck} text="Online Hallucination Checks" />
              </div>
            </div>

            <div className="flex-1 w-full">
              <div className="bg-[#0D1117] border border-gray-700 rounded-lg overflow-hidden shadow-xl text-[10px]">
                <div className="flex items-center gap-2 px-3 py-2 border-b border-white/5 bg-white/5">
                  <div className="w-2 h-2 rounded-full bg-red-500/80" />
                  <div className="w-2 h-2 rounded-full bg-yellow-500/80" />
                  <div className="w-2 h-2 rounded-full bg-green-500/80" />
                  <span className="ml-2 font-mono text-gray-400">opik_trace.log</span>
                </div>
                <div className="p-4 font-mono text-gray-300 space-y-2">
                  <div className="flex gap-2"><span className="text-blue-400">INFO</span><span>Starting Trace #a1b2</span></div>
                  <div className="flex gap-2 pl-3 border-l border-white/10"><span className="text-green-400">✓</span><span>Validator: OK</span></div>
                  <div className="flex gap-2 pl-3 border-l border-white/10"><span className="text-green-400">✓</span><span>Scanner: 45 files (Tree-sitter)</span></div>
                  <div className="flex gap-2 pl-3 border-l border-white/10"><span className="text-purple-400">⚡</span><span>Grader: Tool Call get_criteria(3)</span></div>
                  <div className="flex gap-2 pl-3 border-l border-white/10"><span className="text-red-400">⚖️</span><span>Judge: Conflict Resolved</span></div>
                  <div className="flex gap-2"><span className="text-blue-400">INFO</span><span>Added to Golden Dataset</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --- SECTION 5: ADVANCED PATTERNS --- */}
      <section className="max-w-6xl mx-auto px-6 mb-24">
        <div className="text-center mb-8">
          <h2 className="text-xl font-bold text-text-main mb-2">LangGraph Patterns</h2>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <WorkflowPatternCard 
            icon={<GitBranch className="w-5 h-5" />}
            title="Conditional Routing"
            desc="Dynamic execution paths based on validation state."
            color="text-blue-500"
          />
          <WorkflowPatternCard 
            icon={<Layers className="w-5 h-5" />}
            title="Human-in-the-Loop Sim"
            desc="Judge agent acts as an adversarial reviewer."
            color="text-purple-500"
          />
          <WorkflowPatternCard 
            icon={<Zap className="w-5 h-5" />}
            title="Evaluator-Optimizer"
            desc="System tunes its own prompts via Opik."
            color="text-primary"
          />
        </div>
      </section>

      {/* --- FOOTER --- */}
      <footer className="max-w-6xl mx-auto px-6 py-8 border-t border-border mt-12">
        <div className="flex flex-wrap items-center justify-center gap-6 text-xs text-text-muted font-mono mb-8">
          <div className="flex items-center gap-1.5 hover:text-text-main transition-colors">
            <Code2 className="w-3 h-3" /> Tree-sitter
          </div>
          <div className="w-px h-3 bg-border" />
          <div className="flex items-center gap-1.5 hover:text-text-main transition-colors">
            <Cpu className="w-3 h-3" /> Llama 3.3
          </div>
          <div className="w-px h-3 bg-border" />
          <div className="flex items-center gap-1.5 hover:text-text-main transition-colors">
            <Database className="w-3 h-3" /> Gemini 3 Flash
          </div>
          <div className="w-px h-3 bg-border" />
          <div className="flex items-center gap-1.5 hover:text-text-main transition-colors">
            <Workflow className="w-3 h-3" /> LangGraph
          </div>
          <div className="w-px h-3 bg-border" />
          <div className="flex items-center gap-1.5 hover:text-text-main transition-colors">
            <BookOpen className="w-3 h-3" /> Opik Tracing
          </div>
        </div>
        <p className="text-center text-text-dim text-[10px] font-mono mt-6 opacity-60">
          BUILT FOR NEW YEAR, NEW YOU HACKATHON 2025 · TEAM SKILLPROTOCOL
        </p>
      </footer>
    </div>
  )
}

// --- SUBCOMPONENTS (REFINED FOR CONTRAST) ---

function TechPill({ icon: Icon, label }) {
  return (
    <span className="flex items-center gap-1.5 px-2.5 py-1 bg-surface border border-border rounded-md font-mono text-[10px] text-text-muted shadow-sm">
      <Icon className="w-3 h-3 text-text-dim" />
      {label}
    </span>
  )
}

function AgentGridCard({ agent, index }) {
  const Icon = agent.icon
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="group flex flex-col p-4 bg-surface border border-border rounded-xl hover:border-primary/30 transition-all shadow-sm hover:shadow-md"
    >
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg ${agent.bg} ${agent.color}`}>
          <Icon className="w-4 h-4" />
        </div>
        <div>
          <h4 className="font-bold text-text-main text-sm">{agent.name}</h4>
          <span className="text-[9px] font-mono uppercase tracking-wider text-text-muted">
            {agent.role}
          </span>
        </div>
      </div>
      <p className="text-xs text-text-muted leading-relaxed line-clamp-3 group-hover:line-clamp-none transition-all">
        {agent.desc}
      </p>
    </motion.div>
  )
}

function MethodologyCard({ step, title, icon: Icon, desc, color, bg, border }) {
  return (
    <motion.div 
      whileHover={{ y: -3 }}
      className={`bg-surface border ${border} p-5 rounded-xl relative overflow-hidden group shadow-sm`}
    >
      <div className={`absolute top-0 right-0 p-3 opacity-5 group-hover:opacity-10 transition-opacity`}>
        <Icon className={`w-20 h-20 ${color}`} />
      </div>
      <div className={`text-[10px] font-mono font-bold mb-2 ${color} ${bg} px-1.5 py-0.5 rounded inline-block`}>
        STEP {step}
      </div>
      <h3 className="text-sm font-bold text-text-main mb-2 flex items-center gap-2">
        <Icon className={`w-4 h-4 ${color}`} /> {title}
      </h3>
      <p className="text-xs text-text-muted leading-relaxed relative z-10">
        {desc}
      </p>
    </motion.div>
  )
}

function WorkflowPatternCard({ icon, title, desc, color }) {
  return (
    <div className="p-4 rounded-xl border border-border bg-surface hover:border-primary/30 transition-all shadow-sm">
      <div className={`mb-3 p-2 bg-surface rounded-lg w-fit ${color} bg-opacity-10`}>
        {icon}
      </div>
      <h3 className="text-sm font-bold mb-1 text-text-main">{title}</h3>
      <p className="text-xs text-text-muted leading-relaxed">{desc}</p>
    </div>
  )
}

function FeatureRow({ icon: Icon, text }) {
  return (
    <div className="flex items-center gap-3 text-xs text-text-main">
      <div className="p-1.5 bg-surface rounded-full border border-border shrink-0 shadow-sm">
        <Icon className="w-3 h-3 text-primary" />
      </div>
      {text}
    </div>
  )
}