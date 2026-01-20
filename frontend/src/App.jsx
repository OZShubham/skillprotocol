import { Routes, Route, useNavigate, useLocation, useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { LayoutDashboard } from 'lucide-react'
import { api } from './services/api'
import logo from './assets/logo.png'

// Components
import LandingPage from './components/LandingPage'
import AnalysisPage from './components/AnalysisPage'
import CreditCertificate from './components/CreditCertificate'
import DashboardPage from './components/DashboardPage'

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()

  // --- DYNAMIC USER STATE ---
  // Default to 'Guest', but this changes dynamically based on the repo being analyzed
  const [currentUserId, setCurrentUserId] = useState(() => {
    return localStorage.getItem('last_user') || 'Guest'
  })

  const [analysisHistory, setAnalysisHistory] = useState([])
  
  const [userStats, setUserStats] = useState({
    totalCredits: 0,
    verifiedRepos: 0,
    avgSfia: 0,
    rank: 'N/A',
    username: 'Guest'
  })

  // --- EFFECT 1: CONTEXT SWITCHING ---
  // When currentUserId changes, we wipe the old history and load the new user's world.
  useEffect(() => {
    const loadUserData = async () => {
      // 1. Visual Reset (so you don't see old data for a split second)
      setAnalysisHistory([]) 
      
      // 2. Fetch new history from DB
      try {
        if (currentUserId !== 'Guest') {
          const history = await api.getUserHistory(currentUserId)
          setAnalysisHistory(history)
        }
      } catch (e) {
        console.error("Failed to load user history", e)
      }
    }

    loadUserData()
    
    // Persist context so refresh works
    localStorage.setItem('last_user', currentUserId)
    
  }, [currentUserId])

  // --- EFFECT 2: STATS CALCULATION ---
  // Runs whenever the history data updates (which happens after user switch)
  useEffect(() => {
    if (analysisHistory.length >= 0) {
      calculateUserStats()
    }
  }, [analysisHistory])

  const calculateUserStats = () => {
    // --- SMART DEDUPLICATION LOGIC ---
    // Group by Repo URL and take MAX credits to prevent double-counting
    const uniqueRepoCredits = {}
    
    analysisHistory.forEach(item => {
      const url = item.repo_url
      const credits = item.final_credits || 0
      
      // Keep only the highest score for this repo URL
      if (!uniqueRepoCredits[url] || credits > uniqueRepoCredits[url]) {
        uniqueRepoCredits[url] = credits
      }
    })

    // Sum the BEST runs
    const totalCredits = Object.values(uniqueRepoCredits).reduce((sum, credit) => sum + credit, 0)

    // Count unique valid repos (where credits > 0)
    const verifiedRepos = Object.keys(uniqueRepoCredits).filter(url => uniqueRepoCredits[url] > 0).length

    // Calculate Avg SFIA based on the BEST runs
    const bestRuns = Object.entries(uniqueRepoCredits)
      .map(([url, bestCredit]) => analysisHistory.find(item => item.repo_url === url && item.final_credits === bestCredit))
      .filter(Boolean)

    const avgSfia = verifiedRepos > 0 
      ? bestRuns.reduce((sum, item) => sum + (item.sfia_level || 0), 0) / verifiedRepos
      : 0

    // Rank Logic
    let rank = 'Beginner'
    if (totalCredits > 100) rank = 'Top 10%'
    else if (totalCredits > 50) rank = 'Top 25%'
    else if (totalCredits > 20) rank = 'Top 50%'

    // Update Stats State
    const newStats = {
      totalCredits: parseFloat(totalCredits.toFixed(2)),
      verifiedRepos,
      avgSfia: parseFloat(avgSfia.toFixed(1)),
      rank,
      username: currentUserId // Ensure stats reflect the current context
    }

    setUserStats(newStats)
  }

  // --- HANDLER: USER CONTEXT SWITCH ---
  // This is called by LandingPage when it detects a username in the URL
  const handleUserDetected = (username) => {
    if (username && username !== currentUserId) {
      console.log(`Context Switch: ${currentUserId} -> ${username}`)
      setCurrentUserId(username)
    }
  }

  // --- HANDLER: ANALYSIS COMPLETE ---
  const handleAnalysisComplete = async (jobId) => {
    try {
      const result = await api.getResult(jobId)
      
      if (result.final_credits !== undefined) {
        
        // Refresh full history for the CURRENT user
        const history = await api.getUserHistory(currentUserId)
        setAnalysisHistory(history)

        // Navigation Logic
        if (result.final_credits > 0) {
          navigate(`/certificate/${jobId}`)
        } else {
          // Check if it was a duplicate run
          const isDuplicate = history.some(h => h.repo_url === result.repo_url && h.final_credits > 0)
          
          if (isDuplicate) {
             alert('Repository already analyzed! Redirecting to previous certificate.')
             navigate('/dashboard')
          } else {
             alert('Analysis complete but no credits awarded. Please check repository quality.')
             navigate('/')
          }
        }
      }
    } catch (err) {
      console.error('Error fetching result:', err)
      alert('Error retrieving analysis result')
      navigate('/')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      {/* Navigation */}
      <nav className="relative z-50 border-b border-white/5 bg-[#050505]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            
            {/* Logo */}
            <button 
              onClick={() => navigate('/')}
              className="flex items-center gap-2 group focus:outline-none transition-opacity hover:opacity-80 -ml-6"
            >
              <img 
                src={logo} 
                alt="SkillProtocol" 
                className="h-16 w-auto object-contain" 
              />
            </button>

            {/* Actions Area */}
            <div className="flex items-center gap-6">
              
              {/* Dynamic Context Badge */}
              <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-gray-500">
                <div className={`w-1.5 h-1.5 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.5)] ${currentUserId !== 'Guest' ? 'bg-emerald-500' : 'bg-gray-500'}`} />
                <span>Viewing: <strong className="text-white">{currentUserId}</strong></span>
              </div>

              {/* Dashboard Button */}
              <button
                onClick={() => navigate('/dashboard')}
                className="group flex items-center gap-2 px-4 py-1.5 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20 transition-all active:scale-95"
              >
                <LayoutDashboard className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors" />
                <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">
                  Dashboard
                </span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Routes */}
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          
          <Route path="/" element={
            <motion.div
              key="landing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {/* Pass the detector function down */}
              <LandingPage 
                onStartAnalysis={(jobId) => navigate(`/analyze/${jobId}`)} 
                onUserDetected={handleUserDetected}
                currentUser={currentUserId}
              />
            </motion.div>
          } />

          <Route path="/analyze/:jobId" element={
            <motion.div
              key="analysis"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <AnalysisPageWrapper onComplete={handleAnalysisComplete} />
            </motion.div>
          } />

          <Route path="/certificate/:jobId" element={
            <motion.div
              key="certificate"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <CertificateLoader />
            </motion.div>
          } />

          <Route path="/dashboard" element={
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <DashboardPage 
                onNewAnalysis={() => navigate('/')} 
                userStats={userStats}
                analysisHistory={analysisHistory}
                onViewCertificate={(result) => navigate(`/certificate/${result.id || result.job_id}`)}
              />
            </motion.div>
          } />
          
        </Routes>
      </AnimatePresence>
    </div>
  )
}

// --- Route Wrappers ---

function AnalysisPageWrapper({ onComplete }) {
  const { jobId } = useParams()
  const navigate = useNavigate()
  
  return (
    <AnalysisPage 
      jobId={jobId} 
      onComplete={onComplete}
      onError={() => navigate('/')}
    />
  )
}

function CertificateLoader() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchResult = async () => {
      try {
        const data = await api.getResult(jobId)
        // Show certificate if it exists, regardless of credits (might be 0 for duplicate)
        if (data.job_id) { 
          setResult(data)
        } else {
          navigate('/')
        }
      } catch (e) {
        navigate('/')
      } finally {
        setLoading(false)
      }
    }
    fetchResult()
  }, [jobId, navigate])

  if (loading) return <div className="text-center pt-20 text-white">Loading certificate...</div>
  if (!result) return null

  return <CreditCertificate result={result} onViewDashboard={() => navigate('/dashboard')} />
}