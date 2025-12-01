import React, { useState } from 'react'
import Plot from 'react-plotly.js'
import { TrendingUp, AlertCircle, CheckCircle, Lightbulb, BarChart } from 'lucide-react'

function Dashboard({ analysisResult }) {
    const { profile, insights, ai_insights, visualizations, summary } = analysisResult

    return (
        <div className="dashboard">
            {/* Summary Section */}
            <div className="summary-section">
                <h2 className="section-title">Analysis Summary</h2>
                <div className="summary-cards">
                    <div className="summary-card">
                        <div className="card-icon">
                            <BarChart size={24} />
                        </div>
                        <div className="card-content">
                            <h3>{profile.basic_info.rows.toLocaleString()}</h3>
                            <p>Total Rows</p>
                        </div>
                    </div>
                    <div className="summary-card">
                        <div className="card-icon">
                            <TrendingUp size={24} />
                        </div>
                        <div className="card-content">
                            <h3>{profile.basic_info.columns}</h3>
                            <p>Columns</p>
                        </div>
                    </div>
                    <div className="summary-card">
                        <div className="card-icon">
                            <CheckCircle size={24} />
                        </div>
                        <div className="card-content">
                            <h3>{ai_insights?.data_quality?.score || 'N/A'}/10</h3>
                            <p>Data Quality</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* AI Insights Section */}
            {ai_insights && (
                <div className="insights-section">
                    <h2 className="section-title">
                        <Lightbulb size={24} />
                        Executive Intelligence
                    </h2>

                    {/* Executive Summary - Hero Card */}
                    {ai_insights.executive_summary && (
                        <div className="insight-hero-card">
                            <h3>Executive Summary</h3>
                            <p className="summary-text">{ai_insights.executive_summary}</p>
                        </div>
                    )}

                    <div className="insights-grid-layout">
                        {/* Key Trends */}
                        {ai_insights.key_trends && (
                            <div className="insight-block">
                                <h3>
                                    <TrendingUp size={20} />
                                    Key Trends
                                </h3>
                                <ul className="insight-list">
                                    {ai_insights.key_trends.map((trend, idx) => (
                                        <li key={idx}>{trend}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Business Implications */}
                        {ai_insights.business_implications && (
                            <div className="insight-block highlight-block">
                                <h3>
                                    <AlertCircle size={20} />
                                    Business Implications
                                </h3>
                                <ul className="insight-list">
                                    {ai_insights.business_implications.map((imp, idx) => (
                                        <li key={idx}>{imp}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Recommendations */}
                        {ai_insights.recommendations && (
                            <div className="insight-block action-block">
                                <h3>
                                    <CheckCircle size={20} />
                                    Recommended Actions
                                </h3>
                                <ul className="insight-list">
                                    {ai_insights.recommendations.map((rec, idx) => (
                                        <li key={idx}>{rec}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Statistical Insights - Moved to bottom/secondary */}
            <div className="insights-section secondary">
                <h2 className="section-title">
                    <BarChart size={24} />
                    Technical Analysis
                </h2>
                <div className="insight-pills">
                    {insights.map((insight, idx) => (
                        <div key={idx} className="insight-pill">
                            {insight}
                        </div>
                    ))}
                </div>
            </div>

            {/* Visualizations */}
            <div className="visualizations-section">
                <h2 className="section-title">Visualizations</h2>
                <div className="charts-grid">
                    {visualizations.map((viz, idx) => (
                        <div key={idx} className="chart-card">
                            <h3 className="chart-title">{viz.title}</h3>
                            <p className="chart-description">{viz.description}</p>
                            <div className="chart-container">
                                <Plot
                                    data={JSON.parse(viz.data).data}
                                    layout={{
                                        ...JSON.parse(viz.data).layout,
                                        autosize: true,
                                        margin: { t: 30, r: 20, b: 40, l: 50 }
                                    }}
                                    config={{ responsive: true, displayModeBar: false }}
                                    style={{ width: '100%', height: '100%' }}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Data Profile Details */}
            <div className="profile-section">
                <h2 className="section-title">Column Details</h2>
                <div className="columns-grid">
                    {Object.entries(profile.columns).map(([colName, colInfo]) => (
                        <div key={colName} className="column-card">
                            <h4>{colName}</h4>
                            <div className="column-details">
                                <div className="detail-row">
                                    <span className="label">Type:</span>
                                    <span className={`badge badge-${colInfo.type}`}>
                                        {colInfo.type}
                                    </span>
                                </div>
                                <div className="detail-row">
                                    <span className="label">Unique:</span>
                                    <span>{colInfo.unique_count} ({colInfo.unique_percentage.toFixed(1)}%)</span>
                                </div>
                                <div className="detail-row">
                                    <span className="label">Missing:</span>
                                    <span className={colInfo.missing_percentage > 10 ? 'text-warning' : ''}>
                                        {colInfo.missing_count} ({colInfo.missing_percentage.toFixed(1)}%)
                                    </span>
                                </div>
                                {colInfo.type === 'numeric' && (
                                    <>
                                        <div className="detail-row">
                                            <span className="label">Mean:</span>
                                            <span>{colInfo.mean?.toFixed(2) || 'N/A'}</span>
                                        </div>
                                        <div className="detail-row">
                                            <span className="label">Range:</span>
                                            <span>{colInfo.min?.toFixed(2)} - {colInfo.max?.toFixed(2)}</span>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default Dashboard
