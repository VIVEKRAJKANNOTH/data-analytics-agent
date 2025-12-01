"""
Flask backend API for data analytics agent
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
import os
from werkzeug.utils import secure_filename
import pandas as pd
from dotenv import load_dotenv

from agent import AnalyticsAgent
from services import InMemorySessionService, MemoryBank
from utils.json_encoder import CustomJSONProvider

load_dotenv()

app = Flask(__name__)
app.json = CustomJSONProvider(app)
CORS(app)
swagger = Swagger(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATA_FOLDER'] = 'data'  # Persistent CSV storage
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

# Initialize session and memory services
session_service = InMemorySessionService()
memory_service = MemoryBank()

# Initialize agent with services
agent = AnalyticsAgent(
    session_service=session_service,
    memory_service=memory_service
)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """
    Health check endpoint
    ---
    responses:
      200:
        description: API status
        schema:
          type: object
          properties:
            status:
              type: string
              example: running
            service:
              type: string
              example: Data Analytics Agent API
            version:
              type: string
              example: 1.0.0
    """
    return jsonify({
        'status': 'running',
        'service': 'Data Analytics Agent API',
        'version': '1.0.0'
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Handle file upload and analysis
    ---
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: The Excel or CSV file to analyze
    responses:
      200:
        description: Analysis result
      400:
        description: Invalid file or error
      500:
        description: Server error
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload Excel or CSV file'}), 400
        
        # Save file to temporary location
        filename = secure_filename(file.filename)
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_filepath)
        
        # Load data to get stats and convert to CSV if needed
        if filename.endswith('.csv'):
            df = pd.read_csv(temp_filepath)
        else:
            result = agent.data_ingestion.load_excel(temp_filepath)
            if not result['success']:
                return jsonify(result), 400
            df = result['data']
        
        # Save as CSV to data folder for persistence
        # We use absolute path to ensure agent can find it easily
        csv_filename = filename.replace('.xlsx', '.csv').replace('.xls', '.csv')
        csv_path = os.path.abspath(os.path.join(app.config['DATA_FOLDER'], csv_filename))
        df.to_csv(csv_path, index=False)
        
        # Load into agent using FILE PATH
        agent.load_dataset(csv_path)
        
        # Clean up temp file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        
        return jsonify({
            'success': True,
            'filename': csv_filename,
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist()
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/load-from-api', methods=['POST'])
def load_from_api():
    """
    Load data from API endpoint
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            url:
              type: string
              description: The API URL to fetch data from
            method:
              type: string
              default: GET
              description: HTTP method
            headers:
              type: object
              description: Request headers
            params:
              type: object
              description: Query parameters
            json_path:
              type: string
              description: JSON path to extract data list
    responses:
      200:
        description: Analysis result
      400:
        description: Invalid request
      500:
        description: Server error
    """
    try:
        data = request.json
        url = data.get('url')
        method = data.get('method', 'GET')
        headers = data.get('headers', {})
        params = data.get('params', {})
        json_path = data.get('json_path')
        
        if not url:
            return jsonify({'success': False, 'error': 'API URL is required'}), 400
        
        # Load data from API
        result = agent.data_ingestion.load_from_api(
            url=url,
            method=method,
            headers=headers,
            params=params,
            json_path=json_path
        )
        
        if not result['success']:
            return jsonify(result), 400
        
        df = result['data']
        
        # Save as CSV for persistence
        filename = f"api_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = os.path.abspath(os.path.join(app.config['DATA_FOLDER'], filename))
        df.to_csv(csv_path, index=False)
        
        # Load into agent
        agent.load_dataset(csv_path)
        
        return jsonify({
            'success': True,
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist()
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Conversational interface for data analysis
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            message:
              type: string
              description: User question or command
    responses:
      200:
        description: Agent response with optional visualization
        schema:
          type: object
          properties:
            success:
              type: boolean
            response:
              type: string
            plot_config:
              type: object
            code:
              type: string
      400:
        description: Missing message
      500:
        description: Server error
    """
    try:
        data = request.json
        message = data.get('message')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        # Auto-generate sample data if none is loaded
        if agent.current_file_path is None:
            import numpy as np
            
            # Generate sample sales data
            np.random.seed(42)
            n_rows = 100
            
            sample_df = pd.DataFrame({
                'Date': pd.date_range('2024-01-01', periods=n_rows, freq='D'),
                'Product': np.random.choice(['Product A', 'Product B', 'Product C', 'Product D'], n_rows),
                'Region': np.random.choice(['North', 'South', 'East', 'West'], n_rows),
                'Sales': np.random.uniform(1000, 10000, n_rows).round(2),
                'Units': np.random.randint(10, 200, n_rows),
                'Customer_Rating': np.random.uniform(3.0, 5.0, n_rows).round(1)
            })
            sample_df['Price'] = (sample_df['Sales'] / sample_df['Units']).round(2)
            
            # Save sample data
            filename = "auto_sample_sales.csv"
            csv_path = os.path.abspath(os.path.join(app.config['DATA_FOLDER'], filename))
            sample_df.to_csv(csv_path, index=False)
            
            # Load sample data into agent
            agent.load_dataset(csv_path)
        
        # Call agent chat with function calling
        response = agent.chat(message)
        
        return jsonify({
            'success': True,
            'response': response.get('response', ''),
            'plot_config': response.get('plot_config'),
            'code': response.get('code'),
            'execution_log': response.get('execution_log')
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-sample-data', methods=['POST'])
def generate_sample_data():
    """
    Generate sample dataset for specific domain
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
            type: object
            properties:
                domain:
                    type: string
                    enum: [cricket, sales, finance]
                    description: Domain of data to generate
    responses:
      200:
        description: Analysis of sample data
      500:
        description: Server error
    """
    try:
        data = request.json
        domain = data.get('domain', 'sales')
        
        # Generate data using utility
        from utils.sample_data_generators import get_sample_data
        result = get_sample_data(domain)
        
        if not result['success']:
            return jsonify(result), 400
            
        df = result['data']
        
        # Save as CSV for persistence
        filename = f"sample_{domain}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = os.path.abspath(os.path.join(app.config['DATA_FOLDER'], filename))
        df.to_csv(csv_path, index=False)
        
        # Load into agent
        agent.load_dataset(csv_path)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'domain': domain
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sample-data', methods=['GET'])
def get_sample_data_legacy():
    """
    Legacy endpoint for sales sample data
    """
    try:
        from utils.sample_data_generators import get_sample_data
        result = get_sample_data('sales')
        
        if not result['success']:
            return jsonify(result), 400
            
        df = result['data']
        
        # Save as CSV for persistence
        filename = f"sample_sales_legacy_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = os.path.abspath(os.path.join(app.config['DATA_FOLDER'], filename))
        df.to_csv(csv_path, index=False)
        
        agent.load_dataset(csv_path)
        
        # Return basic info
        return jsonify({
            'success': True,
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist()
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Create upload and data folders if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)
    
    print("🚀 Data Analytics Agent API starting...")
    print("📊 Access the API at http://localhost:5000")
    print("🤖 Powered by Google Gemini AI")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
