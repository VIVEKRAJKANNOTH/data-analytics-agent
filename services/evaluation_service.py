import os
import time
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime
import google.generativeai as genai

class EvaluationService:
    def __init__(self, storage_path: str = "data/evaluations.json"):
        self.storage_path = storage_path
        self.evaluations = []
        self._load_evaluations()
        
        # Configure Gemini
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            logging.warning("GOOGLE_API_KEY or GEMINI_API_KEY not found. LLM evaluation will not work.")
            self.model = None

    def _load_evaluations(self):
        """Load evaluations from JSON file"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    self.evaluations = json.load(f)
            else:
                self.evaluations = []
        except Exception as e:
            logging.error(f"Failed to load evaluations: {str(e)}")
            self.evaluations = []

    def _save_evaluations(self):
        """Save evaluations to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(self.evaluations, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save evaluations: {str(e)}")

    def add_evaluation(self, 
                      session_id: str, 
                      message_index: int, 
                      rating: str, 
                      feedback: Optional[str] = None,
                      user_message: Optional[str] = None,
                      agent_response: Optional[str] = None) -> str:
        """
        Add a new evaluation
        
        Args:
            session_id: ID of the chat session
            message_index: Index of the message in the conversation
            rating: 'positive' or 'negative'
            feedback: Optional text feedback
            user_message: Context - what the user asked
            agent_response: Context - what the agent replied
            
        Returns:
            evaluation_id
        """
        evaluation_id = f"eval_{int(time.time())}_{len(self.evaluations)}"
        
        evaluation = {
            "id": evaluation_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "rating": rating, # 'positive' or 'negative'
            "feedback": feedback,
            "context": {
                "user_message": user_message,
                "agent_response": agent_response
            }
        }
        
        self.evaluations.append(evaluation)
        self._save_evaluations()
        
        logging.info(f"Added evaluation {evaluation_id} for session {session_id}")
        return evaluation_id

    def evaluate_with_llm(self, 
                         session_id: str, 
                         user_message: str, 
                         agent_response: str,
                         message_index: int = 0) -> Dict:
        """
        Trigger an LLM-based evaluation of an interaction
        """
        if not self.model:
            raise ValueError("LLM not configured (missing API key)")
            
        prompt = f"""
        You are an expert AI Quality Assurance Evaluator. 
        Evaluate the following interaction between a User and a Data Analytics AI Agent.
        
        User Query: "{user_message}"
        Agent Response: "{agent_response}"
        
        Evaluate based on these criteria:
        1. Correctness: Is the information accurate and relevant?
        2. Helpfulness: Did it answer the user's intent?
        3. Clarity: Is the response easy to understand?
        
        Provide your response in JSON format with the following structure:
        {{
            "score": <integer_1_to_10>,
            "reasoning": "<brief_explanation>",
            "criteria_scores": {{
                "correctness": <integer_1_to_10>,
                "helpfulness": <integer_1_to_10>,
                "clarity": <integer_1_to_10>
            }}
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            result = json.loads(text)
            
            # Store this as an evaluation
            evaluation_id = self.add_evaluation(
                session_id=session_id,
                message_index=message_index,
                rating='positive' if result['score'] >= 7 else 'negative', # Infer rating from score
                feedback=f"[LLM Auto-Eval] Score: {result['score']}/10. {result['reasoning']}",
                user_message=user_message,
                agent_response=agent_response
            )
            
            # Update the stored evaluation with full LLM details
            for eval_item in self.evaluations:
                if eval_item['id'] == evaluation_id:
                    eval_item['llm_evaluation'] = result
                    break
            self._save_evaluations()
            
            return {
                "evaluation_id": evaluation_id,
                "llm_result": result
            }
            
        except Exception as e:
            logging.error(f"LLM evaluation failed: {str(e)}")
            raise e

    def get_evaluations(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get list of evaluations, newest first"""
        # Sort by timestamp descending
        sorted_evals = sorted(self.evaluations, key=lambda x: x['timestamp'], reverse=True)
        return sorted_evals[offset:offset+limit]

    def get_summary(self) -> Dict:
        """Get summary statistics of evaluations"""
        total = len(self.evaluations)
        if total == 0:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "positive_rate": 0
            }
            
        positive = sum(1 for e in self.evaluations if e.get('rating') == 'positive')
        negative = sum(1 for e in self.evaluations if e.get('rating') == 'negative')
        
        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "positive_rate": round((positive / total) * 100, 1)
        }
