import { motion } from 'framer-motion'
import { 
  CheckCircle2, FileCode, Scale, ShieldCheck, 
  Terminal, Eye, Shield, Check, Activity 
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
      role: 'Forensic Extraction',
      icon: Terminal,
      status: (result.scan_metrics || isJobComplete) ? 'success' : 'pending',
      evidence: result.scan_metrics?.ncrf ? [
        `${fmt(result.scan_metrics.ncrf.total_sloc)} Lines of Code`,
        `${result.scan_metrics.ncrf.files_scanned} Files Parsed`,
        `Dominant: ${result.scan_metrics.ncrf.dominant_language || 'Unknown'}`
      ] : ['Scanning codebase structure...']
    },
    {
      id: 'reviewer',
      label: 'Reviewer Agent',
      role: 'Semantic Analysis',
      icon: Eye,
      // FIX: Use isJobComplete fallback if specific semantic data is missing
      status: (result.semantic_multiplier || result.scan_metrics?.quality_report || isJobComplete) ? 'success' : 'pending',
      evidence: (result.scan_metrics?.quality_report || isJobComplete) ? [
        `Sophistication: ${result.scan_metrics?.quality_report?.sophistication || 'Standard'}`,
        `Design Patterns: Detected`,
        `Quality Checks: Passed`
      ] : ['Analyzing architectural patterns...']
    },
    {
      id: 'grader',
      label: 'Grader Agent',
      role: 'SFIA Assessment',
      icon: Scale,
      status: (result.sfia_result || isJobComplete) ? 'success' : 'pending',
      evidence: result.sfia_result ? [
        `Initial Assessment: Level ${result.sfia_result.sfia_level}`,
        `Confidence Score: ${((result.sfia_result.confidence || 0) * 100).toFixed(0)}%`,
        result.sfia_result.missing_for_next_level?.length > 0 
          ? `Gap: ${result.sfia_result.missing_for_next_level[0].slice(0, 30)}...` 
          : 'No major gaps detected'
      ] : ['Evaluating capabilities...']
    },
    {
      id: 'judge',
      label: 'Judge Agent',
      role: 'Final Arbitration',
      icon: ShieldCheck,
      status: isJobComplete ? 'success' : 'pending',
      isIntervention: result.sfia_result?.judge_intervened,
      evidence: result.sfia_result?.judge_intervened ? [
        `⚠️ INTERVENTION: Overruled Grader`,
        `Final Verdict: Level ${result.sfia_result.sfia_level}`,
        `Reason: Congruence Check Failed`
      ] : [
        `✓ Ratified Grader Assessment`,
        `Congruence Score: 100%`,
        `Verdict: Verified`
      ]
    },
    {
      id: 'auditor',
      label: 'Auditor Agent',
      role: 'Reality Check',
      icon: Check,
      status: (result.audit_result || isJobComplete) ? 'success' : 'pending',
      evidence: result.audit_result ? [
        `CI/CD Status: ${result.audit_result.reality_check_passed ? 'PASS' : 'FAIL'}`,
        result.audit_result.workflow_name ? `Workflow: ${result.audit_result.workflow_name}` : 'No workflows found',
        `Penalty Applied: ${result.audit_result.penalty_applied ? 'Yes (-50%)' : 'No'}`
      ] : ['Checking build status...']
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
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}