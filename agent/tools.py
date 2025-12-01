"""
Tool definitions for the Analytics Agent
"""
import pandas as pd
import json
import os
import sys
from io import StringIO
import threading
import logging
from typing import Dict, Any, List, Optional
from utils.observability import trace_function, measure_time, record_metric

def get_execute_python_tool():
    """
    Returns the execute_python_code tool definition for Gemini function calling
    """
    return {
        'function_declarations': [{
            'name': 'execute_python_code',
            'description': '''Execute Python code for data analysis and visualization.

IMPORTANT REQUIREMENTS:
1. Always start by reading the data: df = pd.read_csv(filename)
2. For date/time columns: Convert to strings using .astype(str) or .dt.strftime() before adding to plot_config
3. Set "result" variable with your computed answer
4. Set "plot_config" variable with Plotly chart configuration (REQUIRED for every analysis)
5. Available: pd (pandas), json, filename variable
6. Do NOT use backslash line continuations - use implicit continuation in brackets/parentheses

CHART TYPE SELECTION:
- Bar chart: Comparisons across categories
- Line chart: Trends over time or sequences
- Scatter plot: Correlations between 2 variables
- Histogram: Distribution of single variable
- Box plot: Statistical distribution with quartiles
- Heatmap: 2D correlation/intensity matrix
- Scatter3d: 3+ dimensional relationships
- Pie/Sunburst: Part-to-whole relationships

PLOT_CONFIG EXAMPLES:

Bar Chart (for comparisons):
{
  "data": [{
    "type": "bar",
    "x": df['category'].tolist(),
    "y": df['value'].tolist(),
    "marker": {
      "color": df['value'].tolist(),
      "colorscale": "Viridis",
      "colorbar": {"title": "Value"}
    },
    "text": df['value'].tolist(),
    "textposition": "auto",
    "hovertemplate": "<b>%{x}</b><br>Value: %{y}<extra></extra>"
  }],
  "layout": {
    "title": {"text": "Your Title", "font": {"size": 20}},
    "xaxis": {"title": "Category Name", "automargin": True},
    "yaxis": {"title": "Value Metric", "automargin": True},
    "template": "plotly_dark",
    "hovermode": "closest",
    "showlegend": False,
    "margin": {"l": 60, "r": 40, "t": 80, "b": 60},
    "height": 500
  }
}

Line Chart (for trends):
{
  "data": [{
    "type": "scatter",
    "mode": "lines+markers",
    "x": df['date'].tolist(),
    "y": df['value'].tolist(),
    "line": {"width": 3, "color": "#1da1f2"},
    "marker": {"size": 8},
    "hovertemplate": "%{x}<br>Value: %{y}<extra></extra>"
  }],
  "layout": {
    "title": {"text": "Trend Over Time", "font": {"size": 20}},
    "xaxis": {"title": "Date/Time", "automargin": True},
    "yaxis": {"title": "Value", "automargin": True},
    "template": "plotly_dark",
    "hovermode": "x unified",
    "margin": {"l": 60, "r": 40, "t": 80, "b": 60}
  }
}

Scatter Plot (for correlations):
{
  "data": [{
    "type": "scatter",
    "mode": "markers",
    "x": df['var1'].tolist(),
    "y": df['var2'].tolist(),
    "marker": {
      "size": 10,
      "color": df['var3'].tolist(),
      "colorscale": "Viridis",
      "showscale": True,
      "colorbar": {"title": "Color Scale"}
    },
    "hovertemplate": "X: %{x}<br>Y: %{y}<extra></extra>"
  }],
  "layout": {
    "title": {"text": "Correlation Analysis", "font": {"size": 20}},
    "xaxis": {"title": "Variable 1 Name", "automargin": True},
    "yaxis": {"title": "Variable 2 Name", "automargin": True},
    "template": "plotly_dark",
    "margin": {"l": 60, "r": 40, "t": 80, "b": 60}
  }
}

3D Scatter (for multi-dimensional):
{
  "data": [{
    "type": "scatter3d",
    "mode": "markers",
    "x": df['col1'].tolist(),
    "y": df['col2'].tolist(),
    "z": df['col3'].tolist(),
    "marker": {
      "size": 6,
      "color": df['col4'].tolist(),
      "colorscale": "Viridis",
      "opacity": 0.8,
      "colorbar": {"title": "Color"}
    },
    "hovertemplate": "X: %{x}<br>Y: %{y}<br>Z: %{z}<extra></extra>"
  }],
  "layout": {
    "title": {"text": "3D Visualization", "font": {"size": 20}},
    "scene": {
      "xaxis": {"title": "X Axis Label"},
      "yaxis": {"title": "Y Axis Label"},
      "zaxis": {"title": "Z Axis Label"}
    },
    "template": "plotly_dark",
    "margin": {"l": 0, "r": 0, "t": 80, "b": 0}
  }
}

STYLING REQUIREMENTS (MANDATORY):
- Always use "template": "plotly_dark" for consistent theming
- Include descriptive titles with {"text": "...", "font": {"size": 20}}
- **CRITICAL: ALWAYS include axis titles** for both xaxis and yaxis with descriptive labels
  * Use meaningful names, not just "X" or "Y"
  * Example: "Revenue (USD)", "Number of Customers", "Date", etc.
- Use proper margins to prevent toolbar overlap: {"l": 60, "r": 40, "t": 80, "b": 60}
  * l (left): Space for y-axis labels (60px minimum)
  * r (right): Space for right side (40px)
  * t (top): Space for title and toolbar (80px minimum to prevent overlap)
  * b (bottom): Space for x-axis labels (60px minimum)
- For x-axis: Set "automargin": True to ensure labels fit properly
- For y-axis: Set "automargin": True to ensure labels fit properly
- Use hovertemplate for custom hover info
- Add colorscales for visual appeal (Viridis, Blues, Reds, etc.)
- Set appropriate height (default: 500)
- Enable showlegend only when multiple traces exist

EXAMPLE WITH PROPER MARGINS:
{
  "layout": {
    "title": {"text": "Your Title", "font": {"size": 20}},
    "xaxis": {"title": "X Label", "automargin": True},
    "yaxis": {"title": "Y Label", "automargin": True},
    "template": "plotly_dark",
    "margin": {"l": 60, "r": 40, "t": 80, "b": 60},
    "height": 500
  }
}''',
            'parameters': {
                'type_': 'OBJECT',
                'properties': {
                    'code': {
                        'type_': 'STRING',
                        'description': 'Python code to execute. Must read CSV, compute result, and create plot_config.'
                    },
                    'description': {
                        'type_': 'STRING',
                        'description': 'Brief description of what this code does'
                    },
                    'filename': {
                        'type_': 'STRING',
                        'description': 'The absolute path to the CSV file to analyze.'
                    }
                },
                'required': ['code', 'description', 'filename']
            }
        }]
    }

