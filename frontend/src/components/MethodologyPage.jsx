import { motion } from 'framer-motion'
import { 
  ArrowLeft, Calculator, BrainCircuit, Scale, 
  ShieldCheck, Network, Binary, CheckCircle2, XCircle, 
  Terminal, FileCode, Layers, GitCommit, Database
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function MethodologyPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-void text-text-main pb-32 font-sans selection:bg-primary/20">
      
      {/* Header */}
      <div className="border-b border-border bg-surface/50 sticky top-0 z-40 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center gap-4">
          <button 
            onClick={() => navigate('/')}
            className="p-2 hover:bg-white/5 rounded-full text-text-muted hover:text-text-main transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-xs md:text-sm font-mono font-bold uppercase tracking-widest text-text-dim">
            SkillProtocol Technical Specification v2.1
          </h1>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-16 space-y-24">

        {/* 1. INTRODUCTION */}
        <section>
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="prose prose-invert max-w-none"
          >
            <h1 className="text-4xl md:text-5xl font-bold text-text-main mb-6 tracking-tight">
              The Architecture of <span className="text-primary">Verified Skill.</span>
            </h1>
            <p className="text-xl text-text-muted leading-relaxed">
              SkillProtocol is not a simple "lines of code" counter. It is a <strong>deterministic evaluation engine</strong> that combines Abstract Syntax Tree (AST) parsing, Bayesian probabilistic modeling, and Large Language Model (LLM) reasoning to mint standardized capability credits.
            </p>
          </motion.div>
        </section>

        {/* 2. THE CORE FORMULA */}
        <section>
          <h2 className="text-2xl font-bold text-text-main mb-8 flex items-center gap-3">
            <Calculator className="w-6 h-6 text-primary" />
            1. The Credit Equation
          </h2>
          
          <div className="bg-panel border border-border rounded-xl p-8 shadow-2xl overflow-x-auto relative group">
            <div className="absolute top-4 right-4 text-[10px] font-mono text-text-dim uppercase tracking-widest border border-border px-2 py-1 rounded">
              Algorithm: CREDIT_MINT_V2
            </div>
            
            <div className="font-mono text-sm md:text-base leading-loose">
              <span className="text-text-dim">// Final Calculation Logic</span><br/>
              <span className="text-primary font-bold">Total_Credits</span> = (<br/>
              &nbsp;&nbsp;<span className="text-blue-400 font-bold">Base_NCrF</span> <br/>
              &nbsp;&nbsp;* <span className="text-green-400 font-bold">SFIA_Level_Multiplier</span> <span className="text-text-dim"> // 0.5x - 1.7x</span><br/>
              &nbsp;&nbsp;* <span className="text-purple-400 font-bold">Quality_Multiplier</span> &nbsp;&nbsp;&nbsp;<span className="text-text-dim"> // 0.8x - 1.2x</span><br/>
              &nbsp;&nbsp;* <span className="text-orange-400 font-bold">Reality_Multiplier</span> &nbsp;&nbsp;&nbsp;<span className="text-text-dim"> // 0.5x or 1.0x</span><br/>
              )
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mt-8">
            <div className="bg-surface border border-border p-5 rounded-lg">
              <h3 className="text-sm font-bold text-text-main mb-2">Why Multipliers?</h3>
              <p className="text-xs text-text-muted leading-relaxed">
                Raw volume (LOC) is a poor proxy for skill. 1,000 lines of spaghetti code is worth less than 100 lines of optimized, tested architecture. Multipliers normalize this discrepancy.
              </p>
            </div>
            <div className="bg-surface border border-border p-5 rounded-lg">
              <h3 className="text-sm font-bold text-text-main mb-2">The Reality Penalty</h3>
              <p className="text-xs text-text-muted leading-relaxed">
                If the <strong>Auditor Agent</strong> detects that the code does not build (CI/CD failure), a strict <strong>0.5x penalty</strong> is applied to the final score, halving the awarded credits.
              </p>
            </div>
          </div>
        </section>

        {/* 3. NCRF & AST PARSING */}
        <section>
          <h2 className="text-2xl font-bold text-text-main mb-8 flex items-center gap-3">
            <Binary className="w-6 h-6 text-blue-400" />
            2. NCrF & Tree-sitter Parsing
          </h2>
          
          <div className="prose prose-invert max-w-none mb-8 text-sm text-text-muted">
            <p>
              We use <strong>Tree-sitter</strong> bindings for Python, TypeScript, Go, Rust, and Java to parse code into an Abstract Syntax Tree (AST). This allows us to ignore comments and whitespace, counting only logical nodes.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Complexity Table */}
            <div className="bg-panel border border-border rounded-xl p-6">
              <h3 className="text-xs font-mono font-bold text-text-dim uppercase mb-4 tracking-wider">Complexity Weights</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between items-center border-b border-border/50 pb-2">
                  <span className="text-text-main">Logical Branch (if/else)</span>
                  <span className="font-mono text-blue-400">+1 Point</span>
                </div>
                <div className="flex justify-between items-center border-b border-border/50 pb-2">
                  <span className="text-text-main">Loop (for/while)</span>
                  <span className="font-mono text-blue-400">+2 Points</span>
                </div>
                <div className="flex justify-between items-center border-b border-border/50 pb-2">
                  <span className="text-text-main">Class Definition</span>
                  <span className="font-mono text-blue-400">+3 Points</span>
                </div>
                <div className="flex justify-between items-center border-b border-border/50 pb-2">
                  <span className="text-text-main">Async/Await Pattern</span>
                  <span className="font-mono text-blue-400">+5 Points</span>
                </div>
                <div className="flex justify-between items-center pt-1">
                  <span className="text-text-main">Recursion</span>
                  <span className="font-mono text-blue-400">+8 Points</span>
                </div>
              </div>
            </div>

            {/* Learning Hours Calculation */}
            <div className="bg-panel border border-border rounded-xl p-6 flex flex-col justify-center">
              <h3 className="text-xs font-mono font-bold text-text-dim uppercase mb-4 tracking-wider">Estimated Learning Hours</h3>
              <div className="bg-surface p-4 rounded-lg font-mono text-xs text-text-muted mb-4">
                Hours = (LOC / 100) * Tier_Multiplier
              </div>
              <ul className="space-y-2 text-xs text-text-dim">
                <li className="flex justify-between"><span className="text-text-main">Simple Tier:</span> 2 hours / 100 LOC</li>
                <li className="flex justify-between"><span className="text-text-main">Moderate Tier:</span> 5 hours / 100 LOC</li>
                <li className="flex justify-between"><span className="text-text-main">Complex Tier:</span> 10 hours / 100 LOC</li>
              </ul>
              <div className="mt-4 pt-4 border-t border-border text-[10px] text-primary/80">
                * Capped at 200 hours per single repository to prevent gaming.
              </div>
            </div>
          </div>
        </section>

        {/* 4. BAYESIAN VALIDATION (Deep Dive) */}
        <section>
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-text-main flex items-center gap-3">
              <BrainCircuit className="w-6 h-6 text-purple-400" />
              3. The Bayesian Guard
            </h2>
            <span className="bg-purple-500/10 text-purple-400 px-3 py-1 rounded-full text-xs font-bold border border-purple-500/20">
              ANTI-HALLUCINATION
            </span>
          </div>

          <p className="text-text-muted mb-8 text-sm leading-relaxed max-w-3xl">
            LLMs can be biased. To prevent "grade inflation," we calculate a <strong>Prior Probability Distribution</strong> for the SFIA level <em>before</em> the LLM sees the code. This anchors the final score in statistical reality.
          </p>

          <div className="bg-panel border border-border rounded-xl p-8 relative overflow-hidden">
            {/* Background Graph Lines */}
            <div className="absolute inset-0 opacity-10 pointer-events-none">
              <svg width="100%" height="100%">
                <path d="M0,100 Q400,50 800,100" stroke="currentColor" fill="none" strokeWidth="2" />
              </svg>
            </div>

            <div className="grid md:grid-cols-2 gap-12 relative z-10">
              <div>
                <h4 className="text-sm font-bold text-white mb-4">The Likelihood Function</h4>
                <div className="font-mono text-xs text-purple-300 bg-purple-900/10 p-4 rounded-lg border border-purple-500/20 mb-4">
                  P(Level | Evidence) ∝ P(Evidence | Level) * P(Level)
                </div>
                <p className="text-xs text-text-muted">
                  We update the probability of a repo being Level 5 based on three hard metrics:
                </p>
                <ul className="mt-4 space-y-2 text-sm text-text-dim">
                  <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 bg-purple-500 rounded-full" /> <strong>Maintainability Index (MI):</strong> Uses Halstead Complexity measures.</li>
                  <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 bg-purple-500 rounded-full" /> <strong>Test Density:</strong> Ratio of test files to source files.</li>
                  <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 bg-purple-500 rounded-full" /> <strong>Git Stability:</strong> Variance in commit frequency over time.</li>
                </ul>
              </div>

              <div>
                <h4 className="text-sm font-bold text-white mb-4">The "Judge" Logic</h4>
                <div className="space-y-3">
                  <div className="flex gap-3 items-start">
                    <AlertTriangleIcon className="w-4 h-4 text-orange-400 mt-0.5" />
                    <div>
                      <div className="text-xs font-bold text-text-main">Conflict Detection</div>
                      <div className="text-[10px] text-text-muted">
                        If Bayesian Math says "Level 2" (90% conf) but LLM says "Level 5", the <strong>Judge Agent</strong> is triggered to arbitrate.
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-3 items-start">
                    <ShieldCheck className="w-4 h-4 text-green-400 mt-0.5" />
                    <div>
                      <div className="text-xs font-bold text-text-main">Evidence Requirement</div>
                      <div className="text-[10px] text-text-muted">
                        To override the Bayesian Prior, the LLM must cite specific file paths containing advanced patterns (e.g., "Custom Middleware in `auth.ts`").
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 5. SFIA FRAMEWORK DETAILS */}
        <section>
          <h2 className="text-2xl font-bold text-text-main mb-8 flex items-center gap-3">
            <Scale className="w-6 h-6 text-green-400" />
            4. SFIA Capability Levels
          </h2>
          
          <div className="overflow-hidden border border-border rounded-xl">
            <table className="w-full text-sm text-left">
              <thead className="bg-surface text-text-dim font-mono uppercase text-xs">
                <tr>
                  <th className="p-4 border-b border-border w-24">Level</th>
                  <th className="p-4 border-b border-border w-32">Title</th>
                  <th className="p-4 border-b border-border">Technical Criteria (Must Have)</th>
                  <th className="p-4 border-b border-border w-20">Mult</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                <tr className="bg-panel hover:bg-surface/50 transition-colors">
                  <td className="p-4 font-mono font-bold text-text-dim">L1</td>
                  <td className="p-4 font-bold text-text-main">Follow</td>
                  <td className="p-4 text-text-muted">Basic scripts. Single file execution. No modularity. Linear logic only.</td>
                  <td className="p-4 font-mono text-green-400">0.5x</td>
                </tr>
                <tr className="bg-panel hover:bg-surface/50 transition-colors">
                  <td className="p-4 font-mono font-bold text-text-dim">L2</td>
                  <td className="p-4 font-bold text-text-main">Assist</td>
                  <td className="p-4 text-text-muted">Functions used. Some separation of concerns. Basic error printing. No tests.</td>
                  <td className="p-4 font-mono text-green-400">0.8x</td>
                </tr>
                <tr className="bg-panel hover:bg-surface/50 transition-colors">
                  <td className="p-4 font-mono font-bold text-text-dim">L3</td>
                  <td className="p-4 font-bold text-text-main">Apply</td>
                  <td className="p-4 text-text-muted"><strong>Professional Baseline.</strong> Modular structure (folder organization). README present. Dependency management (package.json).</td>
                  <td className="p-4 font-mono text-green-400">1.0x</td>
                </tr>
                <tr className="bg-panel hover:bg-surface/50 transition-colors">
                  <td className="p-4 font-mono font-bold text-text-dim">L4</td>
                  <td className="p-4 font-bold text-text-main">Enable</td>
                  <td className="p-4 text-text-muted">Unit Tests present. Design patterns (Singleton, Factory). Async/Concurrency usage. Robust Error Handling.</td>
                  <td className="p-4 font-mono text-green-400">1.3x</td>
                </tr>
                <tr className="bg-panel hover:bg-surface/50 transition-colors">
                  <td className="p-4 font-mono font-bold text-text-dim">L5</td>
                  <td className="p-4 font-bold text-text-main">Ensure</td>
                  <td className="p-4 text-text-muted">CI/CD Pipelines (GitHub Actions). Containerization (Docker). Architecture documentation. High test coverage.</td>
                  <td className="p-4 font-mono text-green-400">1.7x</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* 6. THE AGENT SWARM */}
        <section>
          <h2 className="text-2xl font-bold text-text-main mb-8 flex items-center gap-3">
            <Network className="w-6 h-6 text-orange-400" />
            5. The 6-Agent Swarm
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AgentCard 
              name="Validator" 
              icon={ShieldCheck} 
              desc="Gatekeeper. Checks repo accessibility, size limits, and privacy settings before resource allocation." 
            />
            <AgentCard 
              name="Scanner" 
              icon={Terminal} 
              desc="The Eye. Clones the repo to a sandbox, runs Tree-sitter, calculates NCrF stats, and extracts file samples." 
            />
            <AgentCard 
              name="Reviewer" 
              icon={Layers} 
              desc="Forensic Architect. Analyzes code samples for 'Smells' vs 'Patterns'. Determines Quality Multiplier." 
            />
            <AgentCard 
              name="Grader" 
              icon={Scale} 
              desc="Assessor. Uses the SFIA rubric to propose a capability level based on Scanner and Reviewer evidence." 
            />
            <AgentCard 
              name="Judge" 
              icon={BrainCircuit} 
              desc="The Supreme Court. Compares the Grader's proposal against the Bayesian Prior. Issues final verdict." 
            />
            <AgentCard 
              name="Auditor" 
              icon={CheckCircle2} 
              desc="Reality Check. Queries GitHub Actions API. If the build fails, applies the 50% penalty." 
            />
          </div>
        </section>

        {/* Footer */}
        <div className="border-t border-border pt-12 text-center">
          <p className="text-text-dim text-xs font-mono">
            END OF SPECIFICATION · GENERATED BY SKILLPROTOCOL SYSTEM
          </p>
        </div>

      </div>
    </div>
  )
}

// Sub-component for Agent Cards
function AgentCard({ name, icon: Icon, desc }) {
  return (
    <div className="bg-panel border border-border p-5 rounded-xl hover:border-primary/30 transition-colors group">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 bg-surface rounded-lg text-text-dim group-hover:text-primary transition-colors">
          <Icon className="w-5 h-5" />
        </div>
        <h3 className="font-bold text-text-main">{name} Agent</h3>
      </div>
      <p className="text-sm text-text-muted leading-relaxed">
        {desc}
      </p>
    </div>
  )
}

function AlertTriangleIcon({ className }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      width="24" height="24" viewBox="0 0 24 24" 
      fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" 
      className={className}
    >
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
      <path d="M12 9v4"/>
      <path d="M12 17h.01"/>
    </svg>
  )
}