"""
Memory bank service for long-term memory storage
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
import uuid
import threading


@dataclass
class Memory:
    """Represents a stored memory"""
    memory_id: str
    content: str
    category: str
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.last_accessed:
            data['last_accessed'] = self.last_accessed.isoformat()
        return data


class MemoryBank:
    """
    Long-term memory storage service
    
    Stores memories across sessions for insights, preferences, and context.
    Note: Memories are stored in memory and will be lost on server restart.
    """
    
    def __init__(self):
        """Initialize the memory bank"""
        self._memories: Dict[str, Memory] = {}
        self._lock = threading.Lock()
    
    def add_memory(
        self, 
        content: str, 
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a new memory
        
        Args:
            content: The memory content
            category: Memory category (e.g., 'insight', 'user_preference', 'dataset_info')
            metadata: Optional additional context
            
        Returns:
            Generated memory ID
        """
        memory_id = str(uuid.uuid4())
        
        with self._lock:
            memory = Memory(
                memory_id=memory_id,
                content=content,
                category=category,
                created_at=datetime.now(),
                metadata=metadata or {},
                access_count=0,
                last_accessed=None
            )
            
            self._memories[memory_id] = memory
        
        return memory_id
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Retrieve a specific memory
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory object if found, None otherwise
        """
        with self._lock:
            memory = self._memories.get(memory_id)
            if memory:
                memory.access_count += 1
                memory.last_accessed = datetime.now()
            return memory
    
    def get_memories(
        self, 
        category: Optional[str] = None,
        limit: int = 10,
        sort_by: str = "created_at"
    ) -> List[Memory]:
        """
        Retrieve memories, optionally filtered by category
        
        Args:
            category: Optional category filter
            limit: Maximum number of memories to return
            sort_by: Sort field ('created_at', 'access_count', 'last_accessed')
            
        Returns:
            List of memory objects
        """
        with self._lock:
            memories = list(self._memories.values())
            
            # Filter by category if specified
            if category:
                memories = [m for m in memories if m.category == category]
            
            # Sort
            if sort_by == "access_count":
                memories.sort(key=lambda m: m.access_count, reverse=True)
            elif sort_by == "last_accessed":
                memories.sort(
                    key=lambda m: m.last_accessed if m.last_accessed else datetime.min,
                    reverse=True
                )
            else:  # created_at
                memories.sort(key=lambda m: m.created_at, reverse=True)
            
            # Limit results
            return memories[:limit]
    
    def search_memories(self, query: str, limit: int = 5) -> List[Memory]:
        """
        Search memories by content (simple text search)
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        query_lower = query.lower()
        
        with self._lock:
            matches = [
                memory for memory in self._memories.values()
                if query_lower in memory.content.lower() or query_lower in memory.category.lower()
            ]
            
            # Sort by relevance (access count as proxy) and recency
            matches.sort(
                key=lambda m: (m.access_count, m.created_at),
                reverse=True
            )
            
            # Update access stats for returned memories
            for memory in matches[:limit]:
                memory.access_count += 1
                memory.last_accessed = datetime.now()
            
            return matches[:limit]
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Remove a memory
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if memory was deleted, False if not found
        """
        with self._lock:
            if memory_id in self._memories:
                del self._memories[memory_id]
                return True
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all stored memories
        
        Returns:
            Dictionary with memory statistics and categories
        """
        with self._lock:
            memories = list(self._memories.values())
            
            # Count by category
            categories = {}
            for memory in memories:
                categories[memory.category] = categories.get(memory.category, 0) + 1
            
            # Get most accessed
            most_accessed = sorted(
                memories,
                key=lambda m: m.access_count,
                reverse=True
            )[:5]
            
            return {
                'total_memories': len(memories),
                'categories': categories,
                'most_accessed': [
                    {
                        'memory_id': m.memory_id,
                        'content': m.content[:100] + '...' if len(m.content) > 100 else m.content,
                        'category': m.category,
                        'access_count': m.access_count
                    }
                    for m in most_accessed
                ]
            }
    
    def clear_all(self) -> int:
        """
        Clear all memories (use with caution)
        
        Returns:
            Number of memories removed
        """
        with self._lock:
            count = len(self._memories)
            self._memories.clear()
            return count
