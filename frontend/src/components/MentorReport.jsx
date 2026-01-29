import { motion } from 'framer-motion'
import { BookOpen, Target, TrendingUp, Zap, CheckCircle2, AlertCircle } from 'lucide-react'
import { useState } from 'react'

export default function MentorReport({ plan }) {
  if (!plan?.markdown_report) {
    return (
      <div className="bg-surface border border-border rounded-xl p-8 text-center">
        <BookOpen className="w-12 h-12 text-text-dim mx-auto mb-4" />
        <p className="text-text-muted">No mentorship plan available</p>
      </div>
    )
  }

  // --- FIX START: Safely Extract Markdown ---
  // If the backend sends a JSON string inside the field, we parse it here.
  let reportContent = plan.markdown_report;
  
  try {
    const trimmed = reportContent.trim();
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
      const parsed = JSON.parse(trimmed);
      // Try known keys or fallback to the raw string if structure is unexpected
      reportContent = parsed.mentorship_report || parsed.markdown || parsed.report || reportContent;
    }
  } catch (e) {
    // Not JSON, ignore and use as raw string
  }
  // --- FIX END ---

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

        {/* Stats */}
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
        <MarkdownRenderer content={reportContent} />
      </div>
    </motion.div>
  )
}


// ============================================================================
// Markdown Renderer
// ============================================================================

function MarkdownRenderer({ content }) {
  // Ensure content is a string before parsing
  const safeContent = typeof content === 'string' ? content : JSON.stringify(content);
  const sections = parseMarkdown(safeContent);

  return (
    <div className="prose-custom space-y-8">
      {sections.map((section, i) => (
        <MarkdownSection key={i} {...section} />
      ))}
    </div>
  )
}


// ============================================================================
// Markdown Parser
// ============================================================================

function parseMarkdown(content) {
  const sections = []
  const lines = content.split('\n')
  
  let currentSection = null
  let currentParagraph = []
  let currentList = []
  let inCodeBlock = false
  let codeBlockContent = []
  let codeLanguage = ''
  
  const flushParagraph = () => {
    if (currentParagraph.length > 0 && currentSection) {
      currentSection.content.push({
        type: 'paragraph',
        text: currentParagraph.join(' ')
      })
      currentParagraph = []
    }
  }
  
  const flushList = () => {
    if (currentList.length > 0 && currentSection) {
      currentSection.content.push({
        type: 'list',
        items: currentList
      })
      currentList = []
    }
  }
  
  // Default section for content before any header
  if (!content.trim().startsWith('#')) {
      currentSection = {
          level: 1,
          title: 'Introduction',
          content: []
      }
  }

  for (const line of lines) {
    // Code blocks
    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        if (currentSection) {
          currentSection.content.push({
            type: 'code',
            language: codeLanguage,
            content: codeBlockContent.join('\n')
          })
        }
        codeBlockContent = []
        codeLanguage = ''
        inCodeBlock = false
      } else {
        flushParagraph()
        flushList()
        // Handle ```javascript etc.
        codeLanguage = line.trim().substring(3).trim()
        inCodeBlock = true
      }
      continue
    }
    
    if (inCodeBlock) {
      codeBlockContent.push(line)
      continue
    }
    
    // H1 Headers
    if (line.startsWith('# ')) {
      flushParagraph()
      flushList()
      if (currentSection) sections.push(currentSection)
      
      currentSection = {
        level: 1,
        title: line.replace('# ', '').trim(),
        content: []
      }
    }
    // H2 Headers
    else if (line.startsWith('## ')) {
      flushParagraph()
      flushList()
      // If we hit an H2 but have no currentSection, create a dummy one
      if (!currentSection) {
          currentSection = { level: 1, title: 'Report', content: [] }
      }
      
      currentSection.content.push({
        type: 'heading',
        level: 2,
        text: line.replace('## ', '').trim()
      })
    }
    // H3 Headers
    else if (line.startsWith('### ')) {
      flushParagraph()
      flushList()
      if (!currentSection) {
          currentSection = { level: 1, title: 'Report', content: [] }
      }
      
      currentSection.content.push({
        type: 'heading',
        level: 3,
        text: line.replace('### ', '').trim()
      })
    }
    // Lists
    else if (line.match(/^[-*]\s/) || line.match(/^\d+\.\s/)) {
      flushParagraph()
      const item = line.replace(/^[-*]\s/, '').replace(/^\d+\.\s/, '').trim()
      currentList.push(item)
    }
    // Horizontal rule
    else if (line.trim() === '---' || line.trim() === '***') {
      flushParagraph()
      flushList()
      if (currentSection) {
        currentSection.content.push({
          type: 'hr'
        })
      }
    }
    // Regular text
    else if (line.trim()) {
      flushList()
      currentParagraph.push(line.trim())
    }
    // Empty line
    else {
      flushParagraph()
      flushList()
    }
  }
  
  // Flush final content
  flushParagraph()
  flushList()
  if (currentSection) sections.push(currentSection)
  
  return sections
}


