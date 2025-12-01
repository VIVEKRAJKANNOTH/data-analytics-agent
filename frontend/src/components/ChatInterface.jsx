import React, { useState, useRef } from 'react'
import axios from 'axios'
import { Send, Loader, Bot, User, Plus, Upload, Database, X, ThumbsUp, ThumbsDown } from 'lucide-react'
import PlotlyRenderer from './PlotlyRenderer'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const API_URL = 'http://localhost:5000/api'

function ChatInterface() {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: 'Hi! I\'m your AI data analyst. Upload a file or generate sample data to get started!'
        }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [showSampleModal, setShowSampleModal] = useState(false)
    const [feedbackModal, setFeedbackModal] = useState({ show: false, rating: null, messageIndex: null, feedback: '' })
    const [sessionId, setSessionId] = useState(null)
    const fileInputRef = useRef(null)

    // Create session on mount
    React.useEffect(() => {
        const createSession = async () => {
            try {
                const response = await axios.post(`${API_URL}/session/create`)
                if (response.data.success) {
                    setSessionId(response.data.session_id)
                }
            } catch (err) {
                console.error("Failed to create session", err)
            }
        }
        createSession()
    }, [])

    const addMessage = (role, content, plotConfig = null, code = null) => {
        setMessages(prev => [...prev, { role, content, plotConfig, code }])
    }

    const handleFileUpload = async (event) => {
        const file = event.target.files[0]
        if (!file) return

        const formData = new FormData()
        formData.append('file', file)

        setUploading(true)
        addMessage('user', `Uploading file: ${file.name}...`)

        try {
            const response = await axios.post(`${API_URL}/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })

            if (response.data.success) {
                addMessage('assistant', `✅ File uploaded successfully! ${response.data.rows} rows, ${response.data.columns} columns.`)
                // Trigger automatic summary
                generateInitialSummary()
            }
        } catch (err) {
            addMessage('assistant', '❌ Upload failed. Please try again.')
        } finally {
            setUploading(false)
            if (fileInputRef.current) fileInputRef.current.value = ''
        }
    }

    const handleSampleData = async (domain) => {
        setShowSampleModal(false)
        setUploading(true)
        addMessage('user', `Generate sample ${domain} data...`)

        try {
            const response = await axios.post(`${API_URL}/generate-sample-data`, { domain })

            if (response.data.success) {
                addMessage('assistant', `✅ Sample ${domain} data generated! ${response.data.rows} rows.`)
                // Trigger automatic summary
                generateInitialSummary()
            }
        } catch (err) {
            addMessage('assistant', '❌ Failed to generate sample data.')
        } finally {
            setUploading(false)
        }
    }

    const generateInitialSummary = async () => {
        setLoading(true)
        try {
            // We send a hidden message to trigger the summary
            const response = await axios.post(`${API_URL}/chat`, {
                message: "Provide a brief summary of this dataset with key statistics and create an appropriate visualization."
            })

            const data = response.data
            addMessage('assistant', data.response, data.plot_config, data.code)
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleSend = async (e) => {
        e.preventDefault()
        if (!input.trim() || loading) return

        const userMessage = input.trim()
        setInput('')
        addMessage('user', userMessage)
        setLoading(true)

        try {
            const endpoint = sessionId ? `${API_URL}/chat-session` : `${API_URL}/chat`
            const payload = sessionId
                ? { session_id: sessionId, message: userMessage }
                : { message: userMessage }

            const response = await axios.post(endpoint, payload)

            const data = response.data
            addMessage('assistant', data.response, data.plot_config, data.code)
        } catch (err) {
            addMessage('assistant', 'Sorry, I encountered an error. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    const openFeedbackModal = (rating, index) => {
        setFeedbackModal({
            show: true,
            rating,
            messageIndex: index,
            feedback: ''
        })
    }

    const submitFeedback = async () => {
        if (!sessionId) return

        try {
            // Find context
            const messageIndex = feedbackModal.messageIndex
            const agentMessage = messages[messageIndex]
            const userMessage = messages[messageIndex - 1] // Assuming user message is immediately before

            await axios.post(`${API_URL}/evaluate`, {
                session_id: sessionId,
                message_index: messageIndex,
                rating: feedbackModal.rating,
                feedback: feedbackModal.feedback,
                user_message: userMessage?.content,
                agent_response: agentMessage?.content
            })

            // Close modal
            setFeedbackModal({ show: false, rating: null, messageIndex: null, feedback: '' })
            alert('Thank you for your feedback!')
        } catch (err) {
            console.error('Failed to submit feedback', err)
            alert('Failed to submit feedback')
        }
    }

    return (
        <div className="chat-interface">
            {/* Toolbar */}
            <div className="chat-toolbar">
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                />
                <button
                    className="toolbar-btn primary"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading || loading}
                >
                    {uploading ? <Loader className="spin" size={16} /> : <Upload size={16} />}
                    Upload Data
                </button>
                <button
                    className="toolbar-btn secondary"
                    onClick={() => setShowSampleModal(true)}
                    disabled={uploading || loading}
                >
                    <Database size={16} />
                    Sample Data
                </button>
            </div>

            <div className="chat-container">
                <div className="chat-messages">
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`message message-${msg.role}`}>
                            <div className="message-icon">
                                {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
                            </div>
                            <div className="message-content">
                                <div className="message-text">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>
                                {msg.plotConfig && (
                                    <div className="message-chart">
                                        <PlotlyRenderer config={msg.plotConfig} height={450} />
                                    </div>
                                )}
                                {msg.code && (
                                    <details className="code-details">
                                        <summary>View Code</summary>
                                        <pre className="code-block">{msg.code}</pre>
                                    </details>
                                )}
                                {msg.role === 'assistant' && sessionId && (
                                    <div className="message-actions flex gap-2 mt-2 justify-end">
                                        <button
                                            onClick={() => openFeedbackModal('positive', idx)}
                                            className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-green-600 transition-colors"
                                            title="Helpful"
                                        >
                                            <ThumbsUp size={14} />
                                        </button>
                                        <button
                                            onClick={() => openFeedbackModal('negative', idx)}
                                            className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-red-600 transition-colors"
                                            title="Not Helpful"
                                        >
                                            <ThumbsDown size={14} />
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="message message-assistant">
                            <div className="message-icon"><Bot size={20} /></div>
                            <div className="message-content">
                                <div className="typing-indicator">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <form className="chat-input-form" onSubmit={handleSend}>
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask about trends, patterns, or specific insights..."
                        className="chat-input"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        className="send-btn"
                        disabled={loading || !input.trim()}
                    >
                        <Send size={20} />
                    </button>
                </form>
            </div>

            {/* Sample Data Modal */}
            {
                showSampleModal && (
                    <div className="modal-overlay">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h3>Select Sample Data</h3>
                                <button onClick={() => setShowSampleModal(false)}><X size={20} /></button>
                            </div>
                            <div className="domain-grid">
                                <button className="domain-card" onClick={() => handleSampleData('cricket')}>
                                    <div className="domain-icon">🏏</div>
                                    <h4>Cricket</h4>
                                    <p>Player stats, runs, boundaries</p>
                                </button>
                                <button className="domain-card" onClick={() => handleSampleData('sales')}>
                                    <div className="domain-icon">📈</div>
                                    <h4>Sales</h4>
                                    <p>Revenue, products, regions</p>
                                </button>
                                <button className="domain-card" onClick={() => handleSampleData('finance')}>
                                    <div className="domain-icon">💰</div>
                                    <h4>Finance</h4>
                                    <p>Transactions, categories, dates</p>
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Feedback Modal */}
            {
                feedbackModal.show && (
                    <div className="modal-overlay">
                        <div className="modal-content" style={{ maxWidth: '400px' }}>
                            <div className="modal-header">
                                <h3>Provide Feedback</h3>
                                <button onClick={() => setFeedbackModal(prev => ({ ...prev, show: false }))}><X size={20} /></button>
                            </div>
                            <div className="p-4">
                                <div className="flex items-center gap-2 mb-4">
                                    {feedbackModal.rating === 'positive' ? (
                                        <span className="flex items-center gap-2 text-green-600 font-medium">
                                            <ThumbsUp size={20} /> Helpful
                                        </span>
                                    ) : (
                                        <span className="flex items-center gap-2 text-red-600 font-medium">
                                            <ThumbsDown size={20} /> Not Helpful
                                        </span>
                                    )}
                                </div>
                                <textarea
                                    className="w-full p-3 border rounded-lg mb-4 focus:ring-2 focus:ring-blue-500 outline-none"
                                    rows="4"
                                    placeholder="Optional: Tell us more about your experience..."
                                    value={feedbackModal.feedback}
                                    onChange={(e) => setFeedbackModal(prev => ({ ...prev, feedback: e.target.value }))}
                                ></textarea>
                                <button
                                    onClick={submitFeedback}
                                    className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                >
                                    Submit Feedback
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }
        </div>
    )
}

export default ChatInterface
