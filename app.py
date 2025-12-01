"""
Flask backend API for data analytics agent
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
import os
import time
import logging
from werkzeug.utils import secure_filename
import pandas as pd
from dotenv import load_dotenv

from agent import AnalyticsAgent
from services import InMemorySessionService, MemoryBank, EvaluationService
from utils.json_encoder import CustomJSONProvider
from utils.observability import (
    initialize_observability,
    get_tracer,
    record_metric,
    trace_function
)

load_dotenv()

# Initialize observability
observability = initialize_observability(
    service_name="data-analytics-agent",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="backend.log"
)
tracer = get_tracer()

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
evaluation_service = EvaluationService()

# Initialize agent with services
agent = AnalyticsAgent(
    session_service=session_service,
    memory_service=memory_service
)

logging.info("Flask app initialized with observability")


# Request/Response logging middleware
@app.before_request
def log_request():
    """Log incoming requests"""
    request.start_time = time.time()
    logging.info(f"Incoming request", extra={
        "extra_fields": {
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr
        }
    })


@app.after_request
def log_response(response):
    """Log responses and record metrics"""
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        
        logging.info(f"Request completed", extra={
            "extra_fields": {
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_seconds": duration
            }
        })
        
        # Record metrics
        record_metric(
            "counter",
            "api_requests_total",
            1,
            {"method": request.method, "endpoint": request.path, "status": str(response.status_code)}
        )
        record_metric(
            "histogram",
            "api_request_duration_seconds",
            duration,
            {"method": request.method, "endpoint": request.path}
        )
        
        # Record errors
        if response.status_code >= 400:
            record_metric(
                "counter",
                "errors_total",
                1,
                {"endpoint": request.path, "status": str(response.status_code)}
            )
    
    return response


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
        logging.info("File upload request received")
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
        logging.error(f"File upload failed: {str(e)}", exc_info=True)
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
        logging.info("API data load request received")
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
        logging.error(f"API data load failed: {str(e)}", exc_info=True)
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
        logging.info("Chat request received", extra={"extra_fields": {"has_dataset": agent.current_file_path is not None}})
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
        logging.error(f"Chat request failed: {str(e)}", exc_info=True)
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


# ========== SESSION MANAGEMENT ENDPOINTS ==========

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """
    Create a new session
    ---
    responses:
      200:
        description: New session created
        schema:
          type: object
          properties:
            success:
              type: boolean
            session_id:
              type: string
    """
    try:
        logging.info("Creating new session")
        data = request.json or {}
        metadata = data.get('metadata', {})
        
        session = session_service.create_session(metadata=metadata)
        
        return jsonify({
            'success': True,
            'session_id': session.session_id,
            'created_at': session.created_at.isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """
    Get session information and conversation history
    ---
    parameters:
      - name: session_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Session information
      404:
        description: Session not found
    """
    try:
        session = session_service.get_session(session_id)
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        return jsonify({
            'success': True,
            'session': session.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    Delete a session
    ---
    parameters:
      - name: session_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Session deleted
      404:
        description: Session not found
    """
    try:
        success = session_service.delete_session(session_id)
        if not success:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        return jsonify({'success': True, 'message': 'Session deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/chat-session', methods=['POST'])
def chat_session():
    """
    Chat with session context
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            session_id:
              type: string
              description: Session ID
            message:
              type: string
              description: User message
    responses:
      200:
        description: Agent response
      400:
        description: Missing parameters
    """
    try:
        logging.info("Session chat request received")
        data = request.json
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'session_id is required'}), 400
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        # Check if session exists
        session = session_service.get_session(session_id)
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
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
            filename = f"session_{session_id}_sample.csv"
            csv_path = os.path.abspath(os.path.join(app.config['DATA_FOLDER'], filename))
            sample_df.to_csv(csv_path, index=False)
            
            # Load sample data into agent
            agent.load_dataset(csv_path)
            
            # Store in session context
            session_service.update_session(session_id, context={'dataset_path': csv_path})
        
        # Call agent chat with session ID
        response = agent.chat(message, session_id=session_id)
        
        return jsonify({
            'success': True,
            'response': response.get('response', ''),
            'plot_config': response.get('plot_config'),
            'code': response.get('code'),
            'execution_log': response.get('execution_log')
        })
    
    except Exception as e:
        logging.error(f"Session chat failed: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== MEMORY BANK ENDPOINTS ==========

@app.route('/api/memory', methods=['GET'])
def get_memories():
    """
    Get memories from the memory bank
    ---
    parameters:
      - name: category
        in: query
        type: string
        required: false
      - name: limit
        in: query
        type: integer
        default: 10
    responses:
      200:
        description: List of memories
    """
    try:
        category = request.args.get('category')
        limit = int(request.args.get('limit', 10))
        
        memories = memory_service.get_memories(category=category, limit=limit)
        
        return jsonify({
            'success': True,
            'memories': [m.to_dict() for m in memories],
            'count': len(memories)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/memory', methods=['POST'])
def add_memory():
    """
    Add a memory to the memory bank
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            content:
              type: string
            category:
              type: string
              default: general
            metadata:
              type: object
    responses:
      200:
        description: Memory added
    """
    try:
        data = request.json
        content = data.get('content')
        category = data.get('category', 'general')
        metadata = data.get('metadata', {})
        
        if not content:
            return jsonify({'success': False, 'error': 'Content is required'}), 400
        
        memory_id = memory_service.add_memory(
            content=content,
            category=category,
            metadata=metadata
        )
        
        return jsonify({
            'success': True,
            'memory_id': memory_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/memory/<memory_id>', methods=['DELETE'])
def delete_memory(memory_id):
    """
    Delete a memory
    ---
    parameters:
      - name: memory_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Memory deleted
      404:
        description: Memory not found
    """
    try:
        success = memory_service.delete_memory(memory_id)
        if not success:
            return jsonify({'success': False, 'error': 'Memory not found'}), 404
        
        return jsonify({'success': True, 'message': 'Memory deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/memory/summary', methods=['GET'])
def get_memory_summary():
    """
    Get memory bank summary
    ---
    responses:
      200:
        description: Memory summary
    """
    try:
        summary = memory_service.get_summary()
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== EVALUATION ENDPOINTS ==========

@app.route('/api/evaluate', methods=['POST'])
def add_evaluation():
    """
    Submit an evaluation for an agent response
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            session_id:
              type: string
            message_index:
              type: integer
            rating:
              type: string
              enum: [positive, negative]
            feedback:
              type: string
            user_message:
              type: string
            agent_response:
              type: string
    responses:
      200:
        description: Evaluation submitted
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        rating = data.get('rating')
        
        if not session_id or not rating:
            return jsonify({'success': False, 'error': 'session_id and rating are required'}), 400
            
        evaluation_id = evaluation_service.add_evaluation(
            session_id=session_id,
            message_index=data.get('message_index', 0),
            rating=rating,
            feedback=data.get('feedback'),
            user_message=data.get('user_message'),
            agent_response=data.get('agent_response')
        )
        
        return jsonify({
            'success': True,
            'evaluation_id': evaluation_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/evaluations', methods=['GET'])
def get_evaluations():
    """
    Get list of evaluations (Admin)
    ---
    parameters:
      - name: limit
        in: query
        type: integer
        default: 50
    responses:
      200:
        description: List of evaluations
    """
    try:
        limit = int(request.args.get('limit', 50))
        evaluations = evaluation_service.get_evaluations(limit=limit)
        summary = evaluation_service.get_summary()
        
        return jsonify({
            'success': True,
            'evaluations': evaluations,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/evaluate/llm', methods=['POST'])
def evaluate_with_llm():
    """
    Trigger LLM-based evaluation
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            session_id:
              type: string
            message_index:
              type: integer
            user_message:
              type: string
            agent_response:
              type: string
    responses:
      200:
        description: Evaluation result
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        user_message = data.get('user_message')
        agent_response = data.get('agent_response')
        
        if not session_id or not user_message or not agent_response:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        result = evaluation_service.evaluate_with_llm(
            session_id=session_id,
            message_index=data.get('message_index', 0),
            user_message=user_message,
            agent_response=agent_response
        )
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Create upload and data folders if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)
    
    logging.info("Starting Data Analytics Agent API")
    print("🚀 Data Analytics Agent API starting...")
    print("📊 Access the API at http://localhost:5000")
    print("🤖 Powered by Google Gemini AI")
    print("📝 Observability: Logging, Tracing, and Metrics enabled")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
