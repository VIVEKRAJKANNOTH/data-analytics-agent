"""
Core analytics agent powered by Google Gemini with function calling for code execution
"""
import google.generativeai as genai
from google.generativeai.types.generation_types import StopCandidateException
import pandas as pd
from typing import Dict, Any, List, Optional
import json
import os
from dotenv import load_dotenv
import sys
import logging
from pydantic import BaseModel, Field
from utils.observability import trace_function, measure_time, record_metric

from .data_ingestion import DataIngestion
from .analytics_engine import AnalyticsEngine
from .visualization import VisualizationEngine
from .tools import get_execute_python_tool, execute_python_code


load_dotenv()


class TimeoutException(Exception):
    """Raised when code execution times out"""
    pass


class AgentResponse(BaseModel):
    """Structured response from the Analytics Agent"""
    response: str = Field(..., description="The natural language answer to the user's question")
    plot_config: Optional[Dict[str, Any]] = Field(None, description="Plotly configuration object")
    code: Optional[str] = Field(None, description="The Python code executed to generate the result")
    execution_log: Optional[Dict[str, Any]] = Field(None, description="Execution metadata for debugging")


class AnalyticsAgent:
    """AI-powered data analytics agent using Gemini with function calling"""
    
    def __init__(self, api_key: Optional[str] = None, session_service=None, memory_service=None):
        """Initialize the agent with Gemini API"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key not provided")
        
        genai.configure(api_key=self.api_key)
        
        logging.info("AnalyticsAgent initialized", extra={
            "extra_fields": {
                "model": "gemini-2.5-flash",
                "has_session_service": session_service is not None,
                "has_memory_service": memory_service is not None
            }
        })
        
        # Get tool definitions
        execute_python_tool = get_execute_python_tool()
        
        # Initialize model with function calling
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            tools=[execute_python_tool],
            generation_config={
                'temperature': 0.5, # Lower temperature for more deterministic code generation
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 8192,
            }
        )
        
        # Initialize components
        self.data_ingestion = DataIngestion()
        self.analytics_engine = AnalyticsEngine()
        self.viz_engine = VisualizationEngine()
        
        # Session and memory services
        self.session_service = session_service
        self.memory_service = memory_service
        
        # Current dataset path
        self.current_file_path = None
        
        # Chat session (for backward compatibility - default session)
        self.chat_session = None
        
        # Session-specific chat sessions
        self._session_chats: Dict[str, Any] = {}
    

    
    def _sanitize_for_json(self, obj: Any) -> Any:
        """
        Recursively convert numpy types and other non-JSON serializable objects 
        to standard Python types for Proto serialization.
        """
        import numpy as np
        from datetime import datetime, date
        
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(v) for v in obj]
        elif isinstance(obj, (pd.Timestamp, datetime, date)):
            # Convert pandas Timestamp and datetime objects to ISO format strings
            return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
        elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.bool_)):
            return bool(obj)
        elif isinstance(obj, (np.ndarray,)):
            return self._sanitize_for_json(obj.tolist())
        elif pd.isna(obj):
            return None
        elif hasattr(obj, 'to_plotly_json'):
            return self._sanitize_for_json(obj.to_plotly_json())
        elif hasattr(obj, 'to_dict'):
            return self._sanitize_for_json(obj.to_dict())
        return obj

    def generate_initial_summary(self) -> Dict[str, Any]:
        """
        Generate an initial summary of the dataset with domain detection and visualization
        """
        if self.current_file_path is None:
            return {"response": "No data loaded"}
            
        prompt = "Provide a brief summary of this dataset with key statistics and create an appropriate visualization."
        
        return self.chat(prompt)

    @trace_function("prepare_context")
    def _prepare_context(self) -> str:
        """Prepare dataset context for LLM - Minimal Context (Pointer + 1 Row)"""
        if self.current_file_path is None:
            return "No dataset loaded"
        
        try:
            # Read ONLY the first row to give schema context
            df = pd.read_csv(self.current_file_path, nrows=1)
            
            context_parts = []
            context_parts.append(f"Filename: {self.current_file_path}")
            context_parts.append(f"Columns: {', '.join(df.columns.tolist())}")
            
            # Sample data - Just 1 row
            sample = df.to_dict('records')
            context_parts.append(f"\nFirst row sample (Schema):\n{json.dumps(sample, default=str, indent=2)}")
            
            return "\n".join(context_parts)
        except Exception as e:
            return f"Error reading file context: {str(e)}"
    
    @trace_function("get_user_preferences")
    def _get_user_preferences(self) -> str:
        """Retrieve user preferences from memory bank and format as context"""
        if not self.memory_service:
            return ""
        
        try:
            # Get user preference memories
            preferences = self.memory_service.get_memories(category='user_preference', limit=20)
            
            if not preferences:
                return ""
            
            # Format as context
            pref_lines = ["\n=== USER PREFERENCES (from memory) ==="]
            for pref in preferences:
                pref_lines.append(f"- {pref.content}")
            pref_lines.append("=== END USER PREFERENCES ===\n")
            
            return "\n".join(pref_lines)
        except Exception as e:
            print(f"Error retrieving preferences: {e}")
            return ""
    
    @trace_function("extract_user_preferences")
    def _extract_user_preferences(self, user_message: str, agent_response: str) -> None:
        """Use LLM to extract user preferences from the conversation and save to memory"""
        if not self.memory_service:
            return
        
        try:
            # Use a lightweight model call to detect preferences
            extraction_prompt = f"""Analyze this conversation exchange and identify if the user expressed any personal preferences, favorites, or likes.

