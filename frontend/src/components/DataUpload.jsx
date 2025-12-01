import React, { useState } from 'react'
import axios from 'axios'
import { Upload, Link as LinkIcon, Loader, FileUp, Database } from 'lucide-react'

const API_URL = 'http://localhost:5000/api'

function DataUpload({ onAnalysisComplete, loading, setLoading }) {
    const [uploadType, setUploadType] = useState('file')
    const [apiUrl, setApiUrl] = useState('')
    const [apiMethod, setApiMethod] = useState('GET')
    const [apiHeaders, setApiHeaders] = useState('')
    const [jsonPath, setJsonPath] = useState('')
    const [error, setError] = useState(null)

    const handleFileUpload = async (e) => {
        const file = e.target.files[0]
        if (!file) return

        setLoading(true)
        setError(null)

        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await axios.post(`${API_URL}/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
            onAnalysisComplete(response.data)
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to upload file')
        } finally {
            setLoading(false)
        }
    }

    const handleApiLoad = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        let headers = {}
        if (apiHeaders) {
            try {
                headers = JSON.parse(apiHeaders)
            } catch (err) {
                setError('Invalid JSON in headers')
                setLoading(false)
                return
            }
        }

        try {
            const response = await axios.post(`${API_URL}/load-from-api`, {
                url: apiUrl,
                method: apiMethod,
                headers: headers,
                json_path: jsonPath || null
            })
            onAnalysisComplete(response.data)
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to load from API')
        } finally {
            setLoading(false)
        }
    }

    const handleSampleData = async () => {
        setLoading(true)
        setError(null)

        try {
            const response = await axios.get(`${API_URL}/sample-data`)
            onAnalysisComplete(response.data)
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to load sample data')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="data-upload">
            <div className="upload-container">
                <h2 className="section-title">Load Your Data</h2>
                <p className="section-description">
                    Upload an Excel/CSV file or connect to an API endpoint to start analyzing
                </p>

                {/* Upload Type Selector */}
                <div className="upload-type-selector">
                    <button
                        className={`type-btn ${uploadType === 'file' ? 'active' : ''}`}
                        onClick={() => setUploadType('file')}
                    >
                        <FileUp size={24} />
                        Upload File
                    </button>
                    <button
                        className={`type-btn ${uploadType === 'api' ? 'active' : ''}`}
                        onClick={() => setUploadType('api')}
                    >
                        <Database size={24} />
                        API Endpoint
                    </button>
                </div>

                {/* File Upload */}
                {uploadType === 'file' && (
                    <div className="upload-section">
                        <div className="file-upload-area">
                            <input
                                type="file"
                                accept=".xlsx,.xls,.csv"
                                onChange={handleFileUpload}
                                disabled={loading}
                                id="file-input"
                                className="file-input"
                            />
                            <label htmlFor="file-input" className="file-label">
                                {loading ? (
                                    <Loader className="spin" size={48} />
                                ) : (
                                    <Upload size={48} />
                                )}
                                <span className="file-label-text">
                                    {loading ? 'Analyzing...' : 'Click to upload or drag & drop'}
                                </span>
                                <span className="file-label-subtext">Excel (.xlsx, .xls) or CSV files</span>
                            </label>
                        </div>

                        <div className="divider">
                            <span>OR</span>
                        </div>

                        <button
                            className="sample-btn"
                            onClick={handleSampleData}
                            disabled={loading}
                        >
                            Try Sample Data
                        </button>
                    </div>
                )}

                {/* API Endpoint */}
                {uploadType === 'api' && (
                    <form className="api-form" onSubmit={handleApiLoad}>
                        <div className="form-group">
                            <label>API Endpoint URL</label>
                            <input
                                type="url"
                                value={apiUrl}
                                onChange={(e) => setApiUrl(e.target.value)}
                                placeholder="https://api.example.com/data"
                                required
                                className="input"
                            />
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label>HTTP Method</label>
                                <select
                                    value={apiMethod}
                                    onChange={(e) => setApiMethod(e.target.value)}
                                    className="select"
                                >
                                    <option value="GET">GET</option>
                                    <option value="POST">POST</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label>JSON Path (optional)</label>
                                <input
                                    type="text"
                                    value={jsonPath}
                                    onChange={(e) => setJsonPath(e.target.value)}
                                    placeholder="e.g., data.results"
                                    className="input"
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label>Headers (JSON, optional)</label>
                            <textarea
                                value={apiHeaders}
                                onChange={(e) => setApiHeaders(e.target.value)}
                                placeholder='{"Authorization": "Bearer token"}'
                                className="textarea"
                                rows={3}
                            />
                        </div>

                        <button type="submit" className="submit-btn" disabled={loading}>
                            {loading ? (
                                <>
                                    <Loader className="spin" size={20} />
                                    Loading...
                                </>
                            ) : (
                                <>
                                    <LinkIcon size={20} />
                                    Load from API
                                </>
                            )}
                        </button>
                    </form>
                )}

                {/* Error Display */}
                {error && (
                    <div className="error-message">
                        {error}
                    </div>
                )}
            </div>
        </div>
    )
}

export default DataUpload
