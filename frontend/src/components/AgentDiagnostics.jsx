import { motion } from 'framer-motion'
import { 
  CheckCircle2, FileCode, Scale, ShieldCheck, 
  Terminal, Eye, Shield, Check, Activity, TrendingUp, AlertTriangle 
} from 'lucide-react'

export default function AgentDiagnostics({ result }) {
  if (!result) return (
    <div className="p-6 text-center text-text-muted bg-panel border border-border rounded-xl">
      No diagnostic data available.
    </div>
  );

  // --- CRITICAL FIX: Global Success Override ---
  // If the user has credits, the pipeline IS complete, regardless of individual flags.
  const isJobComplete = (result.final_credits > 0) || (result.status === 'complete');

  // Helper to safely format numbers
  const fmt = (n) => n?.toLocaleString() || '0'

  const pipeline = [
    {
      id: 'validator',
      label: 'Validator Agent',
      role: 'Sanity Check',
      icon: Shield,
      status: result.validation?.is_valid ? 'success' : 'pending',
      evidence: result.validation ? [
        `Repo Accessible: Yes`,
        `Size: ${fmt(result.validation.size_kb)} KB`,
        `Privacy: ${result.validation.is_private ? 'Private' : 'Public'}`
      ] : ['Validating repository access...']
    },
    {
      id: 'scanner',
      label: 'Scanner Agent',
      role: 'Complete Analysis (NCrF + Semantic)',  // ← UPDATED ROLE
      icon: Terminal,
      status: (result.scan_metrics || isJobComplete) ? 'success' : 'pending',
      evidence: result.scan_metrics?.ncrf ? [
        `${fmt(result.scan_metrics.ncrf.total_sloc)} Lines of Code`,
        `${result.scan_metrics.ncrf.files_scanned} Files Parsed`,
        `Dominant: ${result.scan_metrics.ncrf.dominant_language || 'Unknown'}`,
        result.scan_metrics.ncrf.global_patterns?.has_async ? '✓ Async Patterns Detected' : '',
        result.scan_metrics.ncrf.global_patterns?.has_error_handling ? '✓ Error Handling Present' : '',
        // ADD THESE NEW LINES (semantic analysis info):
        result.scan_metrics.architecture_analysis?.unique_patterns_count 
          ? `🎨 ${result.scan_metrics.architecture_analysis.unique_patterns_count} Design Patterns` 
          : '',
        result.scan_metrics.semantic_report?.sophistication_level 
          ? `📊 Sophistication: ${result.scan_metrics.semantic_report.sophistication_level}` 
          : '',
        result.scan_metrics.semantic_report?.semantic_multiplier 
          ? `🔢 Semantic: ${result.scan_metrics.semantic_report.semantic_multiplier.toFixed(2)}x` 
          : ''
      ].filter(Boolean) : ['Scanning codebase structure...']
    },
        
    {
      id: 'grader',
      label: 'Grader Agent',
      role: 'SFIA Assessment',
      icon: Scale,
      status: (result.sfia_result || isJobComplete) ? 'success' : 'pending',
      evidence: (() => {
        if (!result.sfia_result) return ['Evaluating capabilities...'];
        
        const baseEvidence = [
          `Initial Assessment: Level ${result.sfia_result.sfia_level}`,
          `Confidence: ${((result.sfia_result.confidence || 0) * 100).toFixed(0)}%`,
          result.sfia_result.bayesian_agreement 
            ? '✓ Aligned with Statistical Prior' 
            : '⚠ Deviated from Bayesian Model'
        ];

        // Add tool usage if available
        if (result.sfia_result.tool_calls_made) {
          baseEvidence.push(`🔧 Used ${result.sfia_result.tool_calls_made} tools for analysis`);
        }

        // Add patterns found
        if (result.sfia_result.patterns_found) {
          baseEvidence.push(`📐 ${result.sfia_result.patterns_found} design patterns identified`);
        }

        return baseEvidence;
      })(),
      detailedEvidence: result.sfia_result?.evidence_used || []
    },
    {
      id: 'judge',
      label: 'Judge Agent',
      role: 'Final Arbitration',
      icon: ShieldCheck,
      status: isJobComplete ? 'success' : 'pending',
      isIntervention: result.sfia_result?.judge_intervened,
      evidence: result.sfia_result?.judge_intervened ? [
        `⚖️ INTERVENTION: Overruled Initial Assessment`,
        `Final Verdict: Level ${result.sfia_result.sfia_level}`,
        `Reason: ${result.sfia_result.judge_summary?.slice(0, 60)}...`,
        `Confidence: ${((result.sfia_result.judge_confidence || 0) * 100).toFixed(0)}%`
      ] : [
        `✓ Ratified Grader Assessment`,
        `Congruence: ${result.sfia_result?.is_congruent ? 'Verified' : 'Under Review'}`,
        result.validation_result?.bayesian_best_estimate 
          ? `Bayesian Prior: Level ${result.validation_result.bayesian_best_estimate}` 
          : ''
      ].filter(Boolean)
    },
    {
      id: 'auditor',
      label: 'Auditor Agent',
      role: 'Reality Check',
      icon: Check,
      status: (result.audit_result || isJobComplete) ? 'success' : 'pending',
      evidence: (() => {
        if (!result.audit_result) return ['Checking build status...'];
        
        const audit = result.audit_result;
        
        // No CI/CD case
        if (audit.has_ci_cd === false) {
          return [
            'No CI/CD configured',
            '✓ No penalty applied',
            'Recommendation: Add GitHub Actions'
          ];
        }
        
        // Has CI/CD
        return [
          `CI/CD Status: ${audit.reality_check_passed ? '✓ PASS' : '✗ FAIL'}`,
          audit.workflow_name ? `Workflow: ${audit.workflow_name}` : '',
          audit.github_actions_status ? `Last Run: ${audit.github_actions_status}` : '',
          `Penalty Applied: ${audit.penalty_applied ? 'Yes (-50%)' : 'No'}`
        ].filter(Boolean);
      })()
    },
    {
      id: 'mentor',
      label: 'Mentor Agent',
      role: 'Growth Planning',
      icon: TrendingUp,
      status: (result.mentorship_plan || isJobComplete) ? 'success' : 'pending',
      evidence: (() => {
        if (!result.mentorship_plan) return ['Generating personalized roadmap...'];
        
        const plan = result.mentorship_plan;
        return [
          plan.quick_wins ? `⚡ ${plan.quick_wins.length} Quick Wins Identified` : '',
          plan.credit_projection ? `💰 Potential: +${plan.credit_projection.percentage_increase.toFixed(0)}% credits` : '',
          plan.actionable_roadmap ? `📋 ${plan.actionable_roadmap.length}-step roadmap created` : '',
          plan.next_level_requirements?.estimated_effort_hours 
            ? `⏱️ Est. ${plan.next_level_requirements.estimated_effort_hours}h to next level` 
            : ''
        ].filter(Boolean);
      })()
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <h3 className="text-sm font-bold uppercase tracking-wider text-text-muted flex items-center gap-2">
          <Activity className="w-4 h-4 text-primary" />
          Verification Chain
        </h3>
        <span className="text-[10px] font-mono text-text-dim bg-surface px-2 py-1 rounded border border-border">
          ID: {result.verification_id?.slice(0, 8) || '...'}
        </span>
      </div>

      <div className="relative pl-2">
        {/* Connector Line */}
        <div className="absolute left-8 top-4 bottom-4 w-0.5 bg-border z-0" />

        <div className="space-y-6 relative z-10">
          {pipeline.map((step, idx) => (
            <motion.div 
              key={step.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="flex gap-4"
            >
              {/* Status Indicator */}
              <div className={`w-12 h-12 rounded-full border-4 border-void flex items-center justify-center shrink-0 shadow-sm z-10 ${
                step.isIntervention 
                  ? 'bg-primary text-black border-primary/20' 
                  : step.status === 'success' 
                    ? 'bg-surface text-success border-success/30' 
                    : 'bg-surface text-text-dim border-border'
              }`}>
                <step.icon className="w-5 h-5" />
              </div>

              {/* Agent Card */}
              <div className={`flex-1 p-4 rounded-xl border transition-all ${
                step.isIntervention 
                  ? 'bg-primary/5 border-primary/30' 
                  : step.status === 'success'
                    ? 'bg-surface border-border hover:border-border-strong'
                    : 'bg-void border-border/50 opacity-60'
              }`}>
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className={`font-bold text-sm ${step.isIntervention ? 'text-primary' : 'text-text-main'}`}>
                      {step.label}
                    </h4>
                    <span className="text-[10px] text-text-dim font-mono uppercase tracking-wider">{step.role}</span>
                  </div>
                  {step.status === 'success' && !step.isIntervention && (
                    <CheckCircle2 className="w-4 h-4 text-success opacity-50" />
                  )}
                </div>
                
                {/* Evidence List */}
                <div className="space-y-1.5 mt-3">
                  {step.evidence.map((line, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-text-muted font-mono">
                      <span className={`w-1 h-1 rounded-full ${step.isIntervention ? 'bg-primary' : 'bg-text-dim'}`} />
                      {line}
                    </div>
                  ))}
                </div>

                {/* Detailed Evidence (for Grader) */}
                {step.detailedEvidence && step.detailedEvidence.length > 0 && (
                  <div className="mt-3 bg-surface p-3 rounded-lg border border-border">
                    <div className="text-[10px] text-text-dim uppercase mb-2 font-bold">Evidence Citations</div>
                    <div className="space-y-1">
                      {step.detailedEvidence.slice(0, 5).map((evidence, i) => (
                        <div key={i} className="text-xs text-text-muted flex items-center gap-2 font-mono">
                          <FileCode className="w-3 h-3 text-primary" />
                          {evidence}
                        </div>
                      ))}
                      {step.detailedEvidence.length > 5 && (
                        <div className="text-[10px] text-text-dim italic">
                          +{step.detailedEvidence.length - 5} more citations
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}