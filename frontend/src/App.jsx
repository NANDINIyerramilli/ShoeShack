import React, { useState, useEffect, useRef } from 'react'
import { Send, Sparkles, ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// In-memory cache for fetched link images
const imageCache = new Map()

// High-quality contextual sneaker images for instant visual presentation
const SNEAKER_PREVIEWS = {
  running: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80",
  walking: "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=400&q=80",
  sneaker: "https://images.unsplash.com/photo-1552346154-21d32810aba3?w=400&q=80",
  campus: "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=400&q=80",
  sparx: "https://images.unsplash.com/photo-1560769629-975ec94e6a86?w=400&q=80",
  nike: "https://images.unsplash.com/photo-1515955656352-a1fa3ffcd111?w=400&q=80",
  default: "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&q=80"
}

function getContextualSneakerImage(url = '', text = '') {
  const combined = (url + ' ' + text).toLowerCase()
  if (combined.includes('running')) return SNEAKER_PREVIEWS.running
  if (combined.includes('walking')) return SNEAKER_PREVIEWS.walking
  if (combined.includes('campus')) return SNEAKER_PREVIEWS.campus
  if (combined.includes('sparx')) return SNEAKER_PREVIEWS.sparx
  if (combined.includes('nike')) return SNEAKER_PREVIEWS.nike
  if (combined.includes('sneaker')) return SNEAKER_PREVIEWS.sneaker
  return SNEAKER_PREVIEWS.default
}

function ChatLink({ href, children }) {
  const linkText = typeof children === 'string' ? children : (Array.isArray(children) ? children.join(' ') : '')
  const isDirectImage = href && /\.(jpeg|jpg|gif|png|webp|svg)(\?.*)?$/i.test(href)

  const [imageUrl, setImageUrl] = useState(() => {
    if (isDirectImage) return href
    return imageCache.get(href) || null
  })
  const [failed, setFailed] = useState(false)

  const fallback = getContextualSneakerImage(href, linkText)

  useEffect(() => {
    if (!href || isDirectImage) return
    if (imageCache.has(href)) {
      setImageUrl(imageCache.get(href))
      return
    }

    let active = true
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 3500)

    fetch(`https://api.microlink.io?url=${encodeURIComponent(href)}`, { signal: controller.signal })
      .then(res => res.json())
      .then(data => {
        clearTimeout(timeout)
        const ogImage = data?.data?.image?.url || data?.data?.logo?.url
        if (active) {
          const finalImg = ogImage || fallback
          imageCache.set(href, finalImg)
          setImageUrl(finalImg)
        }
      })
      .catch(() => {
        if (active) {
          imageCache.set(href, fallback)
          setImageUrl(fallback)
        }
      })

    return () => {
      active = false
      clearTimeout(timeout)
      controller.abort()
    }
  }, [href, isDirectImage, fallback])

  const preview = imageUrl || fallback

  const cleanLabel = (() => {
    if (typeof children === 'string' && (children.startsWith('http://') || children.startsWith('https://'))) {
      if (children.includes('flipkart.com')) return 'View on Flipkart'
      if (children.includes('amazon.')) return 'View on Amazon'
      if (children.includes('nike.com')) return 'View on Nike'
      return 'View Product'
    }
    return children
  })()

  return (
    <span className="chat-link-wrap">
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="chat-link-badge"
        title="Open product link"
      >
        <span>{cleanLabel}</span>
        <ExternalLink size={12} className="link-badge-icon" />
      </a>
      {preview && !failed && (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="chat-link-preview-card"
          title={`Product preview: ${linkText || 'Open link'}`}
        >
          <img
            src={preview}
            alt={linkText || "Product preview"}
            className="chat-link-img"
            onError={() => {
              if (preview !== fallback) {
                setImageUrl(fallback)
              } else {
                setFailed(true)
              }
            }}
            loading="lazy"
          />
        </a>
      )}
    </span>
  )
}

