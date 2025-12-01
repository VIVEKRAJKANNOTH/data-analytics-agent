import React from 'react'
import Plot from 'react-plotly.js'
import { Loader } from 'lucide-react'

/**
 * PlotlyRenderer - Renders Plotly visualizations with animation support
 */
function PlotlyRenderer({ config, height = 500, animate = true }) {
    if (!config) {
        return null
    }

    try {
        // Ensure config has required structure
        const plotData = config.data || []
        const plotLayout = config.layout || {}
        const plotFrames = config.frames || [] // Extract frames for animations
        const plotConfig = config.config || {
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        }

        // Merge layout with defaults
        const layout = {
            autosize: true,
            height: height,
            margin: { l: 0, r: 0, t: 40, b: 0 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
                family: 'Inter, system-ui, sans-serif',
                color: '#e1e8ed'
            },
            ...plotLayout
        }

        return (
            <div className="plotly-container">
                <Plot
                    data={plotData}
                    layout={layout}
                    frames={plotFrames}
                    config={plotConfig}
                    style={{ width: '100%', height: '100%' }}
                    useResizeHandler={true}
                />
            </div>
        )
    } catch (error) {
        console.error('Error rendering Plotly chart:', error)
        return (
            <div className="plotly-error">
                <p>⚠️ Unable to render visualization</p>
                <p className="error-detail">{error.message}</p>
            </div>
        )
    }
}

export default PlotlyRenderer
