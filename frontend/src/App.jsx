import React, { useState, useEffect, useRef } from 'react'
import { Send, Sparkles, User, Bot, ArrowRight, RefreshCw, Eye } from 'lucide-react'

export default function App() {
  const [landingVisible, setLandingVisible] = useState(true)
  const [userId, setUserId] = useState('user_1')
  const [inputQuery, setInputQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Welcome to **ShoeShack**! 👟 I'm your AI footwear and customer support assistant. You can ask me to find shoes from our catalog, check your orders, look up support tickets, or answer store policies!"
    }
  ])

  const messagesEndRef = useRef(null)

  // Scroll to bottom on new message
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
        body: JSON.stringify({ query: textToSend, user_id: userId })
      })

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`)
      }

      const data = await response.json()
      const botReply = data.response || "I couldn't generate a response."
      setMessages(prev => [...prev, { role: 'assistant', content: botReply }])
    } catch (err) {
      console.error('Chat error:', err)
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Error communicating with ShoeShack agent: ${err.message}. Please verify the backend API server is running.`
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const suggestions = [
    "👟 Show running shoes under 2000",
    "📦 What are my recent orders?",
    "🔄 What is the return policy?",
    "💳 Do I get a discount with HDFC credit card?",
    "🎫 Any complaints on my account?"
  ]

  // Render message formatting simple helper
  const renderMessageContent = (content) => {
    const lines = content.split('\n')
    return lines.map((line, idx) => {
      // Bold rendering
      const parts = line.split(/(\*\*.*?\*\*)/g)
      return (
        <p key={idx} style={{ minHeight: line.trim() ? 'auto' : '0.5rem' }}>
          {parts.map((part, pIdx) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return <strong key={pIdx}>{part.slice(2, -2)}</strong>
            }
            return part
          })}
        </p>
      )
    })
  }

  return (
    <div className="app-container">
      {/* 1. INITIAL LANDING SPLASH (Shoe with Sky) */}
      <div className={`landing-splash ${!landingVisible ? 'faded-out' : ''}`}>
        <div className="landing-overlay" />
        <div className="landing-content">
          <p className="landing-tagline">
            Step Into Next-Gen Footwear & Agentic AI Support
          </p>
          <button
            className="enter-button"
            onClick={() => setLandingVisible(false)}
          >
            <span>Enter ShoeShack</span>
            <ArrowRight size={20} />
          </button>
        </div>
      </div>

      {/* 2. MAIN WEBPAGE (Shoes and Box Background + Translucent Glass Layer) */}
      <div className="main-page">
        <div className="translucent-layer" />

        <div className="page-content">
          {/* Header Bar */}
          <header className="header-bar">
            <div className="brand-section">
              <span className="brand-logo-icon">👟</span>
              <div>
                <h1 className="brand-title">SHOE SHACK</h1>
                <p className="brand-subtitle">AI Footwear Catalog & Customer Support</p>
              </div>
            </div>

            <div className="header-controls">
              <button
                className="splash-toggle-btn"
                onClick={() => setLandingVisible(true)}
                title="View Splash Screen again"
              >
                <Eye size={15} style={{ display: 'inline', marginRight: '4px', verticalAlign: '-2px' }} />
                Landing Page
              </button>

              <div className="user-selector">
                <User size={15} color="#ff4724" />
                <span>User:</span>
                <select value={userId} onChange={(e) => setUserId(e.target.value)}>
                  <option value="user_1">user_1</option>
                  <option value="user_2">user_2</option>
                  <option value="user_3">user_3</option>
                  <option value="user_4">user_4</option>
                  <option value="user_5">user_5</option>
                </select>
              </div>

              <div className="status-badge">
                <span className="status-dot" />
                <span>Agent Active</span>
              </div>
            </div>
          </header>

          {/* Chat Window */}
          <main className="chat-window">
            <div className="chat-messages">
              {messages.map((msg, index) => (
                <div key={index} className={`message-row ${msg.role}`}>
                  <div className={`avatar ${msg.role === 'user' ? 'user-avatar' : 'bot-avatar'}`}>
                    {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                  </div>
                  <div className="message-bubble">
                    {renderMessageContent(msg.content)}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message-row assistant">
                  <div className="avatar bot-avatar">
                    <Bot size={18} />
                  </div>
                  <div className="message-bubble typing-bubble">
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Suggestions */}
            <div className="suggestions-bar">
              {suggestions.map((s, idx) => (
                <button
                  key={idx}
                  className="suggestion-chip"
                  onClick={() => handleSendMessage(s)}
                  disabled={loading}
                >
                  <Sparkles size={12} style={{ display: 'inline', marginRight: '4px', verticalAlign: '-1px' }} />
                  {s}
                </button>
              ))}
            </div>

            {/* Chat Input Area */}
            <div className="chat-input-area">
              <form
                className="input-form"
                onSubmit={(e) => {
                  e.preventDefault()
                  handleSendMessage()
                }}
              >
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Ask ShoeShack about shoes, orders, complaints, policies…"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  disabled={loading}
                />
                <button
                  type="submit"
                  className="send-button"
                  disabled={!inputQuery.trim() || loading}
                >
                  <Send size={18} />
                </button>
              </form>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
