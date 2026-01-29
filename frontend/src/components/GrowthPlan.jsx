import { motion } from 'framer-motion'
import { 
  Target, Zap, TrendingUp, BookOpen, 
  CheckCircle2, ArrowRight, AlertTriangle, Lightbulb,
  Award, Code, Rocket
} from 'lucide-react'

export default function GrowthPlan({ plan, currentLevel }) {
  // ✅ FIX: Add defensive checks and handle missing data
  if (!plan) {
    return (
      <div className="bg-surface border border-border rounded-xl p-6 text-center">
        <p className="text-text-muted">No mentorship plan available</p>
      </div>
    )
  }

  // ✅ FIX: Safely extract data with fallbacks
  const {
    current_assessment = {},
    next_level_requirements = {},
    actionable_roadmap = [],
    quick_wins = [],
    credit_projection = {},
    current_level: planCurrentLevel,
    target_level: planTargetLevel,
    priority_skills = [],
    learning_plan = {},
    estimated_time_to_next_level,
    recommended_resources = [],
    practice_projects = [],
    actionable_steps = [],
    motivation
  } = plan

  // ✅ Determine levels (handle both old and new format)
  const effectiveCurrentLevel = planCurrentLevel || currentLevel || 1
  const effectiveTargetLevel = planTargetLevel || effectiveCurrentLevel + 1


  // ✅ Handle credit projection (may not exist in all plans)
  const currentCredits = credit_projection?.current_credits ?? 0
  const potentialCredits = credit_projection?.potential_credits_after_improvements ?? 0
  const percentageIncrease = credit_projection?.percentage_increase ?? 0

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Header Section */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-text-main flex items-center justify-center gap-2 mb-2">
          <Target className="w-6 h-6 text-primary" />
          Your Path to Level {effectiveTargetLevel}
        </h2>
        <p className="text-text-muted max-w-2xl mx-auto">
          {current_assessment?.current_level_justification || 
           "Our Mentor Agent has analyzed your code and identified a concrete roadmap to increase your verified skill credits."}
        </p>
      </div>

      {/* Credit Projection Card (if available) */}
      {(currentCredits > 0 || potentialCredits > 0) && (
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
                <div className="text-2xl font-mono font-bold text-text-muted">{currentCredits.toFixed(1)}</div>
              </div>
              <ArrowRight className="w-5 h-5 text-primary animate-pulse" />
              <div className="text-center">
                <div className="text-xs text-primary uppercase tracking-wider font-bold">Potential</div>
                <div className="text-3xl font-mono font-bold text-primary">{potentialCredits.toFixed(1)}</div>
              </div>
              {percentageIncrease > 0 && (
                <div className="text-xs font-bold text-success bg-success/10 px-2 py-1 rounded-full border border-success/20">
                  +{percentageIncrease.toFixed(0)}% Boost
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Quick Wins Section */}
      {quick_wins.length > 0 && (
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
      )}

      {/* Priority Skills / Missing Requirements */}
      {(priority_skills.length > 0 || next_level_requirements?.missing_technical_skills?.length > 0) && (
        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-sm font-bold text-text-main uppercase tracking-wider mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            Focus Areas
          </h3>
          <div className="space-y-4">
            {/* Priority Skills */}
            {priority_skills.length > 0 && (
              <div>
                <span className="text-xs text-text-dim font-bold block mb-2">PRIORITY SKILLS</span>
                <div className="flex flex-wrap gap-2">
                  {priority_skills.map((skill, i) => (
                    <span key={i} className="text-xs px-3 py-1.5 bg-primary/10 text-primary border border-primary/20 rounded-full">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Missing Technical Skills */}
            {next_level_requirements?.missing_technical_skills?.length > 0 && (
              <div>
                <span className="text-xs text-text-dim font-bold block mb-2">TECHNICAL SKILLS</span>
                <div className="flex flex-wrap gap-2">
                  {next_level_requirements.missing_technical_skills.map((skill, i) => (
                    <span key={i} className="text-xs px-2 py-1 bg-red-500/10 text-red-400 border border-red-500/20 rounded">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Missing Architectural Patterns */}
            {next_level_requirements?.missing_architectural_patterns?.length > 0 && (
              <div>
                <span className="text-xs text-text-dim font-bold block mb-2">ARCHITECTURE</span>
                <div className="flex flex-wrap gap-2">
                  {next_level_requirements.missing_architectural_patterns.map((pat, i) => (
                    <span key={i} className="text-xs px-2 py-1 bg-orange-500/10 text-orange-400 border border-orange-500/20 rounded">
                      {pat}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Actionable Roadmap */}
      {actionable_roadmap.length > 0 && (
        <div className="bg-panel border border-border rounded-xl overflow-hidden">
          <div className="p-6 border-b border-border bg-surface/30">
            <h3 className="text-lg font-bold text-text-main flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-blue-400" />
              Strategic Roadmap
            </h3>
          </div>
          <div className="divide-y divide-border">
            {actionable_roadmap.map((step, idx) => (
              <div key={idx} className="p-6 hover:bg-surface/50 transition-colors group">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface border border-border flex items-center justify-center font-mono text-sm text-text-muted group-hover:border-primary/50 group-hover:text-primary transition-colors">
                    {step.step_number || idx + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-3 mb-2">
                      <h4 className="text-base font-bold text-text-main">{step.action}</h4>
                      {step.difficulty && (
                        <span className={`text-[10px] px-2 py-0.5 rounded border uppercase font-bold tracking-wider
                          ${step.difficulty === 'beginner' ? 'bg-green-500/10 text-green-400 border-green-500/20' : 
                            step.difficulty === 'intermediate' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : 
                            'bg-purple-500/10 text-purple-400 border-purple-500/20'}`}>
                          {step.difficulty}
                        </span>
                      )}
                      {step.estimated_time && (
                        <span className="text-[10px] text-text-dim flex items-center gap-1">
                          <Lightbulb className="w-3 h-3" /> {step.estimated_time}
                        </span>
                      )}
                    </div>
                    
                    {/* Resources */}
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
      )}

        {/* ✅ ADD: Fallback if actionable_roadmap is empty but actionable_steps exists */}
        {actionable_steps.length > 0 && actionable_roadmap.length === 0 && (
          <div className="bg-surface border border-border rounded-xl p-6">
            <h3 className="text-sm font-bold text-text-main uppercase tracking-wider mb-4 flex items-center gap-2">
              <Rocket className="w-4 h-4 text-blue-400" />
              Action Steps
            </h3>
            <ol className="space-y-3 list-decimal list-inside">
              {actionable_steps.map((step, idx) => (
                <li key={idx} className="text-sm text-text-main p-3 bg-panel border border-border rounded-lg">
                  {step}
                </li>
              ))}
            </ol>
          </div>
        )}

      

      {/* Practice Projects */}
      {practice_projects.length > 0 && (
        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-sm font-bold text-text-main uppercase tracking-wider mb-4 flex items-center gap-2">
            <Code className="w-4 h-4 text-green-400" />
            Practice Projects
          </h3>
          <div className="space-y-3">
            {practice_projects.map((project, idx) => (
              <div key={idx} className="p-4 bg-panel border border-border rounded-lg">
                <h4 className="font-bold text-text-main mb-1">{project.title || `Project ${idx + 1}`}</h4>
                <p className="text-sm text-text-muted mb-2">{project.focus || project.description}</p>
                {project.difficulty && (
                  <span className="text-xs px-2 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded">
                    {project.difficulty}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Estimated Time */}
      {estimated_time_to_next_level && (
        <div className="bg-primary/5 border border-primary/20 rounded-xl p-4 text-center">
          <div className="text-sm text-text-muted mb-1">Estimated Time to Level {effectiveTargetLevel}</div>
          <div className="text-2xl font-bold text-primary">{estimated_time_to_next_level}</div>
        </div>
      )}

      {/* Motivation Message */}
      {motivation && (
        <div className="bg-surface border border-border rounded-xl p-6 text-center">
          <Award className="w-8 h-8 text-primary mx-auto mb-3" />
          <p className="text-text-main italic">"{motivation}"</p>
        </div>
      )}

      {/* Current Assessment Details */}
      {current_assessment?.strengths?.length > 0 && (
        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-sm font-bold text-text-main uppercase tracking-wider mb-4">Current Assessment</h3>
          <div className="space-y-4">
            <div>
              <h4 className="text-xs text-text-dim font-bold mb-2">STRENGTHS</h4>
              <ul className="space-y-2">
                {current_assessment.strengths.map((strength, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-text-main">
                    <CheckCircle2 className="w-4 h-4 text-success mt-0.5 shrink-0" />
                    {strength}
                  </li>
                ))}
              </ul>
            </div>
            {current_assessment.weaknesses?.length > 0 && (
              <div>
                <h4 className="text-xs text-text-dim font-bold mb-2">AREAS FOR IMPROVEMENT</h4>
                <ul className="space-y-2">
                  {current_assessment.weaknesses.map((weakness, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-text-main">
                      <AlertTriangle className="w-4 h-4 text-orange-400 mt-0.5 shrink-0" />
                      {weakness}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Learning Plan (if using alternative format) */}
      {learning_plan?.phase_1 && (
        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-sm font-bold text-text-main uppercase tracking-wider mb-4">Learning Phases</h3>
          <div className="space-y-3">
            {Object.entries(learning_plan).map(([phase, description]) => (
              <div key={phase} className="p-3 bg-panel border border-border rounded-lg">
                <div className="font-bold text-text-main mb-1 capitalize">{phase.replace('_', ' ')}</div>
                <p className="text-sm text-text-muted">{description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Resources (if at root level) */}
      {recommended_resources.length > 0 && (
        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-sm font-bold text-text-main uppercase tracking-wider mb-4">Recommended Resources</h3>
          <ul className="space-y-2">
            {recommended_resources.map((resource, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-primary hover:underline cursor-pointer">
                <ArrowRight className="w-3 h-3" />
                {resource}
              </li>
            ))}
          </ul>
        </div>
      )}

    </div>
  )
}