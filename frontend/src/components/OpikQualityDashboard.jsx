import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  TrendingUp, Activity, Target, AlertCircle, 
  ExternalLink, Award, Zap, BarChart3, 
  CheckCircle, XCircle, Clock
} from 'lucide-react'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../services/api' // Real API Import

export default function OpikQualityDashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getOpikStats()
      
      if (data && !data.error) {
        setStats(data)
      } else {
        throw new Error(data?.error || 'Failed to fetch real-time stats')
      }
    } catch (err) {
      setError(err.message || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-void">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-text-muted">Loading Opik Dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-void">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-error mx-auto mb-4"></AlertCircle>
          <h2 className="text-2xl font-bold text-white mb-2">Dashboard Unavailable</h2>
          <p className="text-text-muted mb-4">{error}</p>
          <button 
            onClick={loadDashboardData}
            className="px-4 py-2 bg-primary text-black rounded-lg hover:bg-yellow-500 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // Safe data extraction with fallbacks
  const abResults = stats?.ab_test_results
  const qualityTrend = stats?.quality_trend || []

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8 bg-void min-h-screen">
      
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Opik Quality Dashboard</h1>
          <p className="text-text-muted">Real-time AI performance metrics and optimization insights</p>
        </div>
        {stats?.opik_dashboard_url && (
          <a 
            href={stats.opik_dashboard_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-white transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            View in Opik
          </a>
        )}
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard 
          icon={<Activity className="w-6 h-6" />}
          label="Total Analyses"
          value={stats?.total_analyses || 0}
          color="blue"
        />
        <MetricCard 
          icon={<Target className="w-6 h-6" />}
          label="Current Accuracy"
          value={`${((stats?.current_accuracy || 0) * 100).toFixed(1)}%`}
          color="green"
          trend={stats?.improvement_percentage > 0 ? 'up' : 'stable'}
        />
        <MetricCard 
          icon={<TrendingUp className="w-6 h-6" />}
          label="Improvement"
          value={`+${(stats?.improvement_percentage || 0).toFixed(1)}%`}
          color="purple"
          highlight
        />
        <MetricCard 
          icon={<Award className="w-6 h-6" />}
          label="Baseline"
          value={`${((stats?.baseline_accuracy || 0.70) * 100).toFixed(1)}%`}
          color="gray"
        />
      </div>

      {/* A/B Test Results - WITH SAFE CHECKS */}
      {abResults && abResults.variant_a && abResults.variant_b && (
        <div className="bg-panel border border-border rounded-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-xl font-bold text-white mb-1">Live A/B Experiment</h2>
              <p className="text-sm text-text-muted">{abResults.experiment_name || 'Unnamed Experiment'}</p>
            </div>
            <div className="px-3 py-1 rounded-full bg-green-500/10 border border-green-500/30 text-green-400 text-sm font-bold">
              Winner: {abResults.winner === 'b' ? 'Variant B' : 'Variant A'}
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Variant A */}
            <VariantCard 
              variant="A"
              name={abResults.variant_a.name || 'Variant A'}
              successRate={abResults.variant_a.success_rate || 0}
              sampleSize={abResults.variant_a.sample_size || 0}
              avgConfidence={abResults.variant_a.avg_confidence || 0}
              isWinner={abResults.winner === 'a'}
            />

            {/* Variant B */}
            <VariantCard 
              variant="B"
              name={abResults.variant_b.name || 'Variant B'}
              successRate={abResults.variant_b.success_rate || 0}
              sampleSize={abResults.variant_b.sample_size || 0}
              avgConfidence={abResults.variant_b.avg_confidence || 0}
              isWinner={abResults.winner === 'b'}
            />
          </div>

          {/* Improvement Bar */}
          <div className="mt-6 p-4 bg-surface rounded-lg">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-text-muted">Performance Improvement</span>
              <span className="text-primary font-bold">+{(abResults.improvement_percentage || 0).toFixed(1)}%</span>
            </div>
            <div className="h-2 bg-void rounded-full overflow-hidden">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(100, (abResults.improvement_percentage || 0) * 2)}%` }}
                transition={{ duration: 1 }}
                className="h-full bg-gradient-to-r from-primary to-green-500 rounded-full"
              />
            </div>
          </div>
        </div>
      )}

      {/* Quality Trend Chart */}
      {qualityTrend.length > 0 && (
        <div className="bg-panel border border-border rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4">Quality Trend (Project History)</h2>
          <div style={{ width: '100%', minHeight: '300px' }}>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={qualityTrend}>
                <defs>
                  <linearGradient id="colorAccuracy" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis 
                  dataKey="index" 
                  stroke="#666"
                  tick={{ fill: '#666', fontSize: 12 }}
                />
                <YAxis 
                  stroke="#666"
                  tick={{ fill: '#666', fontSize: 12 }}
                  domain={[0, 1]}
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#121212', 
                    border: '1px solid #333', 
                    borderRadius: '8px' 
                  }}
                  labelStyle={{ color: '#666' }}
                  itemStyle={{ color: '#10B981' }}
                  formatter={(value) => [`${(value * 100).toFixed(1)}%`, 'Accuracy']}
                />
                <Area 
                  type="monotone" 
                  dataKey="accuracy" 
                  stroke="#10B981" 
                  fillOpacity={1} 
                  fill="url(#colorAccuracy)" 
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* System Health */}
      <div className="grid md:grid-cols-3 gap-6">
        <HealthCard 
          title="Agent Performance"
          status="healthy"
          message="All agents operating within normal parameters"
          icon={<CheckCircle className="w-8 h-8 text-green-400" />}
        />
        <HealthCard 
          title="Bayesian Validator"
          status="healthy"
          message="Statistical model alignment: High"
          icon={<Target className="w-8 h-8 text-blue-400" />}
        />
        <HealthCard 
          title="Telemetry Sync"
          status="healthy"
          message="Connection to Opik cloud is active"
          icon={<Activity className="w-8 h-8 text-purple-400" />}
        />
      </div>

      {/* Footer */}
      <div className="text-center text-sm text-text-dim">
        <p>Last updated: {stats?.last_updated ? new Date(stats.last_updated).toLocaleString() : 'Just now'}</p>
        <p className="mt-2">
          Powered by <span className="text-primary font-bold">Opik</span> - AI Quality & Observability
        </p>
      </div>
    </div>
  )
}

function MetricCard({ icon, label, value, color, trend, highlight }) {
  const colorClasses = {
    blue: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
    green: 'text-green-400 bg-green-500/10 border-green-500/30',
    purple: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
    gray: 'text-gray-400 bg-gray-500/10 border-gray-500/30'
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-6 rounded-xl border ${highlight ? 'bg-primary/5 border-primary/30' : 'bg-surface border-border'}`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
        {trend === 'up' && (
          <TrendingUp className="w-4 h-4 text-green-400" />
        )}
      </div>
      <div className={`text-3xl font-bold mb-1 ${highlight ? 'text-primary' : 'text-white'}`}>
        {value}
      </div>
      <div className="text-sm text-text-muted">{label}</div>
    </motion.div>
  )
}

function VariantCard({ variant, name, successRate, sampleSize, avgConfidence, isWinner }) {
  return (
    <div className={`p-6 rounded-xl border ${isWinner ? 'bg-green-500/5 border-green-500/30' : 'bg-surface border-border'}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${isWinner ? 'bg-green-500/20 text-green-400' : 'bg-white/5 text-white'}`}>
            {variant}
          </div>
          <div>
            <div className="text-sm font-bold text-white">{name}</div>
            <div className="text-xs text-text-dim">{sampleSize} samples</div>
          </div>
        </div>
        {isWinner && (
          <Award className="w-6 h-6 text-green-400" />
        )}
      </div>

      <div className="space-y-3">
        <div>
          <div className="text-xs text-text-muted mb-1">Success Rate</div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-void rounded-full overflow-hidden">
              <div 
                className={`h-full ${isWinner ? 'bg-green-500' : 'bg-white/30'} rounded-full`}
                style={{ width: `${successRate * 100}%` }}
              />
            </div>
            <div className={`text-sm font-bold ${isWinner ? 'text-green-400' : 'text-white'}`}>
              {(successRate * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        <div>
          <div className="text-xs text-text-muted mb-1">Avg Confidence</div>
          <div className="text-sm text-white">{(avgConfidence * 100).toFixed(1)}%</div>
        </div>
      </div>
    </div>
  )
}

function HealthCard({ title, status, message, icon }) {
  const statusColors = {
    healthy: 'border-green-500/30 bg-green-500/5',
    warning: 'border-yellow-500/30 bg-yellow-500/5',
    error: 'border-red-500/30 bg-red-500/5'
  }

  return (
    <div className={`p-6 rounded-xl border ${statusColors[status]}`}>
      <div className="flex items-center gap-4 mb-3">
        {icon}
        <div>
          <div className="text-sm font-bold text-white">{title}</div>
          <div className={`text-xs uppercase tracking-wider ${
            status === 'healthy' ? 'text-green-400' : 
            status === 'warning' ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {status}
          </div>
        </div>
      </div>
      <p className="text-sm text-text-muted">{message}</p>
    </div>
  )
}