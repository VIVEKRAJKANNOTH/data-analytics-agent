import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ThumbsUp, ThumbsDown, MessageSquare, ArrowLeft, Sparkles, Loader, TrendingUp, BarChart3, Activity, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';

const API_URL = 'http://localhost:5000/api';

const AdminDashboard = () => {
    const [evaluations, setEvaluations] = useState([]);
    const [summary, setSummary] = useState({ total: 0, positive: 0, negative: 0, positive_rate: 0 });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        fetchEvaluations();
    }, []);

    const fetchEvaluations = async () => {
        try {
            setLoading(true);
            const response = await axios.get(`${API_URL}/evaluations?limit=100`);
            if (response.data.success) {
                setEvaluations(response.data.evaluations);
                setSummary(response.data.summary);
            }
        } catch (err) {
            setError('Failed to load evaluations');
            console.error(err);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const handleRefresh = () => {
        setRefreshing(true);
        fetchEvaluations();
    };

    const handleAutoEvaluate = async (evalItem) => {
        try {
            // Optimistic update to show loading state for specific item
            setEvaluations(prev => prev.map(e =>
                e.id === evalItem.id ? { ...e, evaluating: true } : e
            ));

            const response = await axios.post(`${API_URL}/evaluate/llm`, {
                session_id: evalItem.session_id,
                message_index: 0, // Default for now, ideally should be stored
                user_message: evalItem.context.user_message,
                agent_response: evalItem.context.agent_response
            });

            if (response.data.success) {
                // Refresh list to get updated data
                fetchEvaluations();
            }
        } catch (err) {
            console.error("Auto-evaluation failed", err);
            alert("Failed to run auto-evaluation");
            // Revert loading state
            setEvaluations(prev => prev.map(e =>
                e.id === evalItem.id ? { ...e, evaluating: false } : e
            ));
        }
    };

    if (loading) {
        return (
            <div className="admin-dashboard-container">
                <div className="loading-state">
                    <Loader size={48} className="spin" style={{ color: 'var(--accent-primary)' }} />
                    <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>Loading dashboard...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="admin-dashboard-container">
                <div className="error-state">
                    <p style={{ color: 'var(--accent-error)' }}>{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-dashboard-container">
            <div className="admin-dashboard">
                {/* Header */}
                <div className="dashboard-header">
                    <div className="header-left">
                        <Link to="/" className="back-button">
                            <ArrowLeft size={20} />
                        </Link>
                        <div className="header-title-section">
                            <h1 className="dashboard-title">Evaluation Dashboard</h1>
                            <p className="dashboard-subtitle">Monitor agent performance and user feedback</p>
                        </div>
                    </div>
                    <button
                        onClick={handleRefresh}
                        className="refresh-button"
                        disabled={refreshing}
                    >
                        <RefreshCw size={18} className={refreshing ? 'spin' : ''} />
                        <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
                    </button>
                </div>

                {/* Summary Cards */}
                <div className="stats-grid">
                    <div className="stat-card stat-card-total">
                        <div className="stat-icon-wrapper">
                            <BarChart3 size={24} />
                        </div>
                        <div className="stat-content">
                            <div className="stat-label">Total Evaluations</div>
                            <div className="stat-value">{summary.total}</div>
                            <div className="stat-trend">All time</div>
                        </div>
                        <div className="stat-decoration"></div>
                    </div>

                    <div className="stat-card stat-card-positive">
                        <div className="stat-icon-wrapper">
                            <ThumbsUp size={24} />
                        </div>
                        <div className="stat-content">
                            <div className="stat-label">Positive Feedback</div>
                            <div className="stat-value">{summary.positive}</div>
                            <div className="stat-trend">
                                {summary.total > 0 ? `${Math.round((summary.positive / summary.total) * 100)}% of total` : 'N/A'}
                            </div>
                        </div>
                        <div className="stat-decoration"></div>
                    </div>

                    <div className="stat-card stat-card-negative">
                        <div className="stat-icon-wrapper">
                            <ThumbsDown size={24} />
                        </div>
                        <div className="stat-content">
                            <div className="stat-label">Negative Feedback</div>
                            <div className="stat-value">{summary.negative}</div>
                            <div className="stat-trend">
                                {summary.total > 0 ? `${Math.round((summary.negative / summary.total) * 100)}% of total` : 'N/A'}
                            </div>
                        </div>
                        <div className="stat-decoration"></div>
                    </div>

                    <div className="stat-card stat-card-satisfaction">
                        <div className="stat-icon-wrapper">
                            <TrendingUp size={24} />
                        </div>
                        <div className="stat-content">
                            <div className="stat-label">Satisfaction Rate</div>
                            <div className={`stat-value stat-${summary.positive_rate >= 70 ? 'excellent' : summary.positive_rate >= 50 ? 'good' : 'poor'}`}>
                                {summary.positive_rate}%
                            </div>
                            <div className="stat-trend">
                                {summary.positive_rate >= 70 ? 'Excellent!' : summary.positive_rate >= 50 ? 'Good' : 'Needs improvement'}
                            </div>
                        </div>
                        <div className="stat-decoration"></div>
                    </div>
                </div>

                {/* Recent Evaluations List */}
                <div className="evaluations-section">
                    <div className="section-header">
                        <div>
                            <h2 className="section-title">Recent Feedback</h2>
                            <p className="section-subtitle">Latest user interactions and evaluations</p>
                        </div>
                        <div className="feedback-count">
                            <Activity size={16} />
                            <span>{evaluations.length} items</span>
                        </div>
                    </div>

                    <div className="evaluations-list">
                        {evaluations.length === 0 ? (
                            <div className="empty-evaluations">
                                <MessageSquare size={48} style={{ opacity: 0.3 }} />
                                <p className="empty-title">No evaluations yet</p>
                                <p className="empty-subtitle">User feedback will appear here once available</p>
                            </div>
                        ) : (
                            evaluations.map((eval_item, index) => (
                                <div key={eval_item.id} className="evaluation-card" style={{ animationDelay: `${index * 0.05}s` }}>
                                    <div className="eval-header">
                                        <div className="eval-meta">
                                            <div className={`rating-badge rating-${eval_item.rating}`}>
                                                {eval_item.rating === 'positive' ? (
                                                    <ThumbsUp size={14} />
                                                ) : (
                                                    <ThumbsDown size={14} />
                                                )}
                                                <span>{eval_item.rating === 'positive' ? 'Positive' : 'Negative'}</span>
                                            </div>
                                            <div className="eval-timestamp">
                                                {new Date(eval_item.timestamp).toLocaleString()}
                                            </div>
                                        </div>
                                        <div className="eval-id">#{eval_item.id.slice(0, 8)}</div>
                                    </div>

                                    {eval_item.feedback && (
                                        <div className="feedback-section">
                                            <div className="feedback-label">User Feedback</div>
                                            <div className="feedback-text">{eval_item.feedback}</div>
                                        </div>
                                    )}

                                    <div className="context-grid">
                                        <div className="context-card context-query">
                                            <div className="context-label">
                                                <MessageSquare size={12} />
                                                <span>User Query</span>
                                            </div>
                                            <div className="context-text">{eval_item.context.user_message}</div>
                                        </div>
                                        <div className="context-card context-response">
                                            <div className="context-label">
                                                <Sparkles size={12} />
                                                <span>Agent Response</span>
                                            </div>
                                            <div className="context-text context-text-expandable">
                                                {eval_item.context.agent_response}
                                            </div>
                                        </div>
                                    </div>

                                    {/* LLM Evaluation Section */}
                                    {eval_item.llm_evaluation ? (
                                        <div className="llm-evaluation">
                                            <div className="llm-eval-header">
                                                <div className="llm-eval-title">
                                                    <Sparkles size={16} />
                                                    <span>AI Quality Assessment</span>
                                                </div>
                                                <div className="llm-eval-score">
                                                    <span className="score-value">{eval_item.llm_evaluation.score}</span>
                                                    <span className="score-max">/10</span>
                                                </div>
                                            </div>
                                            <p className="llm-eval-reasoning">{eval_item.llm_evaluation.reasoning}</p>
                                            <div className="criteria-scores">
                                                <div className="criteria-item">
                                                    <div className="criteria-name">Correctness</div>
                                                    <div className="criteria-value">
                                                        <div className="criteria-bar">
                                                            <div
                                                                className="criteria-fill"
                                                                style={{ width: `${(eval_item.llm_evaluation.criteria_scores?.correctness || 0) * 10}%` }}
                                                            ></div>
                                                        </div>
                                                        <span className="criteria-score">{eval_item.llm_evaluation.criteria_scores?.correctness || 0}</span>
                                                    </div>
                                                </div>
                                                <div className="criteria-item">
                                                    <div className="criteria-name">Helpfulness</div>
                                                    <div className="criteria-value">
                                                        <div className="criteria-bar">
                                                            <div
                                                                className="criteria-fill"
                                                                style={{ width: `${(eval_item.llm_evaluation.criteria_scores?.helpfulness || 0) * 10}%` }}
                                                            ></div>
                                                        </div>
                                                        <span className="criteria-score">{eval_item.llm_evaluation.criteria_scores?.helpfulness || 0}</span>
                                                    </div>
                                                </div>
                                                <div className="criteria-item">
                                                    <div className="criteria-name">Clarity</div>
                                                    <div className="criteria-value">
                                                        <div className="criteria-bar">
                                                            <div
                                                                className="criteria-fill"
                                                                style={{ width: `${(eval_item.llm_evaluation.criteria_scores?.clarity || 0) * 10}%` }}
                                                            ></div>
                                                        </div>
                                                        <span className="criteria-score">{eval_item.llm_evaluation.criteria_scores?.clarity || 0}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="eval-actions">
                                            <button
                                                onClick={() => handleAutoEvaluate(eval_item)}
                                                disabled={eval_item.evaluating}
                                                className="auto-eval-button"
                                            >
                                                {eval_item.evaluating ? (
                                                    <>
                                                        <Loader size={14} className="spin" />
                                                        <span>Evaluating...</span>
                                                    </>
                                                ) : (
                                                    <>
                                                        <Sparkles size={14} />
                                                        <span>Auto-Evaluate with AI</span>
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
