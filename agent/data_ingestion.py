"""
Data ingestion module for Excel files and API endpoints
"""
import pandas as pd
import requests
from typing import Dict, Any, Optional, List
import json


class DataIngestion:
    """Handles data loading from various sources"""
    
    def load_excel(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Load data from Excel file
        
        Args:
            file_path: Path to Excel file
            sheet_name: Specific sheet to load (None = all sheets)
            
        Returns:
            Dictionary with data and metadata
        """
        try:
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                return {
                    'success': True,
                    'data': df,
                    'sheets': [sheet_name],
                    'shape': df.shape,
                    'columns': df.columns.tolist(),
                    'dtypes': df.dtypes.to_dict()
                }
            else:
                # Load all sheets
                excel_file = pd.ExcelFile(file_path)
                sheets = {}
                for sheet in excel_file.sheet_names:
                    sheets[sheet] = pd.read_excel(file_path, sheet_name=sheet)
                
                # Use first sheet as primary
                primary_df = sheets[excel_file.sheet_names[0]]
                
                return {
                    'success': True,
                    'data': primary_df,
                    'all_sheets': sheets,
                    'sheets': excel_file.sheet_names,
                    'shape': primary_df.shape,
                    'columns': primary_df.columns.tolist(),
                    'dtypes': primary_df.dtypes.to_dict()
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def load_from_api(self, 
                      url: str, 
                      method: str = 'GET',
                      headers: Optional[Dict] = None,
                      params: Optional[Dict] = None,
                      auth: Optional[tuple] = None,
                      json_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load data from API endpoint
        
        Args:
            url: API endpoint URL
            method: HTTP method (GET/POST)
            headers: Request headers
            params: Query parameters
            auth: Authentication tuple (username, password)
            json_path: Path to data in JSON response (e.g., 'data.results')
            
        Returns:
            Dictionary with data and metadata
        """
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, auth=auth)
            else:
                response = requests.post(url, headers=headers, json=params, auth=auth)
            
            response.raise_for_status()
            
            data = response.json()
            
            # Navigate JSON path if provided
            if json_path:
                for key in json_path.split('.'):
                    data = data[key]
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                return {
                    'success': False,
                    'error': 'Unsupported data format from API'
                }
            
            return {
                'success': True,
                'data': df,
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': df.dtypes.to_dict(),
                'source': 'api',
                'url': url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate and provide quality metrics for dataset
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Validation metrics
        """
        return {
            'row_count': len(df),
            'column_count': len(df.columns),
            'missing_values': df.isnull().sum().to_dict(),
            'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict(),
            'duplicate_rows': df.duplicated().sum(),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'dtypes': df.dtypes.to_dict()
        }
