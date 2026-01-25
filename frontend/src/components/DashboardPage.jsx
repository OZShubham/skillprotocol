import { useState, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Award, TrendingUp, Plus, ExternalLink, Activity, Shield, 
  GitCommit, Layers, ChevronRight, Code, Database 
} from 'lucide-react'
import SpotlightCard from './ui/SpotlightCard'
import SkillRadar from './ui/SkillRadar' 
import { api } from '../services/api' 

export default function DashboardPage({ onNewAnalysis, userStats, analysisHistory, onViewCertificate }) {
  
  const [recentFullDetails, setRecentFullDetails] = useState([]);
  const [loadingDetails, setLoadingDetails] = useState(false);

  useEffect(() => {
    const hydrateRecentRuns = async () => {
      if (!analysisHistory || analysisHistory.length === 0) return;
      
      setLoadingDetails(true);
      try {
        const recentItems = analysisHistory.slice(0, 10);
        const promises = recentItems.map(item => 
          api.getResult(item.id || item.job_id).catch(() => null)
        );
        const fullResults = await Promise.all(promises);
        setRecentFullDetails(fullResults.filter(r => r !== null));
      } catch (e) {
        console.error("Hydration error", e);
      } finally {
        setLoadingDetails(false);
      }
    };
    hydrateRecentRuns();
  }, [analysisHistory]);

  const localStats = useMemo(() => {
    if (!analysisHistory || analysisHistory.length === 0) {
      return { ...userStats, totalCredits: 0, verifiedRepos: 0, avgSfia: 0, rank: 'UNRANKED' }
    }

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

  const getSafeDate = (input) => {
    if (!input) return new Date();
    if (typeof input === 'string' && !input.endsWith('Z') && !input.includes('+')) {
      return new Date(input + 'Z');
    }
    const date = new Date(input);
    return isNaN(date.getTime()) ? new Date() : date;
  }

  const getTimeAgo = (ts) => {
    if (!ts) return '...';
    const date = getSafeDate(ts);
    const now = new Date();
    const diffMs = now - date; 
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const recentActivity = useMemo(() => {
    return (analysisHistory || []).slice(0, 5).map(item => {
      const repoName = item.repo_url?.split('/').slice(-2).join('/') || 'Unknown Repo';
      const rawDate = item.analyzed_at || item.created_at || item.started_at; 
      
      return {
        id: item.id || item.job_id,
        repo: repoName,
        amount: item.final_credits > 0 ? `+${item.final_credits.toFixed(1)}` : 'FAILED',
        time: getTimeAgo(rawDate),
        status: item.final_credits > 0 ? 'success' : 'failed',
        fullItem: item
      }
    })
  }, [analysisHistory])

  const heatmapData = useMemo(() => {
    const last30Days = Array.from({ length: 30 }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - (29 - i))
      return date.toISOString().split('T')[0]
    })

    return last30Days.map(date => {
      const count = analysisHistory.filter(item => {
        const rawDate = item.analyzed_at || item.created_at;
        if (!rawDate) return false;
        return getSafeDate(rawDate).toISOString().split('T')[0] === date;
      }).length

      let intensity = 'bg-surface border-border'
      if (count >= 3) intensity = 'bg-primary border-primary'
      else if (count === 2) intensity = 'bg-primary/60 border-primary/60'
      else if (count === 1) intensity = 'bg-primary/30 border-primary/30'

      return { date, count, intensity }
    })
  }, [analysisHistory])

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 pb-20">
      
      {/* 1. PROFILE HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8 border-b border-border pb-8">
        <div className="flex items-center gap-5">
          <div className="w-14 h-14 bg-panel border border-border rounded-full flex items-center justify-center relative overflow-hidden shadow-md">
            <span className="font-mono text-xl font-bold text-text-main">{getInitials(localStats.username)}</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-main tracking-tight flex items-center gap-3">
              {localStats.username}
            </h1>
            <p className="text-text-muted text-sm font-mono mt-1">
              Rank: <span className="text-primary">{localStats.rank}</span>
            </p>
          </div>
        </div>

        <div className="flex gap-3">
          <button 
            onClick={() => { navigator.clipboard.writeText(window.location.href); alert("Profile URL copied!"); }}
            className="px-4 py-2 bg-surface hover:bg-panel border border-border text-text-muted hover:text-text-main rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <ExternalLink className="w-4 h-4" /> Share
          </button>
          <button 
            onClick={onNewAnalysis}
            className="px-5 py-2 bg-primary hover:brightness-110 text-white font-bold rounded-lg text-sm transition-all shadow-md shadow-primary/20 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" /> Verify Repo
          </button>
        </div>
      </div>

      {/* 2. STATS OVERVIEW (Compact Grid) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Total Credits" value={(localStats.totalCredits || 0).toFixed(1)} />
        <MetricCard label="Verified Repos" value={localStats.verifiedRepos || 0} />
        <MetricCard label="Avg SFIA Level" value={localStats.avgSfia > 0 ? localStats.avgSfia : 'N/A'} />
        <MetricCard label="Global Rank" value={localStats.rank || 'N/A'} highlight />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Contribution Heatmap */}
          <div className="bg-panel border border-border rounded-xl p-6 shadow-sm">
            <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Activity (30 Days)
            </h3>
            <div className="flex gap-1 overflow-x-auto pb-2">
              {heatmapData.map((day, index) => (
                <div key={index} className="flex flex-col gap-1 min-w-[10px]">
                  {Array.from({ length: 7 }).map((_, row) => (
                    <div 
                      key={row} 
                      className={`w-2.5 h-2.5 rounded-[2px] border ${day.intensity} transition-all`}
                      title={`${day.date}: ${day.count} verifications`}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Recent Audits Table */}
          <div className="bg-panel border border-border rounded-xl overflow-hidden shadow-sm">
            <div className="border-b border-border p-4 bg-surface/30">
              <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4" />
                Audit Log
              </h3>
            </div>
            <div className="divide-y divide-border">
              {recentActivity.length > 0 ? (
                recentActivity.map((item) => (
                  <div 
                    key={item.id} 
                    onClick={() => item.status === 'success' && onViewCertificate(item.fullItem)}
                    className="p-4 flex items-center justify-between hover:bg-surface/50 transition-colors cursor-pointer group"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`p-2 rounded-lg ${item.status === 'success' ? 'bg-success/10 text-success' : 'bg-error/10 text-error'}`}>
                        {item.status === 'success' ? <Shield className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
                      </div>
                      <div>
                        <div className="text-sm font-medium text-text-main group-hover:text-primary transition-colors">{item.repo}</div>
                        <div className="text-xs text-text-muted flex items-center gap-2 mt-0.5">
                          <span>{item.id.slice(0, 8)}</span>
                          <span>•</span>
                          <span>{item.time}</span>
                        </div>
                      </div>
                    </div>
                    <div className={`text-sm font-mono font-bold ${item.status === 'success' ? 'text-success' : 'text-text-muted'}`}>
                      {item.amount}
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-text-muted text-sm">No activity yet.</div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN (1/3 width) */}
        <div className="space-y-6">
           
           {/* Skill Radar */}
           <SkillRadar analysisHistory={recentFullDetails} />

           {/* Tech Stack List - REMOVED h-full */}
           <div className="bg-panel border border-border rounded-xl p-6 shadow-sm">
             <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider mb-4 flex items-center gap-2">
               <Database className="w-4 h-4" />
               Tech Stack
             </h3>
             {loadingDetails ? (
               <div className="text-center text-xs text-text-muted py-4 animate-pulse">Analyzing...</div>
             ) : (
               <TopSkillsList details={recentFullDetails} />
             )}
           </div>

        </div>
      </div>
    </div>
  )
}

function MetricCard({ label, value, highlight }) {
  return (
    <div className={`p-5 rounded-xl border ${highlight ? 'bg-primary/5 border-primary/30' : 'bg-panel border-border'} shadow-sm`}>
      <div className="text-2xl font-bold font-mono-nums text-text-main mb-1">{value}</div>
      <div className="text-xs text-text-muted uppercase tracking-wider font-bold">{label}</div>
    </div>
  )
}

// Compacted List to avoid "going too much down"
function TopSkillsList({ details }) {
  if (!details || details.length === 0) return <div className="text-xs text-text-muted text-center py-4">No data available.</div>;

  const totals = {};
  let globalLines = 0;

  details.forEach(run => {
    const stats = run.scan_metrics?.ncrf?.language_stats || {};
    Object.entries(stats).forEach(([lang, data]) => {
      const sloc = typeof data === 'number' ? data : (data.sloc || 0);
      totals[lang] = (totals[lang] || 0) + sloc;
      globalLines += sloc;
    });
  });

  const topLangs = Object.entries(totals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  return (
    <div className="space-y-3"> {/* Tightened spacing from 4 to 3 */}
      {topLangs.map(([lang, lines]) => {
        const percent = Math.round((lines / globalLines) * 100);
        return (
          <div key={lang}>
            <div className="flex justify-between text-xs mb-1">
              {/* Smaller font size for tighter look */}
              <span className="font-medium text-text-main text-xs">{lang}</span>
              <span className="text-text-muted text-xs">{percent}%</span>
            </div>
            <div className="h-1.5 bg-surface rounded-full overflow-hidden">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${percent}%` }}
                transition={{ duration: 1 }}
                className="h-full bg-primary rounded-full opacity-80"
              />
            </div>
          </div>
        )
      })}
    </div>
  );
}