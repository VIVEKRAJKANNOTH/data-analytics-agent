import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import './App.css'
import ChatInterface from './components/ChatInterface'
import AdminDashboard from './components/AdminDashboard'
import { LayoutDashboard } from 'lucide-react'

function App() {
    return (
        <Router>
            <div className="app">
                {/* Header */}
                <header className="app-header flex justify-between items-center px-6">
                    <h1 className="app-title">Data Analytics Agent</h1>
                    <Link to="/admin" className="text-gray-600 hover:text-blue-600 transition-colors" title="Admin Dashboard">
                        <LayoutDashboard size={24} />
                    </Link>
                </header>

                {/* Main Content */}
                <main className="main">
                    <Routes>
                        <Route path="/" element={<ChatInterface />} />
                        <Route path="/admin" element={<AdminDashboard />} />
                    </Routes>
                </main>
            </div>
        </Router>
    )
}

export default App