const MARKDOWN_COMPONENTS = {
  table: (props) => (
    <div className="table-responsive-wrapper">
      <table className="chat-table" {...props} />
    </div>
  ),
  th: (props) => <th className="chat-th" {...props} />,
  td: (props) => <td className="chat-td" {...props} />,
  a: ({ href, children, ...props }) => (
    <ChatLink href={href} {...props}>{children}</ChatLink>
  ),
  img: ({ src, alt, ...props }) => (
    <div className="chat-image-block">
      <img src={src} alt={alt || "Product"} className="chat-embedded-img" loading="lazy" {...props} />
    </div>
  ),
  ul: (props) => <ul className="chat-ul" {...props} />,
  ol: (props) => <ol className="chat-ol" {...props} />,
  li: (props) => <li className="chat-li" {...props} />,
  p: (props) => <p className="chat-paragraph" {...props} />,
  strong: (props) => <strong className="chat-strong" {...props} />,
  h1: (props) => <h3 className="chat-h1" {...props} />,
  h2: (props) => <h3 className="chat-h2" {...props} />,
  h3: (props) => <h4 className="chat-h3" {...props} />,
  code: ({ inline, children, ...props }) =>
    inline ? (
      <code className="chat-code-inline" {...props}>{children}</code>
    ) : (
      <pre className="chat-pre"><code {...props}>{children}</code></pre>
    )
}

const SUGGESTIONS = [
  "👟 Show running shoes under 2000",
  "📦 Status of my orders",
  "🔄 Return & refund policy",
  "💳 HDFC card discount"
]

export default function App() {
  const [inputQuery, setInputQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Welcome to **Shoe Shack**! 👟 Ask me anything about our sneaker catalog, your orders, or store policies."
    }
  ])

  const messagesEndRef = useRef(null)
  const hasActiveChat = messages.length > 1

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSendMessage = async (queryText) => {
    const textToSend = queryText || inputQuery
    if (!textToSend.trim() || loading) return

    const userMessage = { role: 'user', content: textToSend }
    setMessages(prev => [...prev, userMessage])
    setInputQuery('')
    setLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: textToSend, user_id: 'user_1' })
      })

      if (!response.ok) {
        throw new Error(`Server status: ${response.status}`)
      }

      const data = await response.json()
      const botReply = data.response || "No response received."
      setMessages(prev => [...prev, { role: 'assistant', content: botReply }])
    } catch (err) {
      console.error('Chat error:', err)
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Could not reach Shoe Shack agent (${err.message}).`
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const renderContent = (content) => (
    <div className="markdown-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={MARKDOWN_COMPONENTS}>
        {content}
      </ReactMarkdown>
    </div>
  )

  return (
    <div className={`app-wrapper ${hasActiveChat ? 'chat-expanded' : ''}`}>
      {/* MAIN WEBPAGE (Shoe background + Dynamic Title + Bottom Chat Dock) */}
      <div className={`main-page ${hasActiveChat ? 'chat-active' : ''}`}>
        <div className="backdrop-darkener" />

        {/* Dynamic Title: Prominent Hero when idle, shifts up to header as chat fills screen */}
        <div className={`center-title-container ${hasActiveChat ? 'chat-active' : ''}`}>
          <h1 className={`center-title ${hasActiveChat ? 'chat-active' : ''}`}>SHOE SHACK</h1>
        </div>

        {/* Bottom Chat Dock: Expands gracefully as conversation develops */}
        <div className={`chat-dock ${hasActiveChat ? 'chat-dock-active' : ''}`}>
          <div className="translucent-chat-card">
            {/* Scrollable messages stream */}
            <div className="messages-stream">
              {messages.map((msg, index) => (
                <div key={index} className={`chat-row ${msg.role}`}>
                  <div className="bubble">
                    {renderContent(msg.content)}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="chat-row assistant">
                  <div className="bubble typing-dots">
                    <span className="dot" />
                    <span className="dot" />
                    <span className="dot" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Suggestions */}
            <div className="suggestion-pills">
              {SUGGESTIONS.map((s, idx) => (
                <button
                  key={idx}
                  className="pill-btn"
                  onClick={() => handleSendMessage(s)}
                  disabled={loading}
                >
                  <Sparkles size={11} style={{ display: 'inline', marginRight: '4px', verticalAlign: '-1px' }} />
                  {s}
                </button>
              ))}
            </div>

            {/* Bottom Input Bar */}
            <form
              className="bottom-input-bar"
              onSubmit={(e) => {
                e.preventDefault()
                handleSendMessage()
              }}
            >
              <input
                type="text"
                className="chat-input"
                placeholder="Ask Shoe Shack about shoes, orders, policies…"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className="send-btn"
                disabled={!inputQuery.trim() || loading}
                title="Send message"
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
