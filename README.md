# AI Data Analytics Agent 🤖📊

An intelligent, production-ready data analytics and visualization platform powered by **Google Gemini AI**. Upload your data and get instant insights, automated dashboards, conversational analysis, and LLM-based evaluation - all with a beautiful, modern interface.

## ✨ Key Features

### 🔄 **Multi-Source Data Ingestion**
- Upload Excel/CSV files with drag-and-drop interface
- Connect to RESTful API endpoints with custom headers and parameters
- Auto-generate sample datasets for testing (Sales, Finance, Cricket domains)

### 🤖 **AI-Powered Analysis**
- Google Gemini provides senior-level data analyst insights
- Natural language conversations about your data
- Intelligent preference detection and long-term memory
- Auto-evaluation of agent responses with LLM feedback

### 📊 **Advanced Analytics & Visualization**
- Automatic dashboard generation with interactive Plotly charts
- Statistical profiling and correlation analysis
- Pattern detection and outlier identification
- Multiple visualization types: heatmaps, distributions, comparisons, time series

### 💾 **Session & Memory Management**
- Persistent conversation sessions with history
- Long-term memory bank for user preferences
- Context-aware responses across sessions

### 🎯 **Admin Dashboard**
- Evaluate agent interactions with thumbs up/down ratings
- LLM-based auto-evaluation with scoring and reasoning
- Track conversation history and quality metrics

### 📈 **Observability & Monitoring**
- Structured JSON logging with python-json-logger
- OpenTelemetry tracing for distributed monitoring
- Metrics collection for API performance
- Comprehensive error tracking and debugging

