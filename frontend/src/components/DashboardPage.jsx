import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { 
  Award, TrendingUp, Code, Plus, ExternalLink, 
  Activity, Shield, GitCommit, Layers, Zap, CheckCircle2,
  Eye, Calendar
} from 'lucide-react'
import SpotlightCard from './ui/SpotlightCard'
import SkillGraph from './ui/SkillGraph'
import OpikInsights from './OpikInsights'

export default function DashboardPage({ onNewAnalysis, userStats, analysisHistory, onViewCertificate }) {
  
  const getInitials = (name) => {
    if (!name || name === 'Guest') return 'GU'
    return name.substring(0, 2).toUpperCase()
  }

  // --- SAFELY PARSE DATES ---
  // This helper function prevents the "Invalid time value" crash
  const getSafeDate = (dateString) => {
    try {
      if (!dateString) return new Date(); // Fallback to now
      const date = new Date(dateString);
      // Check if date is valid
      if (isNaN(date.getTime())) return new Date(); 
      return date;
    } catch (e) {
      return new Date();
    }
  }

  // Calculate growth percentage
  const growthPercentage = useMemo(() => {
    if (analysisHistory.length < 2) return 0
    
    const recent = analysisHistory.slice(0, 5).reduce((sum, item) => sum + (item.final_credits || 0), 0)
    const older = analysisHistory.slice(5, 10).reduce((sum, item) => sum + (item.final_credits || 0), 0)
    
    if (older === 0) return 100
    return Math.round(((recent - older) / older) * 100)
  }, [analysisHistory])

  // Generate activity heatmap data
  const heatmapData = useMemo(() => {
    const last30Days = Array.from({ length: 30 }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - (29 - i))
      return date.toISOString().split('T')[0]
    })

    return last30Days.map(date => {
      const count = analysisHistory.filter(item => {
        // FIX: Handle both 'timestamp' (local) and 'created_at' (db)
        const rawDate = item.created_at || item.timestamp;
        const itemDate = getSafeDate(rawDate).toISOString().split('T')[0];
        return itemDate === date;
      }).length

      let intensity = 'bg-surface'
      if (count >= 3) intensity = 'bg-primary'
      else if (count === 2) intensity = 'bg-primary/50'
      else if (count === 1) intensity = 'bg-primary/20'

      return { date, count, intensity }
    })
  }, [analysisHistory])

  // Recent activity for transaction log
  const recentActivity = useMemo(() => {
    return analysisHistory.slice(0, 5).map(item => {
      const repoName = item.repo_url?.split('/').slice(-2).join('/') || 'Unknown Repo'
      
      // FIX: Use safe date extraction
      const rawDate = item.created_at || item.timestamp;
      const time = getTimeAgo(rawDate);
      
      return {
        id: item.id || item.verification_id,
        action: item.final_credits > 0 ? 'Minted Credits' : 'Analysis Failed',
        repo: repoName,
        amount: item.final_credits > 0 ? `+${item.final_credits}` : 'Err',
        time,
        status: item.final_credits > 0 ? 'success' : 'failed',
        result: item
      }
    })
  }, [analysisHistory])

  // Get user initials
  const userInitials = getInitials(userStats.username)

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      
      {/* Header Profile Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-10 border-b border-border pb-8">
        <div className="flex items-center gap-5">
          <div className="w-16 h-16 bg-panel border border-border rounded-full flex items-center justify-center relative overflow-hidden group">
            <span className="font-mono text-2xl font-bold text-white">{userInitials}</span>
            {/* Online Ring Animation */}
            <div className="absolute inset-0 rounded-full border-2 border-primary/30 animate-pulse" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
              {userStats.username}
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-primary/10 text-primary border border-primary/20 uppercase tracking-wider font-bold">
                {userStats.rank}
              </span>
            </h1>
            <p className="text-text-muted text-sm font-mono mt-1 flex items-center gap-3">
              <span>{analysisHistory.length} repositories analyzed</span>
              <span className="text-border">|</span>
              <span className="text-success flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
                Active
              </span>
            </p>
          </div>
        </div>

        <div className="flex gap-3">
          <button className="px-4 py-2 bg-panel hover:bg-surface border border-border text-text-muted hover:text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2 group">
            <ExternalLink className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" /> 
            Share Profile
          </button>
          <button
            onClick={onNewAnalysis}
            className="px-5 py-2 bg-primary hover:bg-yellow-500 text-black font-bold rounded-lg text-sm transition-all hover:shadow-[0_0_20px_rgba(245,158,11,0.3)] flex items-center gap-2"
          >
            <Plus className="w-4 h-4" /> New Analysis
          </button>
        </div>
      </div>

      {/* 1. Advanced Metrics Grid (using SpotlightCard) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <SpotlightCard className="p-6 group">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2 bg-surface rounded-lg border border-border group-hover:border-primary/50 transition-colors">
                <Award className="w-5 h-5 text-primary" />
            </div>
            {growthPercentage > 0 && (
              <span className="text-[10px] font-mono text-success bg-success/10 px-1.5 py-0.5 rounded border border-success/20">
                +{growthPercentage}%
              </span>
            )}
          </div>
          <div className="text-3xl font-bold text-white font-mono-nums">{userStats.totalCredits}</div>
          <div className="text-xs text-text-muted mt-1 uppercase tracking-wider font-mono">Total Credits</div>
        </SpotlightCard>

        <SpotlightCard className="p-6 group">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2 bg-surface rounded-lg border border-border group-hover:border-white/50 transition-colors">
                <GitCommit className="w-5 h-5 text-white" />
            </div>
          </div>
          <div className="text-3xl font-bold text-white font-mono-nums">{userStats.verifiedRepos}</div>
          <div className="text-xs text-text-muted mt-1 uppercase tracking-wider font-mono">Verified Repos</div>
        </SpotlightCard>

        <SpotlightCard className="p-6 group">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2 bg-surface rounded-lg border border-border group-hover:border-purple-400/50 transition-colors">
                <Shield className="w-5 h-5 text-purple-400" />
            </div>
          </div>
          <div className="text-3xl font-bold text-white font-mono-nums">
            {userStats.avgSfia > 0 ? userStats.avgSfia.toFixed(1) : 'N/A'}
          </div>
          <div className="text-xs text-text-muted mt-1 uppercase tracking-wider font-mono">Avg SFIA Level</div>
        </SpotlightCard>

        <SpotlightCard className="p-6 group">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2 bg-surface rounded-lg border border-border group-hover:border-success/50 transition-colors">
                <TrendingUp className="w-5 h-5 text-success" />
            </div>
          </div>
          <div className="text-3xl font-bold text-white font-mono-nums">{userStats.rank}</div>
          <div className="text-xs text-text-muted mt-1 uppercase tracking-wider font-mono">Global Rank</div>
        </SpotlightCard>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        
        {/* Main Feed Section */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* 2. Activity Heatmap */}
          <div className="bg-panel border border-border rounded-xl p-6 relative overflow-hidden">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-sm font-mono text-text-muted uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-text-dim" />
                Verification Activity (Last 30 Days)
              </h3>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-sm bg-surface" />
                <span className="text-xs text-text-dim">Low</span>
                <div className="w-2 h-2 rounded-sm bg-primary" />
                <span className="text-xs text-text-dim">High</span>
              </div>
            </div>
            
            {/* Render Heatmap Grid */}
            <div className="flex gap-1 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
              {heatmapData.map((day, index) => (
                <div key={index} className="flex flex-col gap-1 min-w-[12px]">
                  {Array.from({ length: 7 }).map((_, row) => (
                    <div 
                      key={row} 
                      className={`w-3 h-3 rounded-sm ${day.intensity} hover:border hover:border-white/50 transition-all duration-300 cursor-pointer`}
                      title={`${day.date}: ${day.count} verifications`}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* 3. Transaction Log */}
          <div className="bg-panel border border-border rounded-xl overflow-hidden">
            <div className="border-b border-border p-4 flex items-center justify-between bg-surface/30">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-text-muted" />
                Analysis History
              </h3>
              <span className="text-[10px] bg-surface text-text-dim px-2 py-1 rounded font-mono">
                {analysisHistory.length} TOTAL
              </span>
            </div>
            <div className="divide-y divide-border">
              {recentActivity.length > 0 ? (
                recentActivity.map((item) => (
                  <div key={item.id} className="p-4 flex items-center justify-between hover:bg-surface/50 transition-colors group cursor-pointer">
                    <div className="flex items-center gap-4 flex-1">
                      <div className={`w-2 h-2 rounded-full ${item.status === 'success' ? 'bg-success shadow-[0_0_8px_rgba(16,185,129,0.4)]' : 'bg-error shadow-[0_0_8px_rgba(239,68,68,0.4)]'}`} />
                      <div className="flex-1">
                        <div className="text-sm text-white font-medium group-hover:text-primary transition-colors">{item.action}</div>
                        <div className="text-xs text-text-muted font-mono">{item.repo}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className={`text-sm font-bold font-mono ${item.amount.includes('+') ? 'text-success' : 'text-error'}`}>
                          {item.amount}
                        </div>
                        <div className="text-xs text-text-dim">{item.time}</div>
                      </div>
                      {item.status === 'success' && (
                        <button 
                          onClick={() => onViewCertificate(item.result)}
                          className="p-2 bg-surface hover:bg-border rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                        >
                          <Eye className="w-4 h-4 text-primary" />
                        </button>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center">
                  <Code className="w-12 h-12 text-text-dim mx-auto mb-3" />
                  <p className="text-text-muted text-sm">No analysis history yet</p>
                  <button 
                    onClick={onNewAnalysis}
                    className="mt-4 text-primary hover:text-yellow-400 text-sm font-medium"
                  >
                    Start your first verification →
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="space-y-8">
           {/* 🆕 Opik Quality Dashboard */}
            {analysisHistory.length > 0 && (
              <div className="bg-panel border border-border rounded-xl p-6">
                <OpikInsights result={analysisHistory[0]} />
              </div>
            )}
          
          {/* 4. Skill Topology Graph */}
          <div className="bg-panel border border-border rounded-xl p-1 overflow-hidden group">
             <div className="p-4 border-b border-border/50 flex justify-between items-center">
                <h3 className="text-sm font-mono text-text-muted uppercase tracking-wider">Skill Topology</h3>
                <Activity className="w-3 h-3 text-primary animate-pulse" />
             </div>
             <SkillGraph />
          </div>

          {/* System Status */}
          <div className="bg-void border border-dashed border-border rounded-xl p-6 relative">
            <div className="absolute top-0 right-0 p-2">
                <div className="w-1.5 h-1.5 bg-success rounded-full animate-ping" />
            </div>
            <div className="flex items-center gap-3 mb-4">
              <Zap className="w-5 h-5 text-yellow-500" />
              <h3 className="text-sm font-bold text-white">Opik Agent Status</h3>
            </div>
            <div className="space-y-3 text-xs font-mono text-text-muted">
              {['Validator', 'Scanner', 'Grader', 'Auditor'].map(agent => (
                <div key={agent} className="flex justify-between items-center">
                  <span>{agent.toUpperCase()}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-success">ONLINE</span>
                    <CheckCircle2 className="w-3 h-3 text-success" />
                  </div>
                </div>
              ))}
              <div className="flex justify-between pt-3 border-t border-border mt-2 text-text-dim">
                <span>SYSTEM LATENCY</span>
                <span className="text-primary">42ms</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

// Helper function to calculate time ago
function getTimeAgo(timestamp) {
  if (!timestamp) return 'Unknown'
  
  // FIX: Use Safe Date parsing here too
  let past;
  try {
      past = new Date(timestamp);
      if(isNaN(past.getTime())) throw new Error("Invalid");
  } catch (e) {
      return "Unknown";
  }

  const now = new Date()
  const diffMs = now - past
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  
  return past.toLocaleDateString()
}