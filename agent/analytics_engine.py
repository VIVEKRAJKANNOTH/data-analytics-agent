"""
Analytics engine for data profiling and insight generation
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from scipy import stats


class AnalyticsEngine:
    """Performs data analysis and generates insights"""
    
    def profile_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive data profile
        
        Args:
            df: DataFrame to profile
            
        Returns:
            Statistical profile and metadata
        """
        profile = {
            'basic_info': {
                'rows': len(df),
                'columns': len(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
            },
            'columns': {},
            'missing_data': {},
            'correlations': None,
            'statistical_summary': {}
        }
        
        # Analyze each column
        for col in df.columns:
            col_data = df[col]
            col_profile = {
                'dtype': str(col_data.dtype),
                'missing_count': col_data.isnull().sum(),
                'missing_percentage': (col_data.isnull().sum() / len(df)) * 100,
                'unique_count': col_data.nunique(),
                'unique_percentage': (col_data.nunique() / len(df)) * 100
            }
            
            # Numeric column analysis
            if pd.api.types.is_numeric_dtype(col_data):
                col_profile.update({
                    'type': 'numeric',
                    'min': float(col_data.min()) if not col_data.isnull().all() else None,
                    'max': float(col_data.max()) if not col_data.isnull().all() else None,
                    'mean': float(col_data.mean()) if not col_data.isnull().all() else None,
                    'median': float(col_data.median()) if not col_data.isnull().all() else None,
                    'std': float(col_data.std()) if not col_data.isnull().all() else None,
                    'q25': float(col_data.quantile(0.25)) if not col_data.isnull().all() else None,
                    'q75': float(col_data.quantile(0.75)) if not col_data.isnull().all() else None,
                    'zeros_count': int((col_data == 0).sum()),
                    'negative_count': int((col_data < 0).sum())
                })
            # Categorical column analysis
            else:
                col_profile.update({
                    'type': 'categorical',
                    'top_values': {str(k): v for k, v in col_data.value_counts().head(10).to_dict().items()}
                })
            
            profile['columns'][col] = col_profile
        
        # Calculate correlations for numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            corr_matrix = numeric_df.corr()
            profile['correlations'] = corr_matrix.to_dict()
        
        # Overall statistical summary
        profile['statistical_summary'] = df.describe().to_dict()
        
        return profile
    
    def detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect patterns, trends, and anomalies
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Detected patterns and insights
        """
        patterns = {
            'trends': [],
            'outliers': {},
            'distributions': {},
            'seasonality': []
        }
        
        # Detect outliers in numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                # Using IQR method
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                outliers = col_data[(col_data < Q1 - 1.5 * IQR) | (col_data > Q3 + 1.5 * IQR)]
                
                if len(outliers) > 0:
                    patterns['outliers'][col] = {
                        'count': len(outliers),
                        'percentage': (len(outliers) / len(col_data)) * 100,
                        'values': outliers.tolist()[:10]  # First 10 outliers
                    }
                
                # Distribution analysis
                try:
                    skewness = float(stats.skew(col_data))
                    kurtosis = float(stats.kurtosis(col_data))
                    patterns['distributions'][col] = {
                        'skewness': skewness,
                        'kurtosis': kurtosis,
                        'interpretation': self._interpret_distribution(skewness, kurtosis)
                    }
                except:
                    pass
        
        return patterns
    
    def _interpret_distribution(self, skewness: float, kurtosis: float) -> str:
        """Interpret distribution characteristics"""
        interp = []
        
        if abs(skewness) < 0.5:
            interp.append("approximately symmetric")
        elif skewness > 0:
            interp.append("right-skewed (positively skewed)")
        else:
            interp.append("left-skewed (negatively skewed)")
        
        if abs(kurtosis) < 0.5:
            interp.append("normal-like tails")
        elif kurtosis > 0:
            interp.append("heavy-tailed")
        else:
            interp.append("light-tailed")
        
        return ", ".join(interp)
    
    def generate_insights(self, df: pd.DataFrame, profile: Dict, patterns: Dict) -> List[str]:
        """
        Generate business-level insights from analysis
        
        Args:
            df: Original DataFrame
            profile: Data profile
            patterns: Detected patterns
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Data quality insights
        high_missing = [col for col, info in profile['columns'].items() 
                       if info['missing_percentage'] > 10]
        if high_missing:
            insights.append(f"⚠️ Data Quality: {len(high_missing)} columns have >10% missing values: {', '.join(high_missing[:3])}")
        
        # Correlation insights
        if profile['correlations']:
            strong_corrs = []
            corr_dict = profile['correlations']
            for col1 in corr_dict:
                for col2 in corr_dict[col1]:
                    if col1 < col2:  # Avoid duplicates
                        corr_val = corr_dict[col1][col2]
                        if abs(corr_val) > 0.7 and abs(corr_val) < 1.0:
                            strong_corrs.append((col1, col2, corr_val))
            
            if strong_corrs:
                top_corr = strong_corrs[0]
                insights.append(f"🔗 Strong Correlation: '{top_corr[0]}' and '{top_corr[1]}' are highly correlated ({top_corr[2]:.2f})")
        
        # Outlier insights
        if patterns['outliers']:
            total_outliers = sum(info['count'] for info in patterns['outliers'].values())
            insights.append(f"📊 Outliers Detected: Found {total_outliers} outliers across {len(patterns['outliers'])} columns")
        
        # Distribution insights
        if patterns['distributions']:
            skewed_cols = [col for col, info in patterns['distributions'].items() 
                          if abs(info['skewness']) > 1]
            if skewed_cols:
                insights.append(f"📈 Distribution: {len(skewed_cols)} columns show significant skewness")
        
        # Cardinality insights
        high_card = [col for col, info in profile['columns'].items() 
                    if info['type'] == 'categorical' and info['unique_percentage'] > 50]
        if high_card:
            insights.append(f"🎯 High Cardinality: {', '.join(high_card[:2])} have many unique values (potential identifiers)")
        
        return insights
