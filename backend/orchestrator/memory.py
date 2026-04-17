"""Memory systems for LangChain agents."""
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime
from langchain.memory import ConversationBufferMemory


logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Conversation memory for individual agents.
    
    Wraps LangChain's ConversationBufferMemory to provide context retention
    within each agent's execution. Each agent maintains its own conversation
    history during its reasoning loop.
    
    Features:
    - Stores conversation history (human inputs and AI responses)
    - Provides context for multi-turn agent reasoning
    - Automatically formats memory for agent prompts
    - Supports memory clearing between pipeline runs
    
    Usage:
        memory = ConversationMemory(agent_name="planner")
        memory.add_message("human", "Create an outline for AI presentation")
        memory.add_message("ai", "I'll research the topic first...")
        context = memory.get_context()
    """
    
    def __init__(self, agent_name: str, memory_key: str = "chat_history"):
        """
        Initialize conversation memory for an agent.
        
        Args:
            agent_name: Name of the agent (for logging)
            memory_key: Key for memory variable (default: "chat_history")
        """
        self.agent_name = agent_name
        self.memory_key = memory_key
        self._memory = ConversationBufferMemory(
            memory_key=memory_key,
            return_messages=True
        )
        self._created_at = datetime.now()
        logger.info(f"ConversationMemory initialized for {agent_name} agent")
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to conversation history.
        
        Args:
            role: Message role ("human" or "ai")
            content: Message content
        """
        if role == "human":
            self._memory.chat_memory.add_user_message(content)
        elif role == "ai":
            self._memory.chat_memory.add_ai_message(content)
        else:
            logger.warning(f"Unknown role '{role}', treating as user message")
            self._memory.chat_memory.add_user_message(content)
        
        logger.debug(
            f"{self.agent_name} memory: Added {role} message "
            f"({len(content)} chars)"
        )
    
    def get_context(self) -> str:
        """
        Get formatted conversation context.
        
        Returns:
            Formatted conversation history as string
        """
        messages = self._memory.chat_memory.messages
        if not messages:
            return ""
        
        context_lines = []
        for msg in messages:
            role = "Human" if msg.type == "human" else "AI"
            context_lines.append(f"{role}: {msg.content}")
        
        return "\n".join(context_lines)
    
    def get_messages(self) -> List[Any]:
        """
        Get raw message objects.
        
        Returns:
            List of message objects from LangChain
        """
        return self._memory.chat_memory.messages
    
    def get_langchain_memory(self) -> ConversationBufferMemory:
        """
        Get underlying LangChain memory object.
        
        Returns:
            ConversationBufferMemory instance
        """
        return self._memory
    
    def clear(self) -> None:
        """Clear conversation history."""
        message_count = len(self._memory.chat_memory.messages)
        self._memory.clear()
        logger.info(
            f"{self.agent_name} memory: Cleared {message_count} messages"
        )
    
    def __len__(self) -> int:
        """Return number of messages in memory."""
        return len(self._memory.chat_memory.messages)
    
    def __repr__(self) -> str:
        """String representation of memory."""
        return (
            f"ConversationMemory(agent={self.agent_name}, "
            f"messages={len(self)}, "
            f"age={datetime.now() - self._created_at})"
        )


class IntermediateResultsCache:
    """
    Cache for sharing intermediate results across agents.
    
    Enables cross-agent information sharing in the pipeline. When one agent
    completes, its results are stored in the cache for downstream agents to access.
    
    Pipeline flow:
    1. Planner Agent → stores outline in cache
    2. Content Agent → reads outline, stores content in cache
    3. Reviewer Agent → reads content, stores reviewed content in cache
    4. Design Agent → reads reviewed content, stores designed content in cache
    
    Features:
    - Key-value storage for agent results
    - Metadata tracking (timestamp, agent name)
    - Cache persistence throughout pipeline execution
    - Automatic logging of cache operations
    
    Usage:
        cache = IntermediateResultsCache()
        cache.store("outline", outline_data, agent_name="planner")
        outline = cache.retrieve("outline")
        cache.clear()
    """
    
    def __init__(self):
        """Initialize empty cache."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._created_at = datetime.now()
        logger.info("IntermediateResultsCache initialized")
    
    def store(
        self,
        key: str,
        value: Any,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: Cache key (e.g., "outline", "content", "reviewed")
            value: Value to store (any serializable object)
            agent_name: Optional name of agent storing the value
            metadata: Optional additional metadata
        """
        entry = {
            "value": value,
            "agent_name": agent_name,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        
        self._cache[key] = entry
        
        logger.info(
            f"Cache: Stored '{key}' "
            f"(agent={agent_name}, size={self._estimate_size(value)} bytes)"
        )
        logger.debug(f"Cache operation: store(key={key}, agent={agent_name})")
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        entry = self._cache.get(key)
        
        if entry is None:
            logger.warning(f"Cache: Key '{key}' not found")
            return None
        
        value = entry["value"]
        agent_name = entry.get("agent_name", "unknown")
        timestamp = entry.get("timestamp")
        
        logger.info(
            f"Cache: Retrieved '{key}' "
            f"(stored by {agent_name} at {timestamp})"
        )
        logger.debug(f"Cache operation: retrieve(key={key})")
        
        return value
    
    def has(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        return key in self._cache
    
    def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a cached entry.
        
        Args:
            key: Cache key
            
        Returns:
            Metadata dictionary or None if key not found
        """
        entry = self._cache.get(key)
        if entry is None:
            return None
        
        return {
            "agent_name": entry.get("agent_name"),
            "timestamp": entry.get("timestamp"),
            "metadata": entry.get("metadata", {})
        }
    
    def list_keys(self) -> List[str]:
        """
        List all keys in the cache.
        
        Returns:
            List of cache keys
        """
        return list(self._cache.keys())
    
    def clear(self) -> None:
        """Clear all cached entries."""
        key_count = len(self._cache)
        keys = list(self._cache.keys())
        self._cache.clear()
        
        logger.info(f"Cache: Cleared {key_count} entries: {keys}")
        logger.debug("Cache operation: clear()")
    
    def remove(self, key: str) -> bool:
        """
        Remove a specific entry from the cache.
        
        Args:
            key: Cache key to remove
            
        Returns:
            True if key was removed, False if not found
        """
        if key not in self._cache:
            logger.warning(f"Cache: Cannot remove '{key}': not found")
            return False
        
        del self._cache[key]
        logger.info(f"Cache: Removed '{key}'")
        logger.debug(f"Cache operation: remove(key={key})")
        return True
    
    def _estimate_size(self, value: Any) -> int:
        """
        Estimate size of a value in bytes.
        
        Args:
            value: Value to estimate
            
        Returns:
            Estimated size in bytes
        """
        try:
            import sys
            return sys.getsizeof(value)
        except Exception:
            return 0
    
    def __len__(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        return key in self._cache
    
    def __repr__(self) -> str:
        """String representation of cache."""
        return (
            f"IntermediateResultsCache(entries={len(self)}, "
            f"keys={list(self._cache.keys())}, "
            f"age={datetime.now() - self._created_at})"
        )
