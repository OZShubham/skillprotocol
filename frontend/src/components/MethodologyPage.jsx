import { motion } from 'framer-motion'
import { 
  ArrowLeft, Calculator, BrainCircuit, Scale, 
  ShieldCheck, Network, Binary, CheckCircle2, 
  Terminal, FileCode, Layers, GitCommit, Database,
  Cpu, TrendingUp, Zap, BookOpen
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

        {/* Introduction */}
        <section>
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="prose prose-invert max-w-none"
          >
            <h1 className="text-4xl md:text-5xl font-bold text-text-main mb-6 tracking-tight">
              The Architecture of <span className="text-primary">Hybrid Verification.</span>
            </h1>
            <p className="text-xl text-text-muted leading-relaxed">
              SkillProtocol is a <strong>hybrid verification system</strong> that combines deterministic code analysis 
              with AI reasoning. We use Abstract Syntax Tree (AST) parsing, Bayesian probabilistic modeling, 
              and Large Language Model evaluation to mint standardized capability credits.
            </p>
            
            <div className="bg-primary/5 border border-primary/20 rounded-xl p-6 mt-6">
              <h3 className="text-lg font-bold text-primary mb-2">🎯 Key Distinction</h3>
              <p className="text-sm text-text-muted leading-relaxed">
                Unlike fully autonomous AI agent systems, SkillProtocol uses a <strong>hybrid approach</strong>:
              </p>
              <ul className="text-sm text-text-muted mt-3 space-y-1">
                <li><strong className="text-text-main">3 Deterministic Workers:</strong> Validator, Scanner, Auditor (pure functions)</li>
                <li><strong className="text-text-main">3 AI Agents:</strong> Grader, Judge, Mentor (LLM-powered reasoning)</li>
                <li><strong className="text-text-main">Orchestration:</strong> LangGraph state machine coordinates the pipeline</li>
              </ul>
            </div>
          </motion.div>
        </section>

        {/* Core Formula */}
        <section>
          <h2 className="text-2xl font-bold text-text-main mb-8 flex items-center gap-3">
            <Calculator className="w-6 h-6 text-primary" />
            1. The Credit Equation
          </h2>
          
          <div className="bg-panel border border-border rounded-xl p-8 shadow-2xl overflow-x-auto relative group">
            <div className="absolute top-4 right-4 text-[10px] font-mono text-text-dim uppercase tracking-widest border border-border px-2 py-1 rounded">
              Algorithm: CREDIT_MINT_V2.1
            </div>
            
            <div className="font-mono text-sm md:text-base leading-loose">
              <span className="text-text-dim">// Multi-Dimensional Credit Calculation</span><br/>
              <span className="text-primary font-bold">Total_Credits</span> = (<br/>
              &nbsp;&nbsp;<span className="text-blue-400 font-bold">Base_NCrF</span> <br/>
              &nbsp;&nbsp;* <span className="text-green-400 font-bold">SFIA_Level_Multiplier</span> <span className="text-text-dim"> // 0.5x - 1.7x (AI)</span><br/>
              &nbsp;&nbsp;* <span className="text-purple-400 font-bold">Quality_Multiplier</span> &nbsp;&nbsp;&nbsp;<span className="text-text-dim"> // 0.8x - 1.2x (AST)</span><br/>
              &nbsp;&nbsp;* <span className="text-orange-400 font-bold">Semantic_Multiplier</span> &nbsp;&nbsp;<span className="text-text-dim"> // 0.5x - 1.5x (Gemini)</span><br/>
              &nbsp;&nbsp;* <span className="text-red-400 font-bold">Reality_Multiplier</span> &nbsp;&nbsp;&nbsp;<span className="text-text-dim"> // 0.5x or 1.0x (CI/CD)</span><br/>
              )
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mt-8">
            <div className="bg-surface border border-border p-5 rounded-lg">
              <h3 className="text-sm font-bold text-text-main mb-2">Why Multiple Multipliers?</h3>
              <p className="text-xs text-text-muted leading-relaxed">
                Each dimension captures different aspects of code quality:
                <ul className="mt-2 space-y-1 ml-4">
                  <li>• <strong>SFIA:</strong> Developer capability level</li>
                  <li>• <strong>Quality:</strong> Code health (anti-patterns)</li>
                  <li>• <strong>Semantic:</strong> Architectural sophistication</li>
                  <li>• <strong>Reality:</strong> Does it actually work?</li>
                </ul>
              </p>
            </div>
            <div className="bg-surface border border-border p-5 rounded-lg">
              <h3 className="text-sm font-bold text-text-main mb-2">The Reality Penalty</h3>
              <p className="text-xs text-text-muted leading-relaxed">
                If the <strong>Auditor Worker</strong> detects that CI/CD tests fail, a strict <strong>0.5x penalty</strong> 
                is applied. Code that doesn't build is worth 50% less, regardless of other factors.
              </p>
            </div>
          </div>
        </section>

        {/* NCrF & Tree-sitter */}
        <section>
          <h2 className="text-2xl font-bold text-text-main mb-8 flex items-center gap-3">
            <Binary className="w-6 h-6 text-blue-400" />
            2. NCrF & Tree-sitter Parsing
          </h2>
          
          <div className="prose prose-invert max-w-none mb-8 text-sm text-text-muted">
            <p>
              We use <strong>Tree-sitter</strong> universal parser with language bindings for Python, TypeScript, 
              JavaScript, Java, Go, Rust, C++, Ruby, PHP, and C#. This allows us to ignore comments and whitespace, 
              counting only logical nodes in the Abstract Syntax Tree.
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

            {/* Learning Hours */}
            <div className="bg-panel border border-border rounded-xl p-6 flex flex-col justify-center">
              <h3 className="text-xs font-mono font-bold text-text-dim uppercase mb-4 tracking-wider">NCrF Standard</h3>
              <div className="bg-surface p-4 rounded-lg font-mono text-xs text-text-muted mb-4">
                Credits = Learning_Hours / 30
              </div>
              <ul className="space-y-2 text-xs text-text-dim">
                <li className="flex justify-between"><span className="text-text-main">Simple Tier:</span> 2 hours / 100 LOC</li>
                <li className="flex justify-between"><span className="text-text-main">Moderate Tier:</span> 5 hours / 100 LOC</li>
                <li className="flex justify-between"><span className="text-text-main">Complex Tier:</span> 10 hours / 100 LOC</li>
              </ul>
              <div className="mt-4 pt-4 border-t border-border text-[10px] text-primary/80">
                * Capped at 200 hours per repository to prevent gaming
              </div>
            </div>
          </div>
        </section>

        {/* Bayesian Validation */}
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
            LLMs can hallucinate or be biased. To prevent "grade inflation," we calculate a <strong>Prior Probability 
            Distribution</strong> for the SFIA level <em>before</em> the AI agents see the code. This anchors the 
            final score in statistical reality.
          </p>

          <div className="bg-panel border border-border rounded-xl p-8 relative overflow-hidden">
            <div className="grid md:grid-cols-2 gap-12 relative z-10">
              <div>
                <h4 className="text-sm font-bold text-white mb-4">The Likelihood Function</h4>
                <div className="font-mono text-xs text-purple-300 bg-purple-900/10 p-4 rounded-lg border border-purple-500/20 mb-4">
                  P(Level | Evidence) ∝ P(Evidence | Level) * P(Level)
                </div>
                <p className="text-xs text-text-muted">
                  We update the probability based on hard metrics:
                </p>
                <ul className="mt-4 space-y-2 text-sm text-text-dim">
                  <li className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-purple-500 rounded-full" /> 
                    <strong>Maintainability Index (MI):</strong> Halstead complexity
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-purple-500 rounded-full" /> 
                    <strong>Test Density:</strong> Ratio of test files
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-purple-500 rounded-full" /> 
                    <strong>Git Stability:</strong> Commit frequency variance
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="text-sm font-bold text-white mb-4">The Judge Agent Logic</h4>
                <div className="space-y-3">
                  <div className="flex gap-3 items-start">
                    <Zap className="w-4 h-4 text-orange-400 mt-0.5" />
                    <div>
                      <div className="text-xs font-bold text-text-main">Conflict Detection</div>
                      <div className="text-[10px] text-text-muted">
                        If Bayesian says "Level 2" (90% conf) but Grader says "Level 5", 
                        the <strong>Judge Agent</strong> is triggered.
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-3 items-start">
                    <ShieldCheck className="w-4 h-4 text-green-400 mt-0.5" />
                    <div>
                      <div className="text-xs font-bold text-text-main">Evidence Requirement</div>
                      <div className="text-[10px] text-text-muted">
                        To override Bayesian Math, Grader must cite specific file paths with 
                        advanced patterns (e.g., "Middleware in `auth.ts`").
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* SFIA Framework */}
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
                  <td className="p-4 text-text-muted">Basic scripts. Single file. Linear logic. No modularity.</td>
                  <td className="p-4 font-mono text-green-400">0.5x</td>
                </tr>
                <tr className="bg-panel hover:bg-surface/50 transition-colors">
                  <td className="p-4 font-mono font-bold text-text-dim">L2</td>
                  <td className="p-4 font-bold text-text-main">Assist</td>
                  <td className="p-4 text-text-muted">Functions used. Some separation. Basic error printing. No tests.</td>
                  <td className="p-4 font-mono text-green-400">0.8x</td>
                </tr>
                <tr className="bg-panel hover:bg-surface/50 transition-colors">
                  <td className="p-4 font-mono font-bold text-text-dim">L3</td>
                  <td className="p-4 font-bold text-text-main">Apply</td>
                  <td className="p-4 text-text-muted"><strong>Professional Baseline.</strong> Modular structure. README. Dependencies managed.</td>
                  <td className="p-4 font-mono text-green-400">1.0x</td>
                </tr>
                <tr className="bg-panel hover:bg-surface/50 transition-colors">
                  <td className="p-4 font-mono font-bold text-text-dim">L4</td>
                  <td className="p-4 font-bold text-text-main">Enable</td>
                  <td className="p-4 text-text-muted">Unit Tests. Design patterns (Factory, Strategy). Async. Robust errors.</td>
                  <td className="p-4 font-mono text-green-400">1.3x</td>
                </tr>
                <tr className="bg-panel hover:bg-surface/50 transition-colors">
                  <td className="p-4 font-mono font-bold text-text-dim">L5</td>
                  <td className="p-4 font-bold text-text-main">Ensure</td>
                  <td className="p-4 text-text-muted">CI/CD Pipelines. Docker. Architecture docs. High test coverage.</td>
                  <td className="p-4 font-mono text-green-400">1.7x</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Hybrid System */}
        <section>
          <h2 className="text-2xl font-bold text-text-main mb-8 flex items-center gap-3">
            <Network className="w-6 h-6 text-orange-400" />
            5. The Hybrid Verification Pipeline
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <WorkerCard 
              name="Validator" 
              icon={ShieldCheck}
              type="Worker"
              desc="Checks repo accessibility, size limits, privacy. Returns validation status." 
            />
            <WorkerCard 
              name="Scanner" 
              icon={Terminal}
              type="Worker"
              desc="Tree-sitter AST parsing. Calculates NCrF, complexity, patterns. Extracts code samples." 
            />
            <AgentCard 
              name="Grader" 
              icon={Scale}
              type="AI Agent"
              desc="Groq Llama 3.3 evaluates code against SFIA rubric. Uses tools to read files and validate evidence." 
            />
            <AgentCard 
              name="Judge" 
              icon={BrainCircuit}
              type="AI Agent"
              desc="Gemini 3 Flash arbitrates conflicts between Bayesian and Grader. Final verdict." 
            />
            <WorkerCard 
              name="Auditor" 
              icon={CheckCircle2}
              type="Worker"
              desc="Queries GitHub Actions API. Applies 50% penalty if CI/CD tests fail." 
            />
            <AgentCard 
              name="Mentor" 
              icon={BookOpen}
              type="AI Agent"
              desc="Gemini 3 analyzes gaps and generates personalized improvement roadmap with concrete steps." 
            />
          </div>

          <div className="mt-8 bg-primary/5 border border-primary/20 rounded-xl p-6">
            <h3 className="text-sm font-bold text-primary mb-3">🔄 Orchestration: LangGraph State Machine</h3>
            <p className="text-xs text-text-muted leading-relaxed">
              The workflow is orchestrated by a LangGraph state machine with conditional routing:
            </p>
            <div className="mt-4 font-mono text-xs bg-surface border border-border p-4 rounded-lg">
              Validator → Scanner → Grader → Judge → Auditor → Mentor → Reporter
              <br/><span className="text-text-dim">// Conditional edges handle failures and retries</span>
            </div>
          </div>
        </section>

        {/* Footer */}
        <div className="border-t border-border pt-12 text-center">
          <p className="text-text-dim text-xs font-mono">
            END OF SPECIFICATION · GENERATED BY SKILLPROTOCOL SYSTEM v2.1
          </p>
        </div>

      </div>
    </div>
  )
}

// Component Cards
function WorkerCard({ name, icon: Icon, type, desc }) {
  return (
    <div className="bg-panel border border-border p-5 rounded-xl hover:border-success/30 transition-colors group">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 bg-surface rounded-lg text-success border border-success/20">
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-bold text-text-main">{name}</h3>
          <span className="text-[10px] font-mono text-success uppercase tracking-wider">{type}</span>
        </div>
      </div>
      <p className="text-sm text-text-muted leading-relaxed">
        {desc}
      </p>
    </div>
  )
}

function AgentCard({ name, icon: Icon, type, desc }) {
  return (
    <div className="bg-panel border border-primary/20 p-5 rounded-xl hover:border-primary/50 transition-colors group">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 bg-primary/10 rounded-lg text-primary border border-primary/30">
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-bold text-text-main">{name}</h3>
          <span className="text-[10px] font-mono text-primary uppercase tracking-wider">{type}</span>
        </div>
      </div>
      <p className="text-sm text-text-muted leading-relaxed">
        {desc}
      </p>
    </div>
  )
}