// ============================================================================
// Section Component
// ============================================================================

function MarkdownSection({ level, title, content }) {
  return (
    <div className="space-y-6">
      {/* H1 Title */}
      {level === 1 && (
        <h1 className="text-4xl font-bold text-text-main pb-4 border-b-2 border-border">
          {title}
        </h1>
      )}
      
      {/* Content Blocks */}
      <div className="space-y-4">
        {content.map((block, i) => (
          <ContentBlock key={i} {...block} />
        ))}
      </div>
    </div>
  )
}


// ============================================================================
// Content Blocks
// ============================================================================

function ContentBlock({ type, text, items, level, content, language }) {
  switch (type) {
    case 'heading':
      return <Heading level={level} text={text} />
    
    case 'paragraph':
      return <Paragraph text={text} />
    
    case 'list':
      return <List items={items} />
    
    case 'code':
      return <CodeBlock content={content} language={language} />
    
    case 'hr':
      return <hr className="border-border my-8" />
    
    default:
      return null
  }
}


function Heading({ level, text }) {
  // Extract emoji from text if present
  const emojiMatch = text.match(/^(\p{Emoji})\s+(.+)$/u)
  const emoji = emojiMatch ? emojiMatch[1] : null
  const cleanText = emojiMatch ? emojiMatch[2] : text
  
  const icons = {
    2: <Target className="w-5 h-5 text-primary" />,
    3: <TrendingUp className="w-4 h-4 text-primary" />
  }
  
  if (level === 2) {
    return (
      <h2 className="text-2xl font-bold text-text-main mt-10 mb-4 flex items-center gap-3">
        {emoji && <span className="text-3xl">{emoji}</span>}
        {!emoji && icons[2]}
        {cleanText}
      </h2>
    )
  }
  
  if (level === 3) {
    return (
      <h3 className="text-xl font-bold text-primary mt-6 mb-3 flex items-center gap-2">
        {emoji && <span className="text-2xl">{emoji}</span>}
        {!emoji && icons[3]}
        {cleanText}
      </h3>
    )
  }
  
  return null
}


function Paragraph({ text }) {
  return (
    <p className="text-text-muted leading-relaxed text-base">
      <FormattedText text={text} />
    </p>
  )
}


function List({ items }) {
  return (
    <ul className="space-y-2 my-4">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-3 text-text-muted">
          <span className="text-primary mt-1.5 shrink-0">→</span>
          <span className="flex-1">
            <FormattedText text={item} />
          </span>
        </li>
      ))}
    </ul>
  )
}


function CodeBlock({ content, language }) {
  const [copied, setCopied] = useState(false)
  
  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  
  return (
    <div className="relative group">
      <pre className="bg-surface p-4 rounded-lg text-sm font-mono overflow-x-auto border border-border">
        <code className="text-text-main">{content}</code>
      </pre>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 px-3 py-1 bg-panel border border-border rounded text-xs text-text-muted hover:text-text-main hover:border-primary transition-colors opacity-0 group-hover:opacity-100"
      >
        {copied ? 'Copied!' : 'Copy'}
      </button>
      {language && (
        <div className="absolute top-2 left-2 px-2 py-1 bg-primary/10 rounded text-xs text-primary font-semibold">
          {language}
        </div>
      )}
    </div>
  )
}


// ============================================================================
// Inline Text Formatting
// ============================================================================

function FormattedText({ text }) {
  if (!text) return null;
  
  const parts = []
  let current = ''
  let i = 0
  
  while (i < text.length) {
    // Bold **text**
    if (text[i] === '*' && text[i+1] === '*') {
      if (current) parts.push(current)
      current = ''
      
      i += 2
      let bold = ''
      while (i < text.length && !(text[i] === '*' && text[i+1] === '*')) {
        bold += text[i]
        i++
      }
      parts.push(
        <strong key={parts.length} className="text-text-main font-bold">
          {bold}
        </strong>
      )
      i += 2
    }
    // Inline code `text`
    else if (text[i] === '`') {
      if (current) parts.push(current)
      current = ''
      
      i++
      let code = ''
      while (i < text.length && text[i] !== '`') {
        code += text[i]
        i++
      }
      parts.push(
        <code 
          key={parts.length} 
          className="bg-surface px-2 py-0.5 rounded text-primary text-sm font-mono"
        >
          {code}
        </code>
      )
      i++
    }
    // Regular text
    else {
      current += text[i]
      i++
    }
  }
  
  if (current) parts.push(current)
  
  return parts.length > 1 ? parts : text
}


// ============================================================================
// Level Progress Indicator
// ============================================================================

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