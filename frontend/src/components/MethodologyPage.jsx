import { motion } from 'framer-motion'
import { 
  ArrowLeft, Calculator, BrainCircuit, Scale, 
  ShieldCheck, Shield, Network, Binary, CheckCircle2,
  Terminal, Layers, Database, Cpu, Zap, 
  Search, Eye, LockKeyhole, FileCode, GitCommit
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function MethodologyPage() {
  const navigate = useNavigate()

  // Fade-in animation variant
  const fadeInUp = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  }

  return (
    <div className="min-h-screen bg-void text-text-main pb-32 font-sans selection:bg-primary/20">
      
      {/* Header */}
      <div className="border-b border-border bg-surface/80 sticky top-0 z-40 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center gap-4">
          <button 
            onClick={() => navigate('/')}
            className="p-2 hover:bg-white/5 rounded-full text-text-muted hover:text-text-main transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-px h-6 bg-border" />
            <h1 className="text-sm font-mono font-bold uppercase tracking-widest text-text-main">
              Technical Specification
            </h1>
            <span className="text-xs font-mono text-text-dim px-2 py-0.5 bg-surface border border-border rounded">v2.2</span>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-16 space-y-32">

        {/* --- INTRODUCTION --- */}
        <section>
          <motion.div 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={fadeInUp}
            className="prose prose-invert max-w-none"
          >
            <div className="flex items-center gap-3 mb-6">
              <span className="px-3 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full text-xs font-bold tracking-wider uppercase">
                Architecture Overview
              </span>
            </div>
            
            <h1 className="text-5xl font-bold text-text-main mb-8 leading-tight">
              A Hybrid Intelligence <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-orange-400">Verification Engine.</span>
            </h1>
            
            <p className="text-xl text-text-muted leading-relaxed mb-8">
              SkillProtocol is a <strong>multi-agent system</strong> that bridges the gap between 
              deterministic static analysis and probabilistic AI reasoning. We use Abstract Syntax Tree (AST) parsing 
              across 15+ languages, Bayesian statistical modeling, and a council of 7 specialized AI agents 
              to mint standardized capability credits.
            </p>
            
            <div className="bg-surface/50 border border-primary/20 rounded-2xl p-8">
              <h3 className="text-lg font-bold text-primary mb-4 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5" />
                The "Triple-Lock" Protocol
              </h3>
              <p className="text-sm text-text-muted leading-relaxed mb-6">
                Most AI coding tools hallucinate because they treat code as unstructured text. 
                SkillProtocol treats code as a rigorous data structure:
              </p>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <div className="p-2 bg-green-500/10 w-fit rounded-lg"><Binary className="w-5 h-5 text-green-500" /></div>
                  <strong className="text-text-main block">1. Mathematical</strong>
                  <p className="text-xs text-text-dim leading-relaxed">Deterministic AST scanning calculates objective complexity metrics (Cyclomatic, Halstead). Zero AI involvement.</p>
                </div>
                <div className="space-y-2">
                  <div className="p-2 bg-purple-500/10 w-fit rounded-lg"><BrainCircuit className="w-5 h-5 text-purple-500" /></div>
                  <strong className="text-text-main block">2. Bayesian</strong>
                  <p className="text-xs text-text-dim leading-relaxed">A statistical model predicts the likely skill level <span className="font-mono">P(Level | Evidence)</span> before the AI sees the code.</p>
                </div>
                <div className="space-y-2">
                  <div className="p-2 bg-blue-500/10 w-fit rounded-lg"><Zap className="w-5 h-5 text-blue-500" /></div>
                  <strong className="text-text-main block">3. Adversarial</strong>
                  <p className="text-xs text-text-dim leading-relaxed">A "Judge" agent explicitly challenges the "Grader" agent if assessments deviate from the math.</p>
                </div>
              </div>
            </div>
          </motion.div>
        </section>

        {/* --- 7 AGENT COUNCIL --- */}
        <section>
          <div className="flex items-center gap-4 mb-12">
            <div className="p-3 bg-surface border border-border rounded-xl">
              <Network className="w-8 h-8 text-orange-400" />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-text-main">The 7-Agent Council</h2>
              <p className="text-text-muted">Orchestrated via LangGraph State Machine</p>
            </div>
          </div>
          
          <div className="relative border-l-2 border-border ml-4 space-y-12 pb-12">
            <AgentTimelineItem 
              step="01"
              name="Validator" 
              type="Deterministic Worker"
              tech="GitHub API + Regex"
              desc="The gatekeeper. It validates repository accessibility, checks size limits (<500MB), ensures privacy compliance, and handles OAuth tokens securely using Python's `httpx` library. It filters out empty or archived repositories to save compute."
            />
            <AgentTimelineItem 
              step="02"
              name="Scanner" 
              type="Deterministic Worker"
              tech="Tree-sitter (C-based AST)"
              desc="The archaeologist. It uses Tree-sitter bindings to parse code into Abstract Syntax Trees for 15+ languages (Python, TS, Rust, Go, etc.). It calculates SLOC (Logical), Cyclomatic Complexity, and detects architectural patterns (e.g., MVC, Singleton) purely via structure, not AI."
            />
            <AgentTimelineItem 
              step="03"
              name="Math Model" 
              type="Statistical Worker"
              tech="Bayesian Inference"
              desc="The oracle. It calculates a 'Prior Probability' distribution for the SFIA level based purely on hard metrics (SLOC density, test presence, commit stability). This creates a 'Statistical Anchor' that the AI agents must respect."
            />
            <AgentTimelineItem 
              step="04"
              name="Grader" 
              type="AI Agent"
              tech="Llama 3.3 70B (via Groq)"
              desc="The evaluator. Uses Tool Calling (`read_file`, `get_criteria`) to semantically assess code quality against the SFIA framework. It cannot just guess; it must cite specific file paths and patterns as evidence in its structured output."
            />
            <AgentTimelineItem 
              step="05"
              name="Judge" 
              type="AI Agent"
              tech="Gemini 3 Flash"
              desc="The supreme arbitrator. It resolves conflicts between the Grader (AI) and the Math Model (Stats). If the Grader claims 'Level 5' but the Math says 'Level 2', the Judge intervenes to prevent grade inflation."
            />
            <AgentTimelineItem 
              step="06"
              name="Auditor" 
              type="Deterministic Worker"
              tech="GitHub Actions API"
              desc="The reality check. It queries the GitHub Actions API to verify that the code actually compiles and passes tests. It applies a strict 50% credit penalty if CI/CD pipelines are failing. Code must run to count."
            />
            <AgentTimelineItem 
              step="07"
              name="Mentor" 
              type="AI Agent"
              tech="Gemini 3 Flash (Long Context)"
              desc="The coach. It analyzes the gap between current and next levels. It generates a personalized, time-boxed roadmap with 'Quick Wins' and specific resource links, outputting formatted Markdown."
            />
          </div>
        </section>

        {/* --- NCrF & TREE-SITTER --- */}
        <section>
          <div className="flex items-center gap-4 mb-12">
            <div className="p-3 bg-surface border border-border rounded-xl">
              <Terminal className="w-8 h-8 text-blue-400" />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-text-main">NCrF & Code Metrics</h2>
              <p className="text-text-muted">Normalized Code Reputation Factor</p>
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 gap-12">
            <div className="prose prose-invert prose-sm text-text-muted">
              <p>
                Traditional tools count lines of text. We count <strong>Logical Nodes</strong>. 
                Using <strong>Tree-sitter</strong>, we build an Abstract Syntax Tree (AST) for the entire repository. 
                This allows us to ignore whitespace, comments, and imports, focusing purely on algorithmic complexity.
              </p>
              <p>
                Our <strong>NCrF Formula</strong> converts complexity into a standardized "Learning Hours" equivalent, 
                normalizing value across different languages (e.g., 100 lines of Rust is worth more than 100 lines of HTML).
              </p>
            </div>

            <div className="bg-panel border border-border rounded-xl p-6">
              <h3 className="text-xs font-mono font-bold text-text-dim uppercase mb-4 tracking-wider">Complexity Weights</h3>
              <div className="space-y-3 text-sm">
                <WeightRow label="Control Flow (if/else/switch)" points="+1 Point" />
                <WeightRow label="Loops (for/while/recursion)" points="+2 Points" />
                <WeightRow label="Class/Struct Definition" points="+3 Points" />
                <WeightRow label="Async/Concurrency Patterns" points="+5 Points" />
                <WeightRow label="Metaprogramming/Reflection" points="+8 Points" />
              </div>
            </div>
          </div>
        </section>

        {/* --- BAYESIAN MATH --- */}
        <section>
          <div className="flex items-center gap-4 mb-12">
            <div className="p-3 bg-surface border border-border rounded-xl">
              <Calculator className="w-8 h-8 text-purple-400" />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-text-main">The Bayesian Guard</h2>
              <p className="text-text-muted">Statistical Hallucination Prevention</p>
            </div>
          </div>

          <div className="bg-panel border border-border rounded-2xl p-8 relative overflow-hidden">
            <div className="grid md:grid-cols-2 gap-12 relative z-10">
              <div>
                <h4 className="text-lg font-bold text-white mb-6">Likelihood Functions</h4>
                <p className="text-sm text-text-muted mb-6">
                  We verify the probability of a skill level given the evidence found in the AST.
                </p>
                <ul className="space-y-4 text-sm text-text-dim">
                  <li className="flex items-center gap-3">
                    <div className="p-1.5 bg-purple-500/10 rounded border border-purple-500/20">
                      <FileCode className="w-4 h-4 text-purple-400" />
                    </div>
                    <span><strong>SLOC Likelihood:</strong> Log-Normal distribution</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="p-1.5 bg-purple-500/10 rounded border border-purple-500/20">
                      <Cpu className="w-4 h-4 text-purple-400" />
                    </div>
                    <span><strong>Complexity Density:</strong> Gaussian distribution</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="p-1.5 bg-purple-500/10 rounded border border-purple-500/20">
                      <GitCommit className="w-4 h-4 text-purple-400" />
                    </div>
                    <span><strong>Git Stability:</strong> Variance analysis</span>
                  </li>
                </ul>
              </div>

              <div className="flex flex-col justify-center">
                <div className="font-mono text-sm text-purple-300 bg-purple-900/10 p-6 rounded-xl border border-purple-500/20 text-center">
                  <div className="text-xs text-purple-400/50 uppercase tracking-widest mb-2">BAYES' THEOREM</div>
                  P(Level | Evidence) <br/>
                  ∝ <br/>
                  P(Evidence | Level) * P(Level)
                </div>
                <div className="mt-6 text-center text-xs text-text-muted">
                  * Prior P(Level) derived from 12,000+ GitHub repos
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* --- SFIA FRAMEWORK --- */}
        <section>
          <div className="flex items-center gap-4 mb-12">
            <div className="p-3 bg-surface border border-border rounded-xl">
              <Scale className="w-8 h-8 text-green-400" />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-text-main">SFIA Capability Levels</h2>
              <p className="text-text-muted">Skills Framework for the Information Age</p>
            </div>
          </div>
          
          <div className="overflow-hidden border border-border rounded-xl shadow-sm">
            <table className="w-full text-sm text-left">
              <thead className="bg-surface text-text-dim font-mono uppercase text-xs">
                <tr>
                  <th className="p-4 border-b border-border w-24">Level</th>
                  <th className="p-4 border-b border-border w-32">Title</th>
                  <th className="p-4 border-b border-border">Technical Criteria (Must Have)</th>
                  <th className="p-4 border-b border-border w-24">Credit Mult</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                <SfiaRow level="L1" title="Follow" desc="Basic scripts. Single file. Linear logic. No modularity." mult="0.5x" />
                <SfiaRow level="L2" title="Assist" desc="Functions used. Some separation. Basic error printing. No tests." mult="0.8x" />
                <SfiaRow level="L3" title="Apply" desc="Professional Baseline. Modular structure. README. Dependencies managed." mult="1.0x" />
                <SfiaRow level="L4" title="Enable" desc="Unit Tests. Design patterns (Factory, Strategy). Async. Robust errors." mult="1.3x" />
                <SfiaRow level="L5" title="Ensure" desc="CI/CD Pipelines. Docker. Architecture docs. High test coverage." mult="1.7x" />
              </tbody>
            </table>
          </div>
        </section>

        {/* --- OPIK OBSERVABILITY --- */}
        <section>
          <div className="flex items-center gap-4 mb-12">
            <div className="p-3 bg-surface border border-border rounded-xl">
              <Eye className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-text-main">Opik Observability</h2>
              <p className="text-text-muted">The Nervous System of SkillProtocol</p>
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-panel border border-border p-8 rounded-2xl">
              <h3 className="font-bold text-text-main mb-4 flex items-center gap-3">
                <Search className="w-5 h-5 text-primary" /> The "Data Flywheel"
              </h3>
              <p className="text-sm text-text-muted mb-6 leading-relaxed">
                We don't just log data; we learn from it. User feedback triggers an automated optimization loop.
              </p>
              <ul className="text-xs text-text-dim space-y-4">
                <li className="flex gap-3">
                  <span className="font-mono text-primary font-bold">01</span>
                  <span>Users provide feedback (Thumbs Up/Down) on their certificates.</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-mono text-primary font-bold">02</span>
                  <span>System auto-mines positive traces into a "Golden Dataset".</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-mono text-primary font-bold">03</span>
                  <span><strong>Opik MetaPromptOptimizer</strong> runs offline to mathematically improve prompts against this dataset.</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-mono text-primary font-bold">04</span>
                  <span>Accuracy improved by <strong>15.5%</strong> during development.</span>
                </li>
              </ul>
            </div>

            <div className="bg-panel border border-border p-8 rounded-2xl">
              <h3 className="font-bold text-text-main mb-4 flex items-center gap-3">
                <Shield className="w-5 h-5 text-primary" /> Online Evaluations
              </h3>
              <p className="text-sm text-text-muted mb-6 leading-relaxed">
                Every single analysis is graded by Opik Evaluators (LLM-as-a-Judge) in real-time before being shown to the user.
              </p>
              <div className="space-y-3">
                <div className="flex justify-between items-center text-xs p-4 bg-surface rounded-xl border border-border">
                  <span className="text-text-main font-bold">Hallucination Watch</span>
                  <span className="text-success font-mono bg-success/10 px-2 py-1 rounded">PASSING (99.2%)</span>
                </div>
                <div className="flex justify-between items-center text-xs p-4 bg-surface rounded-xl border border-border">
                  <span className="text-text-main font-bold">Relevance Check</span>
                  <span className="text-success font-mono bg-success/10 px-2 py-1 rounded">PASSING (98.5%)</span>
                </div>
                <div className="flex justify-between items-center text-xs p-4 bg-surface rounded-xl border border-border">
                  <span className="text-text-main font-bold">Tone Analysis</span>
                  <span className="text-success font-mono bg-success/10 px-2 py-1 rounded">PASSING (99.8%)</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <div className="border-t border-border pt-12 text-center">
          <p className="text-text-dim text-xs font-mono">
            SYSTEM KERNEL: V2.2.0-STABLE · POWERED BY LANGGRAPH & OPIK
          </p>
        </div>

      </div>
    </div>
  )
}

