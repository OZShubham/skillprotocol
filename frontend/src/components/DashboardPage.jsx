import { useState, useMemo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Award, TrendingUp, Code, Plus, ExternalLink, 
  Activity, Shield, GitCommit, Layers, Zap, CheckCircle2,
  Eye, Calendar, ChevronRight, Terminal, Copy
} from 'lucide-react'
import SpotlightCard from './ui/SpotlightCard'
import SkillGraph from './ui/SkillGraph'
import OpikInsights from './OpikInsights'
import { api } from '../services/api' 

export default function DashboardPage({ onNewAnalysis, userStats, analysisHistory, onViewCertificate }) {
  const [selectedAgent, setSelectedAgent] = useState(null)
  
  // --- AUTHORITY DATA CALCULATION ---
  // Fixes "wrong info" by calculating metrics directly from the source of truth (history)
  const localStats = useMemo(() => {
    if (!analysisHistory || analysisHistory.length === 0) {
      return {
        ...userStats,
        totalCredits: 0,
        verifiedRepos: 0,
        avgSfia: 0,
        rank: 'UNRANKED'
      }
    }

    // Deduplicate history by Repo URL taking the highest credit run per repo
    const uniqueRepoCredits = {};
    analysisHistory.forEach(item => {
      const url = item.repo_url;
      const credits = item.final_credits || 0;
      if (!uniqueRepoCredits[url] || credits > uniqueRepoCredits[url]) {
        uniqueRepoCredits[url] = credits;
      }
    });

    const total = Object.values(uniqueRepoCredits).reduce((a, b) => a + b, 0);
    const verifiedCount = Object.keys(uniqueRepoCredits).length;
    
    // Calculate actual average SFIA level from all successful runs
    const validLevels = analysisHistory
      .map(item => item.sfia_level)
      .filter(lvl => lvl && lvl > 0);
      
    const avgLevel = validLevels.length > 0 
      ? validLevels.reduce((a, b) => a + b, 0) / validLevels.length 
      : 0;

    return {
      ...userStats,
      totalCredits: total,
      verifiedRepos: verifiedCount,
      avgSfia: avgLevel.toFixed(1),
      username: userStats.username || 'Developer'
    };
  }, [analysisHistory, userStats]);

  const getInitials = (name) => {
    if (!name || name === 'Guest') return 'GU'
    return name.substring(0, 2).toUpperCase()
  }

  const getSafeDate = (dateString) => {
    try {
      if (!dateString) return new Date(); 
      const date = new Date(dateString);
      return isNaN(date.getTime()) ? new Date() : date;
    } catch (e) {
      return new Date();
    }
  }

  const growthPercentage = useMemo(() => {
    if (!analysisHistory || analysisHistory.length < 2) return 0
    const recent = analysisHistory.slice(0, 5).reduce((sum, item) => sum + (item.final_credits || 0), 0)
    const older = analysisHistory.slice(5, 10).reduce((sum, item) => sum + (item.final_credits || 0), 0)
    if (older === 0) return recent > 0 ? 100 : 0
    return Math.round(((recent - older) / older) * 100)
  }, [analysisHistory])

  const heatmapData = useMemo(() => {
    const last30Days = Array.from({ length: 30 }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - (29 - i))
      return date.toISOString().split('T')[0]
    })

    return last30Days.map(date => {
      const count = analysisHistory.filter(item => {
        const rawDate = item.created_at || item.timestamp || item.started_at;
        if (!rawDate) return false;
        return getSafeDate(rawDate).toISOString().split('T')[0] === date;
      }).length

      let intensity = 'bg-surface'
      if (count >= 3) intensity = 'bg-primary'
      else if (count === 2) intensity = 'bg-primary/50'
      else if (count === 1) intensity = 'bg-primary/20'

      return { date, count, intensity }
    })
  }, [analysisHistory])

  const recentActivity = useMemo(() => {
    return (analysisHistory || []).slice(0, 5).map(item => {
      const repoName = item.repo_url?.split('/').slice(-2).join('/') || 'Unknown Repo'
      const rawDate = item.created_at || item.timestamp || item.started_at;
      
      return {
        id: item.id || item.job_id || item.verification_id,
        action: item.final_credits > 0 ? 'Minted Credits' : 'Analysis Failed',
        repo: repoName,
        amount: item.final_credits > 0 ? `+${item.final_credits.toFixed(1)}` : '0.0',
        time: getTimeAgo(rawDate),
        status: item.final_credits > 0 ? 'success' : 'failed',
        result: item
      }
    })
  }, [analysisHistory])

  // Identifies the active job for the Live Trace stream
  const activeJobId = analysisHistory[0]?.id || analysisHistory[0]?.job_id;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 pb-20">
      
      {/* HEADER SECTION */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-10 border-b border-border pb-8">
        <div className="flex items-center gap-5">
          <div className="w-16 h-16 bg-panel border border-border rounded-full flex items-center justify-center relative overflow-hidden group">
            <span className="font-mono text-2xl font-bold text-white">{getInitials(localStats.username)}</span>
            <div className="absolute inset-0 rounded-full border-2 border-primary/30 animate-pulse" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
              {localStats.username}
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-primary/10 text-primary border border-primary/20 uppercase tracking-wider font-bold">
                {localStats.rank || 'CITIZEN'}
              </span>
            </h1>
            <p className="text-text-muted text-sm font-mono mt-1 flex items-center gap-3">
              <span>{analysisHistory.length} repositories analyzed</span>
              <span className="text-border">|</span>
              <span className="text-success flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
                Live Node Active
              </span>
            </p>
          </div>
        </div>

        <div className="flex gap-3">
          <button 
            onClick={() => {
                navigator.clipboard.writeText(window.location.href);
                alert("Profile URL copied!");
            }}
            className="px-4 py-2 bg-panel hover:bg-surface border border-border text-text-muted hover:text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2 group"
          >
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

      {/* METRICS GRID */}
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
          <div className="text-3xl font-bold text-white font-mono-nums">{(localStats.totalCredits || 0).toFixed(1)}</div>
          <div className="text-xs text-text-muted mt-1 uppercase tracking-wider font-mono">Total Credits</div>
        </SpotlightCard>

        <SpotlightCard className="p-6 group">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2 bg-surface rounded-lg border border-border group-hover:border-white/50 transition-colors">
                <GitCommit className="w-5 h-5 text-white" />
            </div>
          </div>
          <div className="text-3xl font-bold text-white font-mono-nums">{localStats.verifiedRepos || 0}</div>
          <div className="text-xs text-text-muted mt-1 uppercase tracking-wider font-mono">Verified Repos</div>
        </SpotlightCard>

        <SpotlightCard className="p-6 group">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2 bg-surface rounded-lg border border-border group-hover:border-purple-400/50 transition-colors">
                <Shield className="w-5 h-5 text-purple-400" />
            </div>
          </div>
          <div className="text-3xl font-bold text-white font-mono-nums">
            {localStats.avgSfia > 0 ? localStats.avgSfia : 'N/A'}
          </div>
          <div className="text-xs text-text-muted mt-1 uppercase tracking-wider font-mono">Avg SFIA Level</div>
        </SpotlightCard>

        <SpotlightCard className="p-6 group">
          <div className="flex justify-between items-start mb-4">
            <div className="p-2 bg-surface rounded-lg border border-border group-hover:border-success/50 transition-colors">
                <TrendingUp className="w-5 h-5 text-success" />
            </div>
          </div>
          <div className="text-3xl font-bold text-white font-mono-nums">{localStats.rank || 'Beginner'}</div>
          <div className="text-xs text-text-muted mt-1 uppercase tracking-wider font-mono">Global Rank</div>
        </SpotlightCard>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        
        {/* LEFT COLUMN: ACTIVITY & HISTORY */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Activity Heatmap */}
          <div className="bg-panel border border-border rounded-xl p-6 relative overflow-hidden">
            <h3 className="text-sm font-mono text-text-muted uppercase tracking-wider mb-6 flex items-center gap-2">
              <Activity className="w-4 h-4 text-text-dim" />
              Developer Cadence (Last 30 Days)
            </h3>
            
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

          {/* Analysis History */}
          <div className="bg-panel border border-border rounded-xl overflow-hidden">
            <div className="border-b border-border p-4 flex items-center justify-between bg-surface/30">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-text-muted" />
                Audit Trail
              </h3>
            </div>
            <div className="divide-y divide-border">
              {recentActivity.length > 0 ? (
                recentActivity.map((item) => (
                  <div 
                    key={item.id} 
                    onClick={() => item.status === 'success' && onViewCertificate(item.result)}
                    className="p-4 flex items-center justify-between hover:bg-surface/50 transition-colors group cursor-pointer"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className={`w-2 h-2 rounded-full ${item.status === 'success' ? 'bg-success shadow-[0_0_8px_rgba(16,185,129,0.4)]' : 'bg-error shadow-[0_0_8px_rgba(239,68,68,0.4)]'}`} />
                      <div className="flex-1">
                        <div className="text-sm text-white font-medium group-hover:text-primary transition-colors">{item.action}</div>
                        <div className="text-xs text-text-muted font-mono">{item.repo}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className={`text-sm font-bold font-mono ${item.status === 'success' ? 'text-success' : 'text-error'}`}>
                          {item.amount}
                        </div>
                        <div className="text-xs text-text-dim">{item.time}</div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-text-dim group-hover:text-primary transition-colors" />
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-12 text-center">
                  <Code className="w-12 h-12 text-text-dim mx-auto mb-3" />
                  <p className="text-text-muted text-sm">No verification data available.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: INSIGHTS & LIVE LOGS */}
        <div className="space-y-6">
            
           {/* Skill Topology */}
           <div className="bg-panel border border-border rounded-xl p-1 overflow-hidden group">
             <div className="p-4 border-b border-border/50 flex justify-between items-center bg-void">
                <h3 className="text-xs font-mono text-text-muted uppercase tracking-widest">Topology_Map_v2</h3>
                <Activity className="w-3 h-3 text-primary animate-pulse" />
             </div>
             <SkillGraph />
          </div>

          {/* Opik Diagnostic Widget */}
          {analysisHistory.length > 0 && (
            <div className="bg-panel border border-border rounded-xl p-6">
              <OpikInsights 
                result={analysisHistory[0]} 
                onAgentSelect={setSelectedAgent} 
              />
            </div>
          )}

          

        </div>
      </div>
    </div>
  )
}

// --- SUBCOMPONENT: LIVE SSE TRACE ---
function AgentTransparentLog({ jobId }) {
  const [liveLogs, setLiveLogs] = useState([]);

  useEffect(() => {
    if (!jobId) return;

    // Reset logs on job change
    setLiveLogs([]);

    // SSE Connection to the backend stream
    const eventSource = new EventSource(`http://localhost:8000/api/stream/${jobId}`);

    eventSource.onmessage = (event) => {
      try {
        const newLog = JSON.parse(event.data);
        setLiveLogs((prev) => [newLog, ...prev].slice(0, 50));
      } catch (err) {
        console.error("Failed to parse SSE event:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.warn("SSE connection closed or failed.");
      eventSource.close();
    };

    return () => eventSource.close();
  }, [jobId]);

  
}

// --- UTILS ---
function getTimeAgo(timestamp) {
  if (!timestamp) return '...'
  const past = new Date(timestamp)
  if (isNaN(past.getTime())) return 'Recently'
  const now = new Date()
  const diffMs = now - past
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins/60)}h ago`
  return past.toLocaleDateString()
}