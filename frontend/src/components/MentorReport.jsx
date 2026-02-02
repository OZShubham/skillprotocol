import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { 
  BookOpen, Target, TrendingUp, AlertCircle, 
  Check, Copy, Terminal 
} from 'lucide-react'

export default function MentorReport({ plan }) {
  if (!plan?.markdown_report) {
    return (
      <div className="bg-surface border border-border rounded-xl p-8 text-center">
        <BookOpen className="w-12 h-12 text-text-dim mx-auto mb-4" />
        <p className="text-text-muted">No mentorship plan available</p>
      </div>
    )
  }

  // --- SAFE EXTRACTION LOGIC ---
  // This handles cases where the LLM might double-encode the JSON
  // or return the report inside a nested 'mentorship_report' key.
  let reportContent = plan.markdown_report
  try {
    const trimmed = reportContent.trim()
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
      const parsed = JSON.parse(trimmed)
      reportContent = parsed.mentorship_report || parsed.markdown || parsed.report || reportContent
    }
  } catch (e) {
    // If parsing fails, it's likely just a raw markdown string, which is what we want.
  }

  const currentLevel = plan.current_level || 1
  const targetLevel = plan.target_level || currentLevel + 1

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header Card */}
      <div className="bg-panel border border-border rounded-xl p-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-primary/10 rounded-lg">
              <BookOpen className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-text-main">
                Your Personalized Growth Plan
              </h2>
              <p className="text-sm text-text-muted mt-1">
                Level {currentLevel} → Level {targetLevel}
              </p>
            </div>
          </div>
          
          <LevelProgressIndicator current={currentLevel} target={targetLevel} />
        </div>

        {/* Stats Summary - Only shows if there are specific items to flag */}
        {(plan.missing_elements_count > 0 || plan.issues_identified > 0) && (
          <div className="flex gap-4 mt-6 pt-6 border-t border-border flex-wrap">
            {plan.missing_elements_count > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <AlertCircle className="w-4 h-4 text-orange-400" />
                <span className="text-text-muted">
                  {plan.missing_elements_count} gaps to address
                </span>
              </div>
            )}
            {plan.issues_identified > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <Target className="w-4 h-4 text-blue-400" />
                <span className="text-text-muted">
                  {plan.issues_identified} improvements identified
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Main Markdown Content */}
      <div className="bg-panel border border-border rounded-xl p-8">
        <div className="prose-custom">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={MarkdownComponents}
          >
            {reportContent}
          </ReactMarkdown>
        </div>
      </div>
    </motion.div>
  )
}

// ============================================================================
// Custom Markdown Components (Styled for Tailwind & Void Theme)
// ============================================================================

const MarkdownComponents = {
  // H1: Large, underlined, extra spacing
  h1: ({ node, ...props }) => (
    <h1 className="text-4xl font-bold text-text-main pb-4 border-b-2 border-border mb-6 mt-8 first:mt-0" {...props} />
  ),
  
  // H2: Target Icon style
  h2: ({ node, ...props }) => (
    <h2 className="text-2xl font-bold text-text-main mt-10 mb-4 flex items-center gap-3">
      <Target className="w-6 h-6 text-primary shrink-0" />
      <span>{props.children}</span>
    </h2>
  ),

  // H3: TrendingUp Icon style
  h3: ({ node, ...props }) => (
    <h3 className="text-xl font-bold text-primary mt-8 mb-3 flex items-center gap-2">
      <TrendingUp className="w-5 h-5 text-primary shrink-0" />
      <span>{props.children}</span>
    </h3>
  ),

  // Paragraphs with relaxed line-height for readability
  p: ({ node, ...props }) => (
    <p className="text-text-muted leading-relaxed text-base mb-4 last:mb-0" {...props} />
  ),

  // Unordered Lists
  ul: ({ node, ...props }) => (
    <ul className="space-y-2 my-4 pl-1" {...props} />
  ),

  // Ordered Lists
  ol: ({ node, ...props }) => (
    <ol className="space-y-2 my-4 list-decimal list-inside text-text-muted" {...props} />
  ),

  // List Items with custom bullet logic
  li: ({ node, ...props }) => (
    <li className="flex items-start gap-3 text-text-muted">
      {/* If it's a UL, use a custom arrow. If OL, use default numbers. */}
      {node.position?.start.column === 1 && !props.checked && props.ordered !== true ? (
        <>
          <span className="text-primary mt-1.5 shrink-0">→</span>
          <span className="flex-1">{props.children}</span>
        </>
      ) : (
        <span className="flex-1">{props.children}</span>
      )}
    </li>
  ),

  // Blockquotes for hints/notes
  blockquote: ({ node, ...props }) => (
    <blockquote className="border-l-4 border-primary/50 bg-surface/50 p-4 rounded-r-lg my-6 italic text-text-dim" {...props} />
  ),

  // Links (styled to be visible)
  a: ({ node, ...props }) => (
    <a 
      className="text-primary underline decoration-primary/30 underline-offset-4 hover:decoration-primary transition-all" 
      target="_blank" 
      rel="noopener noreferrer" 
      {...props} 
    />
  ),

  // Code Blocks & Inline Code
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '')
    const language = match ? match[1] : ''
    
    // Inline Code `like this`
    if (inline || !match) {
      return (
        <code className="bg-surface px-1.5 py-0.5 rounded text-primary text-sm font-mono border border-border" {...props}>
          {children}
        </code>
      )
    }

    // Block Code (using Syntax Highlighter)
    return (
      <div className="relative group my-6 rounded-lg overflow-hidden border border-border bg-[#282c34]">
        {/* Language Badge */}
        <div className="absolute top-0 right-0 px-3 py-1 text-xs font-mono text-gray-400 bg-white/5 rounded-bl-lg border-b border-l border-white/5">
          {language}
        </div>
        
        {/* Syntax Highlighter */}
        <SyntaxHighlighter
          style={oneDark}
          language={language}
          PreTag="div"
          customStyle={{ margin: 0, padding: '1.5rem', background: 'transparent' }}
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
        
        <CopyButton content={String(children)} />
      </div>
    )
  }
}

// ============================================================================
// Helper Components
// ============================================================================

function CopyButton({ content }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      className="absolute top-3 right-12 p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-white/10 transition-all opacity-0 group-hover:opacity-100"
      title="Copy Code"
    >
      {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
    </button>
  )
}

function LevelProgressIndicator({ current, target }) {
  const getLevelColor = (level) => {
    const colors = {
      1: 'text-gray-400 border-gray-500 bg-gray-500/10',
      2: 'text-blue-400 border-blue-500 bg-blue-500/10',
      3: 'text-green-400 border-green-500 bg-green-500/10',
      4: 'text-primary border-primary bg-primary/10',
      5: 'text-purple-400 border-purple-500 bg-purple-500/10'
    }
    return colors[level] || colors[1]
  }

  return (
    <div className="flex items-center gap-3">
      <div className={`px-4 py-2 rounded-lg border-2 ${getLevelColor(current)} font-bold text-sm`}>
        L{current}
      </div>
      <TrendingUp className="w-5 h-5 text-text-dim" />
      <div className={`px-4 py-2 rounded-lg border-2 ${getLevelColor(target)} font-bold text-sm`}>
        L{target}
      </div>
    </div>
  )
}