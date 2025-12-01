"""
Session management service for maintaining conversation state
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
import uuid
import threading


@dataclass
class Session:
    """Represents a user session with conversation history"""
    session_id: str
    created_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        return data


class InMemorySessionService:
    """
    In-memory session management service
    
    Manages user sessions with conversation history and context.
    Note: Sessions are stored in memory and will be lost on server restart.
    """
    
    def __init__(self):
        """Initialize the session service"""
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.Lock()
    
    def create_session(self, session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Session:
        """
        Create a new session
        
        Args:
            session_id: Optional session ID (generates UUID if not provided)
            metadata: Optional metadata to attach to session
            
        Returns:
            Created session object
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        with self._lock:
            if session_id in self._sessions:
                raise ValueError(f"Session {session_id} already exists")
            
            now = datetime.now()
            session = Session(
                session_id=session_id,
                created_at=now,
                last_activity=now,
                metadata=metadata or {},
                conversation_history=[],
                context={}
            )
            
            self._sessions[session_id] = session
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object if found, None otherwise
        """
        with self._lock:
            return self._sessions.get(session_id)
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """
        Update session attributes
        
        Args:
            session_id: Session identifier
            **kwargs: Attributes to update (metadata, context, etc.)
            
        Returns:
            True if session was updated, False if not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            # Update last activity
            session.last_activity = datetime.now()
            
            # Update allowed attributes
            if 'metadata' in kwargs:
                session.metadata.update(kwargs['metadata'])
            if 'context' in kwargs:
                session.context.update(kwargs['context'])
            
            return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a message to the conversation history
        
        Args:
            session_id: Session identifier
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional message metadata
            
        Returns:
            True if message was added, False if session not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            message = {
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
            
            if metadata:
                message['metadata'] = metadata
            
            session.conversation_history.append(message)
            session.last_activity = datetime.now()
            
            return True
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages to return (most recent)
            
        Returns:
            List of messages, or empty list if session not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return []
            
            history = session.conversation_history
            if limit:
                return history[-limit:]
            return history.copy()
    
    def list_sessions(self) -> List[str]:
        """
        List all active session IDs
        
        Returns:
            List of session IDs
        """
        with self._lock:
            return list(self._sessions.keys())
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Remove sessions older than specified age
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of sessions removed
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        removed_count = 0
        
        with self._lock:
            sessions_to_remove = [
                sid for sid, session in self._sessions.items()
                if session.last_activity < cutoff_time
            ]
            
            for sid in sessions_to_remove:
                del self._sessions[sid]
                removed_count += 1
        
        return removed_count