### 🎨 **Premium UI/UX**
- Modern dark theme with glassmorphism effects
- Smooth animations and micro-interactions
- Responsive design for all screen sizes
- Professional typography and color schemes

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Node.js 16+** ([Download](https://nodejs.org/))
- **pip** (Python package manager)
- **npm** (Node package manager)

### 1. Get Your Google Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### 2. Clone or Download the Project

```bash
# If using git
git clone <your-repo-url>
cd data-analytics-agent

# Or download and extract the ZIP file
cd data-analytics-agent
```

### 3. Backend Setup

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo "GEMINI_API_KEY=your_api_key_here" > .env
echo "LOG_LEVEL=INFO" >> .env
```

**⚠️ Important:** Replace `your_api_key_here` with your actual Gemini API key!

### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Return to root directory
cd ..
```

### 5. Run the Application

You'll need **two terminal windows**:

**Terminal 1 - Backend:**
```bash
# Make sure you're in the project root directory
python app.py
```

The backend API will start at `http://localhost:5000`

You should see:
```
 * Running on http://127.0.0.1:5000
 * Swagger UI available at http://127.0.0.1:5000/apidocs
```

**Terminal 2 - Frontend:**
```bash
# Navigate to frontend directory
cd frontend

# Start development server
npm run dev
```

The frontend will start at `http://localhost:5173`

You should see:
```
  VITE v7.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 6. Access the Application

Open your browser and navigate to:
- **Main App:** [http://localhost:5173](http://localhost:5173)
- **Admin Dashboard:** [http://localhost:5173/admin](http://localhost:5173/admin)
- **API Documentation (Swagger):** [http://localhost:5000/apidocs](http://localhost:5000/apidocs)

## 📖 Usage Guide

### 📤 Upload Data

#### Option 1: File Upload
1. Click the **"Upload File"** tab on the home page
2. Drag and drop your file or click to browse
3. Supported formats: `.xlsx`, `.xls`, `.csv`
4. The dashboard will automatically generate with insights

#### Option 2: API Endpoint
1. Click the **"API Endpoint"** tab
2. Enter your API URL (e.g., `https://api.example.com/data`)
3. Configure:
   - HTTP Method (GET/POST)
   - Headers (e.g., Authorization tokens)
   - Query parameters
   - JSON path to extract data array
4. Click **"Load from API"**

#### Option 3: Sample Data
1. Click **"Try Sample Data"** button
2. Choose a domain (Sales, Finance, Cricket)
3. Explore with pre-generated data

### 📊 View Dashboard

Once data is loaded, you'll see:

- **📈 Summary Cards**: Key metrics (rows, columns, data quality score)
- **🧠 AI Insights**: 
  - Executive summary
  - Key trends and patterns
  - Business implications
  - Actionable recommendations
- **📉 Statistical Insights**: Automated correlation and pattern detection
- **📊 Visualizations**: Interactive charts you can zoom, pan, and download
- **🔍 Column Details**: Detailed statistics for each data column

### 💬 Chat with AI

1. Navigate to the **"Ask AI"** tab
2. Start a conversation about your data:
   - "What are the top 5 products by sales?"
   - "Show me a trend analysis for the last quarter"
   - "Are there any outliers in the customer ratings?"
   - "Create a bar chart comparing regions"
3. The AI will generate responses, code, and visualizations
4. All visualizations are interactive (hover, zoom, download)

### 🎓 Session Management

Sessions allow you to maintain conversation context:

```bash
# Create a new session
POST /api/session/create

# Chat with session context
POST /api/chat-session
{
  "session_id": "your-session-id",
  "message": "Your question here"
}

# Retrieve session history
GET /api/session/{session_id}
```

### 🧠 Memory Bank

The agent remembers your preferences across sessions:

- Automatically detects preferences from conversations
- Stores them in the long-term memory bank
- Retrieves relevant preferences for future queries
- Categories: `user_preference`, `general`, `insight`, etc.

### 👨‍💼 Admin Dashboard

Access at [http://localhost:5173/admin](http://localhost:5173/admin)

Features:
- View all conversation interactions
- Rate responses (👍/👎)
- Auto-evaluate with LLM (scores 1-5 with reasoning)
- Track evaluation metrics
- Monitor conversation quality

## 🏗️ Architecture

### Backend Structure

```
data-analytics-agent/
├── agent/
│   ├── __init__.py
│   ├── analytics_agent.py      # Core AI agent with Gemini integration
│   ├── analytics_engine.py     # Statistical analysis & pattern detection
│   ├── data_ingestion.py       # Excel, CSV & API data loading
│   ├── visualization.py        # Plotly chart generation
│   └── tools.py                # Code execution sandbox
│
├── services/
│   ├── __init__.py
│   ├── session_service.py      # In-memory session management
│   ├── memory_service.py       # Long-term memory bank
│   └── evaluation_service.py   # Response evaluation & LLM scoring
│
├── utils/
│   ├── observability.py        # Logging, tracing, metrics
│   ├── json_encoder.py         # Custom JSON serialization
│   └── sample_data_generators.py  # Domain-specific data generators
│
├── data/                       # Uploaded datasets (CSV storage)
├── uploads/                    # Temporary upload folder
├── app.py                      # Flask REST API server
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables (API keys)
```

### Frontend Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── DataUpload.jsx          # File upload & API integration
│   │   ├── Dashboard.jsx           # Analytics dashboard
│   │   ├── ChatInterface.jsx       # Conversational AI
│   │   ├── AdminDashboard.jsx      # Admin evaluation panel
│   │   └── ...other components
│   ├── App.jsx                     # Main application & routing
│   ├── App.css                     # Global styles
│   └── main.jsx                    # React entry point
│
├── public/                         # Static assets
├── package.json                    # Node dependencies
└── vite.config.ts                  # Vite configuration
```

## 🔌 API Endpoints

### Data Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload Excel/CSV file |
| `POST` | `/api/load-from-api` | Load data from API endpoint |
| `POST` | `/api/generate-sample-data` | Generate domain-specific sample data |
| `GET` | `/api/sample-data` | Legacy sample data endpoint |

### Conversational AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Chat without session |
| `POST` | `/api/chat-session` | Chat with session context |

### Session Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/session/create` | Create a new session |
| `GET` | `/api/session/{id}` | Get session details |
| `DELETE` | `/api/session/{id}` | Delete a session |

### Memory Bank
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/memory` | Get memories (with filters) |
| `POST` | `/api/memory` | Add a new memory |
| `DELETE` | `/api/memory/{id}` | Delete a memory |
| `GET` | `/api/memory/summary` | Get memory statistics |

### Evaluation
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/evaluate` | Submit manual evaluation |
| `POST` | `/api/evaluate/llm` | Auto-evaluate with LLM |
| `GET` | `/api/evaluations` | Get all evaluations |
| `GET` | `/api/evaluations/summary` | Get evaluation statistics |

### Utilities
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/apidocs` | Swagger API documentation |

## 🎯 Technology Stack

### Backend
- **Framework:** Flask 3.0
- **AI/LLM:** Google Generative AI (Gemini 2.5 Flash)
- **Data Processing:** pandas, numpy, scipy
- **Visualization:** Plotly
- **Observability:** OpenTelemetry, python-json-logger
- **API Documentation:** Flasgger (Swagger)

### Frontend
- **Framework:** React 18
- **Build Tool:** Vite
- **HTTP Client:** Axios
- **Routing:** React Router DOM
- **Visualization:** Plotly.js, react-plotly.js
- **UI Library:** Lucide React (icons)
- **Markdown:** react-markdown, remark-gfm
- **Language:** TypeScript

### AI & ML
- **Model:** Google Gemini 1.5 Flash
- **Capabilities:** 
  - Natural language understanding
  - Code generation (Python)
  - Data analysis
  - Preference extraction
  - Response evaluation

## 🧪 Testing

### Test the Backend API

```bash
# Using curl
curl http://localhost:5000/

# Using the provided test scripts
bash test_session_memory.sh
bash test_preference_memory.sh
bash quick_test.sh
```

### Test Files
- `test_session_memory.sh` - Test session management
- `test_preference_memory.sh` - Test preference detection
- `test_admin_evaluation.py` - Test evaluation service

### API Testing with Swagger

Visit [http://localhost:5000/apidocs](http://localhost:5000/apidocs) to:
- Test all endpoints interactively
- View request/response schemas
- Generate sample requests

## 📊 Sample Use Cases

### 1. Sales Analysis
```
Upload: sales_data.csv
Ask: "What are the top 5 products by revenue?"
Ask: "Show me sales trends over time"
Ask: "Which regions have declining performance?"
```

### 2. Financial Analysis
```
Generate: Sample Finance Data
Ask: "Calculate the average transaction value"
Ask: "Show me expense distribution by category"
Ask: "Are there any unusual transactions?"
```

### 3. Cricket Analytics
```
Generate: Sample Cricket Data
Ask: "Who has the highest batting average?"
Ask: "Show me runs scored by match"
Ask: "Compare bowler economy rates"
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
MAX_CONTENT_LENGTH=52428800       # 50MB in bytes
```

### Frontend Configuration

Edit `frontend/vite.config.ts` to change:
- Server port (default: 5173)
- Proxy settings
- Build options

### Backend Configuration

Edit `app.py` to change:
- Upload folder location
- Max file size
- Allowed file extensions
- CORS settings

## 🐛 Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError: No module named 'flask'`
```bash
# Solution: Ensure virtual environment is activated and dependencies are installed
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Problem:** `Error: GEMINI_API_KEY not found`
```bash
# Solution: Check your .env file exists and contains valid API key
cat .env
# Should show: GEMINI_API_KEY=your_key_here
```

**Problem:** Port 5000 already in use
```bash
# Solution: Find and kill the process using port 5000
# On macOS/Linux:
lsof -ti:5000 | xargs kill -9
# On Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Frontend Issues

**Problem:** `Cannot GET /` or blank page
```bash
# Solution: Ensure backend is running first, then restart frontend
# Terminal 1: python app.py
# Terminal 2: cd frontend && npm run dev
```

**Problem:** CORS errors in browser console
```bash
# Solution: Ensure flask-cors is installed and CORS(app) is in app.py
pip install flask-cors
```

**Problem:** `Module not found` errors
```bash
# Solution: Reinstall node modules
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### API Issues

**Problem:** "RECITATION" errors from Gemini
```bash
# Solution: This happens when Gemini detects potential copyright content
# The agent will retry automatically or rephrase the prompt
```

**Problem:** File upload fails
```bash
# Solution: Check file size (<50MB) and format (.xlsx, .xls, .csv)
# Ensure uploads/ and data/ directories exist
mkdir -p uploads data
```

## 📚 Logs and Debugging

### Backend Logs
```bash
# View real-time logs
tail -f backend.log

# View structured JSON logs
cat backend.log | python -m json.tool
```

### Frontend Debugging
- Open browser DevTools (F12)
- Check Console tab for JavaScript errors
- Check Network tab for API request/response details

## 🚀 Production Deployment

### Backend

```bash
# Use a production WSGI server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Or use environment variable
export FLASK_ENV=production
python app.py
```

### Frontend

```bash
cd frontend

# Build for production
npm run build

# Serve the dist folder with a static server
npm install -g serve
serve -s dist -p 5173

# Or deploy to Vercel/Netlify/etc.
```

### Environment Variables for Production

```bash
GEMINI_API_KEY=your_production_key
LOG_LEVEL=WARNING
FLASK_ENV=production
```

## 🔐 Security Considerations

- ✅ **Never commit `.env` file** - Already in `.gitignore`
- ✅ **Validate file uploads** - Max size and type restrictions in place
- ✅ **Sanitize file names** - Using `werkzeug.utils.secure_filename`
- ⚠️ **Code execution** - Python code is executed in a sandboxed environment
- ⚠️ **API keys** - Store in environment variables, not in code
- ⚠️ **CORS** - Currently allows all origins (restrict in production)

## 🤝 Contributing

Contributions are welcome! Here's how you can extend the project:

### Add New Analysis Functions
```python
# In agent/analytics_engine.py
def new_analysis_function(df):
    # Your analysis logic
    return results
```

### Create Custom Visualizations
```python
# In agent/visualization.py
def create_new_chart(df, config):
    fig = go.Figure()
    # Your chart logic
    return fig.to_dict()
```

### Enhance AI Prompts
```python
# In agent/analytics_agent.py
# Modify system_prompt or add new prompt templates
```

### Build New UI Components
```jsx
// In frontend/src/components/
export const NewComponent = () => {
    // Your React component
}
```

## 📈 Future Enhancements

- [ ] Multi-file analysis and data merging
- [ ] Custom dashboard builder with drag-and-drop
- [ ] Export to PDF/PowerPoint
- [ ] Real-time data streaming
- [ ] Collaborative features (shared sessions)
- [ ] Advanced statistical tests (t-tests, ANOVA)
- [ ] Machine learning predictions (forecasting, clustering)
- [ ] Data cleaning and transformation UI
- [ ] User authentication and authorization
- [ ] Database persistence (PostgreSQL/MongoDB)
- [ ] Scheduled reports and alerts
- [ ] Custom SQL query interface
- [ ] Integration with BI tools (Tableau, Power BI)

## 📄 License

MIT License - Feel free to use and modify for your projects!

```
MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- **Google Gemini AI** - For powerful language models and generative AI capabilities
- **Plotly** - For beautiful, interactive visualizations
- **React & Vite** - For modern frontend development
- **Flask** - For simple yet powerful backend API
- **OpenTelemetry** - For observability and monitoring
- **The Open Source Community** - For amazing tools and libraries

## 📧 Support

For questions, issues, or suggestions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review API docs at `/apidocs`
3. Check backend logs: `tail -f backend.log`
4. Open an issue on GitHub with:
   - Description of the problem
   - Steps to reproduce
   - Error messages/logs
   - Your environment (OS, Python version, Node version)

---

**Built with ❤️ using Google Gemini AI**

*Transform your data into insights with the power of AI!*
