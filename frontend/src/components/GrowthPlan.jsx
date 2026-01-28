import { motion } from 'framer-motion'
import { 
  Target, Zap, TrendingUp, BookOpen, 
  CheckCircle2, ArrowRight, AlertTriangle, Lightbulb 
} from 'lucide-react'

export default function GrowthPlan({ plan, currentLevel }) {
  if (!plan) return null;

  const { 
    current_assessment, 
    next_level_requirements, 
    actionable_roadmap, 
    quick_wins, 
    credit_projection 
  } = plan;

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Header Section */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-text-main flex items-center justify-center gap-2 mb-2">
          <Target className="w-6 h-6 text-primary" />
          Your Path to Level {currentLevel + 1}
        </h2>
        <p className="text-text-muted max-w-2xl mx-auto">
          Our Mentor Agent has analyzed your code and identified a concrete roadmap to increase your verified skill credits.
        </p>
      </div>

      {/* 1. Credit Projection Card */}
      <div className="bg-panel border border-primary/30 rounded-xl p-6 relative overflow-hidden shadow-lg shadow-primary/5">
        <div className="absolute top-0 right-0 p-4 opacity-5">
          <TrendingUp className="w-32 h-32" />
        </div>
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-6">
          <div>
            <h3 className="text-lg font-bold text-text-main mb-1">Impact Projection</h3>
            <p className="text-sm text-text-muted">If you complete this roadmap:</p>
          </div>
          <div className="flex items-center gap-8 bg-surface/50 p-4 rounded-lg border border-border">
            <div className="text-center">
              <div className="text-xs text-text-dim uppercase tracking-wider font-bold">Current</div>
              <div className="text-2xl font-mono font-bold text-text-muted">{credit_projection.current_credits.toFixed(1)}</div>
            </div>
            <ArrowRight className="w-5 h-5 text-primary animate-pulse" />
            <div className="text-center">
              <div className="text-xs text-primary uppercase tracking-wider font-bold">Potential</div>
              <div className="text-3xl font-mono font-bold text-primary">{credit_projection.potential_credits_after_improvements.toFixed(1)}</div>
            </div>
            <div className="text-xs font-bold text-success bg-success/10 px-2 py-1 rounded-full border border-success/20">
              +{credit_projection.percentage_increase.toFixed(0)}% Boost
            </div>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        
        {/* 2. Quick Wins (Immediate Action) */}
        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-sm font-bold text-text-main uppercase tracking-wider mb-4 flex items-center gap-2">
            <Zap className="w-4 h-4 text-yellow-400" />
            Quick Wins
          </h3>
          <ul className="space-y-3">
            {quick_wins.map((win, idx) => (
              <li key={idx} className="flex items-start gap-3 p-3 bg-panel border border-border rounded-lg hover:border-primary/30 transition-colors">
                <CheckCircle2 className="w-4 h-4 text-success mt-0.5 shrink-0" />
                <span className="text-sm text-text-main">{win}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 3. The Gap Analysis */}
        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-sm font-bold text-text-main uppercase tracking-wider mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            Missing Requirements
          </h3>
          <div className="space-y-4">
            <div>
              <span className="text-xs text-text-dim font-bold block mb-1">TECHNICAL SKILLS</span>
              <div className="flex flex-wrap gap-2">
                {next_level_requirements.missing_technical_skills.map((skill, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-red-500/10 text-red-400 border border-red-500/20 rounded">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <span className="text-xs text-text-dim font-bold block mb-1">ARCHITECTURE</span>
              <div className="flex flex-wrap gap-2">
                {next_level_requirements.missing_architectural_patterns.map((pat, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-orange-500/10 text-orange-400 border border-orange-500/20 rounded">
                    {pat}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Actionable Roadmap */}
      <div className="bg-panel border border-border rounded-xl overflow-hidden">
        <div className="p-6 border-b border-border bg-surface/30">
          <h3 className="text-lg font-bold text-text-main flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-blue-400" />
            Strategic Roadmap
          </h3>
        </div>
        <div className="divide-y divide-border">
          {actionable_roadmap.map((step) => (
            <div key={step.step_number} className="p-6 hover:bg-surface/50 transition-colors group">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface border border-border flex items-center justify-center font-mono text-sm text-text-muted group-hover:border-primary/50 group-hover:text-primary transition-colors">
                  {step.step_number}
                </div>
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-3 mb-2">
                    <h4 className="text-base font-bold text-text-main">{step.action}</h4>
                    <span className={`text-[10px] px-2 py-0.5 rounded border uppercase font-bold tracking-wider
                      ${step.difficulty === 'beginner' ? 'bg-green-500/10 text-green-400 border-green-500/20' : 
                        step.difficulty === 'intermediate' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : 
                        'bg-purple-500/10 text-purple-400 border-purple-500/20'}`}>
                      {step.difficulty}
                    </span>
                    <span className="text-[10px] text-text-dim flex items-center gap-1">
                      <Lightbulb className="w-3 h-3" /> {step.estimated_time}
                    </span>
                  </div>
                  
                  {step.resources && step.resources.length > 0 && (
                    <div className="mt-3 bg-surface p-3 rounded-lg border border-border">
                      <div className="text-xs text-text-dim mb-2 font-bold uppercase">Recommended Resources</div>
                      <ul className="space-y-1">
                        {step.resources.map((res, i) => (
                          <li key={i} className="text-sm text-primary hover:underline cursor-pointer flex items-center gap-2">
                            <ArrowRight className="w-3 h-3" />
                            {res}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}