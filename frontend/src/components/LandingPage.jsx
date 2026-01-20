import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { ArrowRight, Github, ShieldCheck, Database, Search } from 'lucide-react'
import { api } from '../services/api'

export default function LandingPage({ onStartAnalysis, onUserDetected, currentUser }) {
  const [repoUrl, setRepoUrl] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [showTokenInput, setShowTokenInput] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const location = useLocation() // Get navigation state

  // Check if we were sent back here to retry with a token (Private Repo Flow)
  useEffect(() => {
    if (location.state?.requestToken) {
      setShowTokenInput(true)
      setError('Please enter your GitHub token to access this private repository.')
    }
    if (location.state?.repoUrl) {
      setRepoUrl(location.state.repoUrl)
    }
  }, [location.state])

  // Helper to extract username from "https://github.com/username/repo"
  const extractOwner = (url) => {
    try {
      // Remove protocol and www
      const clean = url.replace(/^https?:\/\/(www\.)?github\.com\//, '').replace(/^github\.com\//, '')
      const parts = clean.split('/')
      return parts[0] || null
    } catch (e) {
      return null
    }
  }

  const handleAnalyze = async () => {
    if (!repoUrl) {
      setError('Please enter a GitHub repository URL')
      return
    }

    // 1. DETECT USER INSTANTLY
    const owner = extractOwner(repoUrl)
    
    if (owner) {
      // Tell App.jsx to switch context to this user
      onUserDetected(owner) 
    } else {
      setError('Invalid GitHub URL format. Expected: github.com/username/repo')
      return
    }

    setLoading(true)
    setError('')

    try {
      // 2. SEND TO API
      // Important: We use the detected 'owner' as the 'user_id' for the backend
      const tokenToSend = githubToken.trim() || null
      const data = await api.analyzeRepo(repoUrl, owner, tokenToSend)
      
      onStartAnalysis(data.job_id)
      
    } catch (err) {
      const errorMsg = err.message || 'Analysis failed'
      
      // Smart error handling for private repos
      if (errorMsg.toLowerCase().includes('private') || errorMsg.toLowerCase().includes('not found')) {
        setError(`Repo not found or private. We need a token to access ${owner}'s code.`)
        setShowTokenInput(true)
      } else {
        setError(errorMsg)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-20 relative z-10">
      
      {/* Hero Section */}
      <div className="text-center max-w-3xl mx-auto mb-20">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 text-xs text-text-muted mb-6 font-mono">
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          SYSTEM OPERATIONAL
        </div>
        
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6">
          Proof of <span className="text-white">Work.</span><br />
          <span className="text-primary">Verified.</span>
        </h1>
        
        <p className="text-lg text-text-muted mb-10 leading-relaxed max-w-2xl mx-auto">
          The first specialized agentic workflow for minting NCrF & SFIA skill credits directly from your commit history. Backed by Opik traces.
        </p>

        {/* Input Bar */}
        <div className="flex flex-col gap-4 max-w-xl mx-auto">
          <div className="flex bg-panel border border-border p-1.5 rounded-xl shadow-2xl shadow-primary/5 focus-within:border-primary/50 focus-within:shadow-primary/20 transition-all">
            <div className="flex items-center pl-4 text-text-dim">
              <Github className="w-5 h-5" />
            </div>
            <input 
              type="text" 
              placeholder="github.com/username/repository"
              className="flex-1 bg-transparent border-none text-white px-4 py-3 focus:outline-none font-mono text-sm placeholder:text-text-dim"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            />
            <button 
              onClick={handleAnalyze}
              disabled={loading}
              className="bg-white text-black hover:bg-gray-200 font-semibold px-6 py-2 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? 'Scanning...' : 'Verify'}
              {!loading && <ArrowRight className="w-4 h-4" />}
            </button>
          </div>

          {/* Token Input (Conditional) */}
          {showTokenInput && (
            <div className="animate-in fade-in slide-in-from-top-2">
              <input 
                type="password"
                placeholder="ghp_... (Private Repo Token)"
                className="w-full bg-panel border border-primary/30 text-white px-4 py-3 rounded-xl focus:outline-none font-mono text-sm placeholder:text-text-dim"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
              />
              <p className="text-xs text-text-muted mt-2 text-left">
                * Your token is never stored. Used once for cloning.
              </p>
            </div>
          )}

          {error && (
            <div className="text-error text-sm font-mono bg-error/10 border border-error/20 p-3 rounded-lg text-left">
              ! {error}
            </div>
          )}
        </div>
      </div>

      {/* Bento Grid Features */}
      <div className="grid md:grid-cols-3 gap-4 auto-rows-[220px]">
        
        {/* Large Feature */}
        <div className="md:col-span-2 row-span-2 bg-panel border border-border rounded-2xl p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-8 opacity-20 group-hover:opacity-40 transition-opacity">
            <Database className="w-48 h-48 text-text-dim" />
          </div>
          <div className="h-full flex flex-col justify-between relative z-10">
            <div>
              <h3 className="text-xl font-bold text-white mb-2">Deep Code Analysis</h3>
              <p className="text-text-muted max-w-md">Our Scanner Agent clones your repository and builds an AST (Abstract Syntax Tree) to measure true algorithmic complexity, not just lines of code.</p>
            </div>
            <div className="font-mono text-xs text-primary bg-primary/5 border border-primary/20 p-4 rounded-lg max-w-sm mt-8">
              &gt; detecting_patterns...<br/>
              &gt; found: Dockerfile, CI/CD, Async/Await<br/>
              &gt; complexity_score: 8.9/10
            </div>
          </div>
        </div>

        {/* Small Feature 1 */}
        <div className="bg-panel border border-border rounded-2xl p-6 flex flex-col justify-between group hover:border-border-strong transition-colors">
          <ShieldCheck className="w-10 h-10 text-success" />
          <div>
            <h3 className="font-bold text-white mb-1">Reality Check</h3>
            <p className="text-sm text-text-muted">We verify GitHub Actions to ensure code actually builds.</p>
          </div>
        </div>

        {/* Small Feature 2 */}
        <div className="bg-panel border border-border rounded-2xl p-6 flex flex-col justify-between group hover:border-border-strong transition-colors">
          <Search className="w-10 h-10 text-primary" />
          <div>
            <h3 className="font-bold text-white mb-1">Opik Tracing</h3>
            <p className="text-sm text-text-muted">Every credit minted is cryptographically linked to a reasoning trace.</p>
          </div>
        </div>

      </div>
    </div>
  )
}