def execute_python_code(code: str, description: str, filename: str) -> Dict[str, Any]:
    """
    Execute Python code in a sandboxed environment
    
    Args:
        code: Python code to execute
        description: Description of what the code does
        filename: Path to the CSV file
        
    Returns:
        Dictionary with execution results
    """
    logging.info(f"Executing Python code: {description}")
    record_metric("counter", "code_executions_total", 1, {"type": "python"})
    
    if not os.path.exists(filename):
        logging.error(f"File not found: {filename}")
        record_metric("counter", "errors_total", 1, {"type": "file_not_found"})
        return {
            "success": False,
            "error": f"File not found: {filename}"
        }
    
    # Restricted globals for safety - pandas is already imported
    restricted_globals = {
        'pd': pd,
        'json': json,
        '__builtins__': {
            'range': range,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'sorted': sorted,
            'enumerate': enumerate,
            'zip': zip,
            'print': print,
            'isinstance': isinstance,
            'type': type,
            'True': True,
            'False': False,
            'None': None,
            '__import__': __import__
        }
    }
    
    local_vars = {'filename': filename}
    
    # Thread-safe execution with timeout
    result_container = {'success': False, 'error': 'Execution timed out'}
    
    @trace_function("execute_code_thread")
    @measure_time("code_execution_duration")
    def execute_code():
        try:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                exec(code, restricted_globals, local_vars)
                output = sys.stdout.getvalue()
            finally:
                sys.stdout = old_stdout
            
            # Extract results
            result = local_vars.get('result', None)
            plot_config = local_vars.get('plot_config', None)
            
            result_container['success'] = True
            result_container['result'] = result
            result_container['plot_config'] = plot_config
            result_container['output'] = output
            result_container['description'] = description
            
        except SyntaxError as e:
            import traceback
            error_msg = f"Syntax Error at line {e.lineno}: {e.msg}\n{traceback.format_exc()}"
            result_container['success'] = False
            result_container['error'] = error_msg
            print(f"❌ SYNTAX ERROR in generated code:\n{error_msg}")
            logging.error(f"Syntax error in generated code", extra={"extra_fields": {"error": str(e), "line": e.lineno}})
            record_metric("counter", "errors_total", 1, {"type": "syntax_error"})
            
        except Exception as e:
            import traceback
            error_msg = f"Execution error: {str(e)}\n{traceback.format_exc()}"
            result_container['success'] = False
            result_container['error'] = error_msg
            print(f"❌ EXECUTION ERROR:\n{error_msg}")
            logging.error(f"Execution error", extra={"extra_fields": {"error": str(e)}})
            record_metric("counter", "errors_total", 1, {"type": "execution_error"})
    
    # Run in thread with timeout
    thread = threading.Thread(target=execute_code)
    thread.daemon = True
    thread.start()
    thread.join(timeout=30)
    
    if thread.is_alive():
        # Thread is still running, timeout occurred
        logging.error("Code execution timed out")
        record_metric("counter", "errors_total", 1, {"type": "timeout"})
        return {
            "success": False,
            "error": "Code execution timed out (30s limit)"
        }
    
    return result_container
