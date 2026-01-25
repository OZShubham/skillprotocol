import { ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip } from 'recharts';
import { motion } from 'framer-motion';

export default function SkillRadar({ analysisHistory }) {
  // Empty State
  if (!analysisHistory || analysisHistory.length === 0) {
    return (
      <div className="w-full h-[320px] flex flex-col items-center justify-center bg-panel border border-border rounded-xl text-text-muted">
        <div className="w-12 h-12 rounded-full bg-surface border border-border flex items-center justify-center mb-3">
          <svg className="w-6 h-6 opacity-20" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zm0 9l2.5-1.25L12 8.5l-2.5 1.25L12 11zm0 2.5l-5-2.5-5 2.5L12 22l10-8.5-5-2.5-5 2.5z"/></svg>
        </div>
        <span className="text-xs font-mono uppercase tracking-wider opacity-50">No Data Available</span>
      </div>
    );
  }

  // 1. Aggregate Data
  const languageStats = {};
  let maxSloc = 0;

  analysisHistory.forEach(run => {
    const stats = run.scan_metrics?.ncrf?.language_stats || {};
    Object.entries(stats).forEach(([lang, data]) => {
      const sloc = typeof data === 'number' ? data : (data.sloc || 0);
      languageStats[lang] = (languageStats[lang] || 0) + sloc;
    });
  });

  // 2. Format & Normalize
  let data = Object.entries(languageStats)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([lang, sloc]) => {
      if (sloc > maxSloc) maxSloc = sloc;
      return { subject: lang, A: sloc, fullMark: 100 };
    });

  // Normalize to 0-100 scale (Standard for Radar charts)
  data = data.map(d => ({
    ...d,
    A: maxSloc > 0 ? (d.A / maxSloc) * 100 : 0
  }));

  // Pad data if needed (Radar needs at least 3 points to form a shape)
  while (data.length < 3 && data.length > 0) {
    data.push({ subject: '', A: 0, fullMark: 100 });
  }

  return (
    <div className="w-full h-[320px] bg-panel relative overflow-hidden rounded-xl border border-border">
      <div className="absolute top-4 left-4 text-[10px] font-mono text-text-muted z-10 flex items-center gap-2 uppercase tracking-wider font-bold">
        <span className="w-1.5 h-1.5 bg-primary rounded-full" />
        Expertise Profile
      </div>

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="w-full h-full pt-4"
      >
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="55%" outerRadius="65%" data={data}>
            <defs>
              <linearGradient id="radarFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.5}/>
                <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            
            {/* The Spider Web Grid */}
            <PolarGrid stroke="var(--color-border)" gridType="polygon" />
            
            {/* Labels */}
            <PolarAngleAxis 
              dataKey="subject" 
              tick={{ fill: 'var(--color-text-dim)', fontSize: 11, fontWeight: 600, fontFamily: 'var(--font-mono)' }} 
            />
            
            {/* Hide Radius Axis numbers */}
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
            
            <Radar
              name="Proficiency"
              dataKey="A"
              stroke="var(--color-primary)"
              strokeWidth={2}
              fill="url(#radarFill)"
              fillOpacity={1}
              isAnimationActive={true}
            />
            
            <Tooltip 
              cursor={false}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  // Reconstruct original value estimation
                  const val = payload[0].value;
                  const estimatedLines = Math.round((val / 100) * maxSloc);
                  return (
                    <div className="bg-surface border border-border px-3 py-2 rounded-lg shadow-xl text-xs">
                      <div className="text-text-muted mb-1 font-bold">{payload[0].payload.subject}</div>
                      <div className="text-primary font-mono">~{estimatedLines.toLocaleString()} LOC</div>
                    </div>
                  );
                }
                return null;
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
}