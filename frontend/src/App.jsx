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
import ThemeToggle from './components/ui/ThemeToggle'
import MethodologyPage from './components/MethodologyPage'

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()

  // --- DYNAMIC USER STATE ---
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
  useEffect(() => {
    const loadUserData = async () => {
      setAnalysisHistory([]) 
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
    localStorage.setItem('last_user', currentUserId)
  }, [currentUserId])

  // --- EFFECT 2: STATS CALCULATION ---
  useEffect(() => {
    if (analysisHistory.length >= 0) {
      calculateUserStats()
    }
  }, [analysisHistory])

  const calculateUserStats = () => {
    const uniqueRepoCredits = {}
    
    analysisHistory.forEach(item => {
      const url = item.repo_url
      const credits = item.final_credits || 0
      if (!uniqueRepoCredits[url] || credits > uniqueRepoCredits[url]) {
        uniqueRepoCredits[url] = credits
      }
    })

    const totalCredits = Object.values(uniqueRepoCredits).reduce((sum, credit) => sum + credit, 0)
    const verifiedRepos = Object.keys(uniqueRepoCredits).filter(url => uniqueRepoCredits[url] > 0).length

    const bestRuns = Object.entries(uniqueRepoCredits)
      .map(([url, bestCredit]) => analysisHistory.find(item => item.repo_url === url && item.final_credits === bestCredit))
      .filter(Boolean)

    const avgSfia = verifiedRepos > 0 
      ? bestRuns.reduce((sum, item) => sum + (item.sfia_level || 0), 0) / verifiedRepos
      : 0

    let rank = 'Beginner'
    if (totalCredits > 100) rank = 'Top 10%'
    else if (totalCredits > 50) rank = 'Top 25%'
    else if (totalCredits > 20) rank = 'Top 50%'

    setUserStats({
      totalCredits: parseFloat(totalCredits.toFixed(2)),
      verifiedRepos,
      avgSfia: parseFloat(avgSfia.toFixed(1)),
      rank,
      username: currentUserId
    })
  }

  const handleUserDetected = (username) => {
    if (username && username !== currentUserId) {
      setCurrentUserId(username)
    }
  }

  const handleAnalysisComplete = async (jobId) => {
    try {
      const result = await api.getResult(jobId)
      if (result.final_credits !== undefined) {
        const history = await api.getUserHistory(currentUserId)
        setAnalysisHistory(history)

        if (result.final_credits > 0) {
          navigate(`/certificate/${jobId}`)
        } else {
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
    <div className="min-h-screen bg-void text-text-main transition-colors duration-300">
      
      {/* NAVBAR FIX: 
          Forced bg-[#050505] (Dark Black) to match your logo background.
          Forced text colors to white/gray so they are visible on the black bar.
      */}
      <nav className="relative z-50 border-b border-white/10 bg-[#050505] sticky top-0">
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
            <div className="flex items-center gap-4">
              
              {/* Theme Toggle */}
              <ThemeToggle />

              {/* Dynamic Context Badge - Forced Dark Mode Colors */}
              <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-gray-400">
                <div className={`w-1.5 h-1.5 rounded-full ${currentUserId !== 'Guest' ? 'bg-emerald-500 shadow-[0_0_8px_#10B981]' : 'bg-gray-600'}`} />
                <span>Viewing: <strong className="text-white">{currentUserId}</strong></span>
              </div>

              {/* Dashboard Button - Forced Dark Mode Colors */}
              <button
                onClick={() => navigate('/dashboard')}
                className="group flex items-center gap-2 px-4 py-1.5 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 transition-all active:scale-95"
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

          <Route path="/methodology" element={
            <motion.div
              key="methodology"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <MethodologyPage />
            </motion.div>
          } />
          
   
          
          <Route path="/" element={
            <motion.div
              key="landing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
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

// Wrappers
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

  if (loading) return <div className="text-center pt-20 text-text-muted">Loading certificate...</div>
  if (!result) return null

  return <CreditCertificate result={result} onViewDashboard={() => navigate('/dashboard')} />
}