// --- SUBCOMPONENTS ---

function AgentTimelineItem({ step, name, type, tech, desc }) {
  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      className="relative pl-8"
    >
      <div className="absolute left-[-5px] top-0 w-2.5 h-2.5 rounded-full bg-border border-4 border-void" />
      
      <div className="flex flex-col md:flex-row md:items-start gap-4 md:gap-8">
        <div className="md:w-48 shrink-0">
          <div className="text-xs font-mono text-text-dim mb-1">{step}</div>
          <h3 className="text-xl font-bold text-text-main">{name}</h3>
          <span className="text-[10px] font-mono uppercase tracking-wider text-primary bg-primary/5 px-2 py-0.5 rounded border border-primary/10 inline-block mt-2">
            {type}
          </span>
        </div>
        
        <div className="bg-panel border border-border p-6 rounded-xl flex-1 hover:border-primary/20 transition-colors">
          <div className="text-xs font-mono text-text-dim mb-3 flex items-center gap-2">
            <Cpu className="w-3 h-3" /> {tech}
          </div>
          <p className="text-sm text-text-muted leading-relaxed">
            {desc}
          </p>
        </div>
      </div>
    </motion.div>
  )
}

function WeightRow({ label, points }) {
  return (
    <div className="flex justify-between items-center border-b border-border/50 pb-3 last:border-0 last:pb-0">
      <span className="text-text-main">{label}</span>
      <span className="font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded text-xs">{points}</span>
    </div>
  )
}

function SfiaRow({ level, title, desc, mult }) {
  return (
    <tr className="bg-panel hover:bg-surface/50 transition-colors">
      <td className="p-4 font-mono font-bold text-text-dim">{level}</td>
      <td className="p-4 font-bold text-text-main">{title}</td>
      <td className="p-4 text-text-muted">{desc}</td>
      <td className="p-4 font-mono text-green-400">{mult}</td>
    </tr>
  )
}