User message: "{user_message}"
Agent response: "{agent_response[:300]}..."

Extract ONLY clear user preferences in this format:
- If user says "X is my favorite Y", extract: "Favorite Y: X"
- If user says "I prefer X", extract: "Prefers: X"
- If user says "I like X", extract: "Likes: X"

Rules:
1. Only extract explicit preferences from the USER's message (not the agent's response)
2. Be specific (e.g., "Favorite player: Virat Kohli" not just "Likes cricket")
3. If no clear preference is expressed, respond with "NONE"
4. Return one preference per line
5. Keep it concise and factual

Extracted preferences:"""
            
            # Quick model call for extraction
            extraction_model = genai.GenerativeModel('gemini-2.5-flash')
            response = extraction_model.generate_content(extraction_prompt)
            
            if response and response.text:
                extracted = response.text.strip()
                
                # Check if preferences were found
                if extracted and extracted != "NONE" and len(extracted) > 0:
                    # Split by lines and save each preference
                    preferences = [p.strip() for p in extracted.split('\n') if p.strip() and p.strip() != 'NONE']
                    
                    for pref in preferences:
                        if pref and len(pref) > 5:  # Minimum length check
                            self.memory_service.add_memory(
                                content=pref,
                                category='user_preference',
                                metadata={
                                    'source': 'auto_extracted',
                                    'user_message': user_message[:200]
                                }
                            )
                            print(f"📝 Saved user preference: {pref}")
                            logging.info(f"Saved user preference", extra={"extra_fields": {"preference": pref}})
        
        except Exception as e:
            print(f"Error extracting preferences: {e}")

    @trace_function("agent_chat")
    @measure_time("agent_chat_duration")
    def chat(self, user_message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Chat interface with function calling for code execution
        
        Args:
            user_message: User's question or request
            session_id: Optional session ID for session-aware chat
            
        Returns:
            Response with text and optional visualization (AgentResponse dict)
        """
        if self.current_file_path is None:
            return AgentResponse(response="Please upload a dataset first to start analyzing data.").model_dump()
        
        # Handle session-aware chat
        if session_id and self.session_service:
            # Add user message to session history
            self.session_service.add_message(session_id, 'user', user_message)
            
            # Use session-specific chat or create new one
            if session_id not in self._session_chats:
                self._session_chats[session_id] = None
            
            chat_session = self._session_chats[session_id]
        else:
            # Use default chat session for backward compatibility
            chat_session = self.chat_session
        
        # Start or continue chat session
        if chat_session is None:
            # Prepare initial context
            context = self._prepare_context()
            
            # Retrieve user preferences from memory
            user_preferences = self._get_user_preferences()
            
            system_instruction = f"""You are an expert Data Analytics AI Agent. 

Dataset Pointer:
{context}
{user_preferences}

CRITICAL INSTRUCTIONS:
1. Minimal Context: You ONLY have the filename and the first row of data. You do NOT see the full dataset.
2. Execute to See: To answer ANY question about the data, you MUST write and execute Python code using execute_python_code.
3. Read the File: Your Python code MUST start by reading the file: df = pd.read_csv(filename). Note: pd (pandas) is already imported for you.
4. ALWAYS Generate Visualizations: For EVERY question, you MUST create an interactive Plotly visualization. Set the plot_config variable.
5. Code Formatting: Do NOT use backslash line continuations. Use implicit line continuation inside brackets/parentheses instead.

Available in execution environment:
- pd (pandas library - already imported)
- json (for JSON operations)
- filename (the CSV file path)

MANDATORY: Every response MUST include:
1. Computed result/answer (set result variable)
2. Interactive Plotly visualization (set plot_config variable)

VISUALIZATION SELECTION GUIDE:
Choose the BEST chart type for the data and question:

2D Charts (use when showing 1-2 dimensions):
- scatter: Relationships between 2 variables, correlations
- bar: Comparisons across categories
- line: Trends over time
- pie: Part-to-whole relationships (use sparingly)
- histogram: Distribution of a single variable
- box: Statistical distribution with quartiles
- violin: Distribution density
- heatmap: Matrix of values with color intensity
- sunburst: Hierarchical part-to-whole
- treemap: Hierarchical rectangles

3D Charts (use when showing 3+ dimensions):
- scatter3d: 3+ variable relationships
- surface: Continuous 3D surface
- mesh3d: 3D mesh objects

When answering:
1. THINK about what chart type best conveys the insight (2D vs 3D)
2. WRITE Python code that reads the CSV, computes the answer, and creates the plot_config
3. EXECUTE the code using execute_python_code
4. EXPLAIN the findings clearly
5. USE USER PREFERENCES: If the user asks about "my favorite X" or "my preferred Y", check the USER PREFERENCES section above and use that information

Remember: 
- Use 2D charts for clarity when possible
- Use 3D only when showing 3+ dimensions
- ALWAYS add interactivity (hover, zoom, pan)
- Use template: plotly_dark for consistent theming
- NEVER skip the visualization"""

            chat_session = self.model.start_chat(history=[])
            
            # Save chat session to appropriate location
            if session_id and self.session_service:
                self._session_chats[session_id] = chat_session
            else:
                self.chat_session = chat_session
            
            # Send system context with exception handling
            try:
                logging.info("Sending system instruction to LLM")
                response = chat_session.send_message(system_instruction)
            except StopCandidateException as e:
                error_msg = f"RECITATION error during system initialization: {e}"
                print(f"❌ {error_msg}")
                return AgentResponse(
                    response="I encountered an error initializing the analysis session. Please try uploading your data again.",
                    plot_config=None,
                    code=None,
                    execution_log={
                        "tool_calls": [],
                        "errors": [error_msg],
                        "warnings": []
                    }
                ).model_dump()
        
        # Send user message with retry logic for RECITATION errors
        max_retries = 2
        retry_count = 0
        response = None
        last_error = None
        
        while retry_count <= max_retries:
            try:
                # Modify prompt on retry to avoid RECITATION
                if retry_count > 0:
                    modified_message = f"Analyze this dataset and provide insights: {user_message}"
                    print(f"🔄 Retry {retry_count}/{max_retries} with modified prompt")
                    response = chat_session.send_message(modified_message)
                else:
                    logging.info("Sending user message to LLM", extra={"extra_fields": {"message_length": len(user_message)}})
                    record_metric("counter", "llm_requests_total", 1, {"type": "chat"})
                    response = chat_session.send_message(user_message)
                
                # Success - break out of retry loop
                break
                
            except StopCandidateException as e:
                last_error = e
                finish_reason = e.finish_reason if hasattr(e, 'finish_reason') else 'unknown'
                
                error_messages = {
                    2: "Response exceeded token limit",
                    3: "Content filtered by safety settings",
                    4: "Potential copyright content detected",
                    10: "Potential copyright content detected"
                }
                error_type = error_messages.get(finish_reason, f"Unknown error (finish_reason: {finish_reason})")
                
                print(f"❌ GEMINI API ERROR (attempt {retry_count + 1}): {error_type}")
                logging.error(f"Gemini API error: {error_type}", extra={"extra_fields": {"finish_reason": finish_reason}})
                record_metric("counter", "errors_total", 1, {"type": "gemini_api", "reason": str(finish_reason)})
                
                # If this was the last retry, return error
                if retry_count >= max_retries:
                    return AgentResponse(
                        response=f"I'm having trouble generating a response. This might be due to content restrictions. Please try rephrasing your question or asking about specific aspects of the data.",
                        plot_config=None,
                        code=None,
                        execution_log={
                            "tool_calls": [],
                            "errors": [f"StopCandidateException after {max_retries + 1} attempts: {error_type}"],
                            "warnings": ["Consider rephrasing the question"]
                        }
                    ).model_dump()
                
                retry_count += 1
            
            except Exception as e:
                # Handle other unexpected exceptions
                error_msg = f"Unexpected error: {str(e)}"
                print(f"❌ {error_msg}")
                return AgentResponse(
                    response="I encountered an unexpected error. Please try again.",
                    plot_config=None,
                    code=None,
                    execution_log={
                        "tool_calls": [],
                        "errors": [error_msg],
                        "warnings": []
                    }
                ).model_dump()
        
        # Additional check for finish_reason after successful response
        if response and response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason
            
            # finish_reason: 1 = STOP (normal), others are errors
            if finish_reason != 1:
                # Log token usage if available
                if hasattr(candidate, 'token_count'):
                    record_metric("counter", "llm_tokens_total", candidate.token_count, {"type": "response"})
                
                error_messages = {
                    2: "MAX_TOKENS - Response exceeded token limit",
                    3: "SAFETY - Content filtered by safety settings",
                    4: "RECITATION - Potential copyright content detected",
                    5: "OTHER - Unknown error",
                    10: "RECITATION - The model detected potential copyrighted content."
                }
                error_msg = error_messages.get(finish_reason, f"Unknown finish_reason: {finish_reason}")
                
                print(f"⚠️  GEMINI API WARNING: {error_msg}")
                # Continue execution but log the warning
        
        # Process function calls
        final_response = ""
        final_plot_config = None
        executed_code = None
        execution_log = {
            "tool_calls": [],
            "errors": [],
            "warnings": []
        }
        
        while response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            
            # Check if it's a function call
            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                
                if function_call.name == "execute_python_code":
                    # Extract parameters
                    code = function_call.args.get("code", "")
                    description = function_call.args.get("description", "")
                    filename = function_call.args.get("filename", self.current_file_path)
                    executed_code = code
                    
                    # Log the tool call
                    print(f"\n{'='*60}")
                    print(f"TOOL EXECUTION: execute_python_code")
                    print(f"Description: {description}")
                    print(f"Filename: {filename}")
                    print(f"Code:\n{code}")
                    print(f"{'='*60}\n")
                    
                    logging.info("Executing tool", extra={
                        "extra_fields": {
                            "tool": "execute_python_code",
                            "description": description
                        }
                    })
                    
                    # Execute the code
                    exec_result = execute_python_code(code, description, filename)
                    
                    # Log execution result
                    print(f"Execution Result:")
                    print(f"  Success: {exec_result.get('success')}")
                    if exec_result.get('success'):
                        print(f"  Result: {exec_result.get('result')}")
                        print(f"  Plot Config: {'Present' if exec_result.get('plot_config') else 'None'}")
                        if exec_result.get('output'):
                            print(f"  Output: {exec_result.get('output')}")
                    else:
                        print(f"  Error: {exec_result.get('error')}")
                    print(f"{'='*60}\n")
                    
                    # Track execution in log
                    execution_log["tool_calls"].append({
                        "tool": "execute_python_code",
                        "description": description,
                        "success": exec_result.get("success"),
                        "has_result": exec_result.get("result") is not None,
                        "has_plot_config": exec_result.get("plot_config") is not None,
                        "error": exec_result.get("error") if not exec_result.get("success") else None
                    })
                    
                    # Check for missing plot_config
                    if exec_result.get("success") and not exec_result.get("plot_config"):
                        warning = "Code executed successfully but no plot_config was generated"
                        execution_log["warnings"].append(warning)
                        print(f"⚠️  WARNING: {warning}")
                    
                    # Sanitize result for Proto serialization (handle numpy types)
                    exec_result = self._sanitize_for_json(exec_result)
                    
                    # Send result back to model using dictionary format
                    # We need to wrap it in a structure that the library understands
                    from google.ai.generativelanguage import Part, FunctionResponse
                    
                    # Construct the function response part using Proto classes
                    response_part = Part(
                        function_response=FunctionResponse(
                            name='execute_python_code',
                            response=exec_result
                        )
                    )
                    
                    response = chat_session.send_message([response_part])
                    
                    # Extract plot config if available
                    if exec_result.get("success") and exec_result.get("plot_config"):
                        final_plot_config = exec_result["plot_config"]
                
            elif hasattr(part, 'text') and part.text:
                # This is the final text response
                final_response = part.text
                break
            else:
                break
        
        # Final summary log
        print(f"\n{'='*60}")
        print(f"FINAL RESPONSE SUMMARY:")
        print(f"  Tool Calls: {len(execution_log['tool_calls'])}")
        print(f"  Warnings: {len(execution_log['warnings'])}")
        print(f"  Errors: {len(execution_log['errors'])}")
        print(f"  Plot Config: {'Present' if final_plot_config else 'MISSING'}")
        print(f"  Code Executed: {'Yes' if executed_code else 'No'}")
        print(f"{'='*60}\n")
        
        # Construct structured response using Pydantic
        agent_response = AgentResponse(
            response=final_response or "Analysis complete.",
            plot_config=final_plot_config,
            code=executed_code,
            execution_log=execution_log
        )
        
        # Add assistant response to session history if using sessions
        if session_id and self.session_service:
            self.session_service.add_message(
                session_id, 
                'assistant', 
                final_response or "Analysis complete.",
                metadata={
                    'has_plot': final_plot_config is not None,
                    'has_code': executed_code is not None
                }
            )
            
            # Auto-save interesting insights to memory bank
            if self.memory_service and final_response and len(final_response) > 50:
                # Simple heuristic: save responses that seem informative
                if any(keyword in final_response.lower() for keyword in ['insight', 'trend', 'shows', 'indicates', 'analysis']):
                    self.memory_service.add_memory(
                        content=final_response[:500],  # Limit length
                        category='insight',
                        metadata={
                            'session_id': session_id,
                            'dataset': self.current_file_path,
                            'user_question': user_message[:200]
                        }
                    )
                
        # Extract and save user preferences from this conversation turn (works for all chats)
        print(f"\n🎯 [DEBUG] About to call preference extraction. memory_service exists: {self.memory_service is not None}")
        if self.memory_service:
            print("🎯 [DEBUG] Calling _extract_user_preferences now...")
            self._extract_user_preferences(user_message, final_response or "")
        else:
            print("🎯 [DEBUG] Skipping preference extraction - no memory service")
        
        return agent_response.model_dump()
    
    def load_dataset(self, file_path: str):
        """Load a new dataset by path"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        self.current_file_path = file_path
        logging.info(f"Dataset loaded: {file_path}")
        self.chat_session = None  # Reset chat session
    
    # Legacy methods for compatibility
    def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Legacy method - now just loads data"""
        return {
            'success': True,
            'summary': f"Dataset loaded: {len(df)} rows, {len(df.columns)} columns"
        }
