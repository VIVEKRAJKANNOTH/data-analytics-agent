"""
Visualization generation using Plotly
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
import json


class VisualizationEngine:
    """Generates interactive visualizations"""
    
    def create_chart(self, 
                     df: pd.DataFrame, 
                     chart_type: str, 
                     x_col: Optional[str] = None,
                     y_col: Optional[str] = None,
                     color_col: Optional[str] = None,
                     title: str = "") -> str:
        """
        Create Plotly chart
        
        Args:
            df: DataFrame with data
            chart_type: Type of chart (line, bar, scatter, pie, heatmap, box, histogram)
            x_col: X-axis column
            y_col: Y-axis column
            color_col: Color grouping column
            title: Chart title
            
        Returns:
            JSON string of Plotly figure
        """
        try:
            fig = None
            
            if chart_type == 'line':
                fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title)
            
            elif chart_type == 'bar':
                fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
            
            elif chart_type == 'scatter':
                fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title,
                               trendline="ols" if len(df) > 10 else None)
            
            elif chart_type == 'pie':
                fig = px.pie(df, names=x_col, values=y_col, title=title)
            
            elif chart_type == 'heatmap':
                # For correlation heatmap
                numeric_df = df.select_dtypes(include=['number'])
                corr = numeric_df.corr()
                fig = px.imshow(corr, 
                              text_auto=True,
                              aspect="auto",
                              title=title or "Correlation Heatmap",
                              color_continuous_scale='RdBu_r')
            
            elif chart_type == 'box':
                fig = px.box(df, x=x_col, y=y_col, color=color_col, title=title)
            
            elif chart_type == 'histogram':
                fig = px.histogram(df, x=x_col, color=color_col, title=title)
            
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
            
            # Ensure axis labels are present (use column names as defaults)
            if fig and hasattr(fig, 'update_layout'):
                layout_updates = {
                    'template': 'plotly_dark',
                    'plot_bgcolor': 'rgba(0,0,0,0)',
                    'paper_bgcolor': 'rgba(0,0,0,0)',
                    'font': dict(family="Inter, sans-serif"),
                    'hovermode': 'x unified',
                    'showlegend': True
                }
                
                # Add axis labels if they don't exist
                if chart_type not in ['pie', 'heatmap']:  # These don't use standard axes
                    if x_col and 'xaxis' not in (fig.layout or {}):
                        layout_updates['xaxis'] = {'title': x_col.replace('_', ' ').title()}
                    if y_col and 'yaxis' not in (fig.layout or {}):
                        layout_updates['yaxis'] = {'title': y_col.replace('_', ' ').title()}
                
                # Ensure title exists
                if not title or title == "":
                    if chart_type == 'heatmap':
                        layout_updates['title'] = "Correlation Heatmap"
                    elif x_col and y_col:
                        layout_updates['title'] = f"{y_col.replace('_', ' ').title()} vs {x_col.replace('_', ' ').title()}"
                    elif x_col:
                        layout_updates['title'] = f"{chart_type.title()} of {x_col.replace('_', ' ').title()}"
                
                fig.update_layout(**layout_updates)
            
            return fig.to_json()
        
        except Exception as e:
            return json.dumps({'error': str(e)})
    
    def auto_generate_visualizations(self, df: pd.DataFrame, profile: Dict) -> List[Dict[str, Any]]:
        """
        Automatically generate relevant visualizations based on data
        
        Args:
            df: DataFrame to visualize
            profile: Data profile from analytics engine
            
        Returns:
            List of chart specifications
        """
        charts = []
        
        numeric_cols = [col for col, info in profile['columns'].items() 
                       if info['type'] == 'numeric']
        categorical_cols = [col for col, info in profile['columns'].items() 
                          if info['type'] == 'categorical' and info['unique_count'] < 20]
        
        # 1. Correlation heatmap if multiple numeric columns
        if len(numeric_cols) > 1:
            chart_json = self.create_chart(
                df, 
                'heatmap',
                title='Feature Correlations'
            )
            charts.append({
                'type': 'heatmap',
                'title': 'Feature Correlations',
                'data': chart_json,
                'description': 'Shows relationships between numeric variables'
            })
        
        # 2. Distribution plots for key numeric columns
        for col in numeric_cols[:3]:  # Top 3 numeric columns
            chart_json = self.create_chart(
                df,
                'histogram',
                x_col=col,
                title=f'Distribution of {col}'
            )
            charts.append({
                'type': 'histogram',
                'title': f'Distribution of {col}',
                'data': chart_json,
                'description': f'Frequency distribution of {col}'
            })
        
        # 3. Categorical analysis
        if categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # Bar chart for categorical vs numeric
            agg_df = df.groupby(cat_col)[num_col].mean().reset_index()
            chart_json = self.create_chart(
                agg_df,
                'bar',
                x_col=cat_col,
                y_col=num_col,
                title=f'Average {num_col} by {cat_col}'
            )
            charts.append({
                'type': 'bar',
                'title': f'Average {num_col} by {cat_col}',
                'data': chart_json,
                'description': f'Comparison of {num_col} across different {cat_col}'
            })
            
            # Box plot for distribution by category
            chart_json = self.create_chart(
                df,
                'box',
                x_col=cat_col,
                y_col=num_col,
                title=f'{num_col} Distribution by {cat_col}'
            )
            charts.append({
                'type': 'box',
                'title': f'{num_col} Distribution by {cat_col}',
                'data': chart_json,
                'description': f'Shows spread and outliers of {num_col} for each {cat_col}'
            })
        
        # 4. Scatter plot for top 2 numeric columns
        if len(numeric_cols) >= 2:
            chart_json = self.create_chart(
                df,
                'scatter',
                x_col=numeric_cols[0],
                y_col=numeric_cols[1],
                color_col=categorical_cols[0] if categorical_cols else None,
                title=f'{numeric_cols[1]} vs {numeric_cols[0]}'
            )
            charts.append({
                'type': 'scatter',
                'title': f'{numeric_cols[1]} vs {numeric_cols[0]}',
                'data': chart_json,
                'description': f'Relationship between {numeric_cols[0]} and {numeric_cols[1]}'
            })
        
        # 5. Pie chart for categorical distribution
        if categorical_cols:
            cat_col = categorical_cols[0]
            value_counts = df[cat_col].value_counts().reset_index()
            value_counts.columns = [cat_col, 'count']
            
            chart_json = self.create_chart(
                value_counts,
                'pie',
                x_col=cat_col,
                y_col='count',
                title=f'Distribution of {cat_col}'
            )
            charts.append({
                'type': 'pie',
                'title': f'Distribution of {cat_col}',
                'data': chart_json,
                'description': f'Proportion of different {cat_col} categories'
            })
        
        return charts
