"""Unit tests for memory system infrastructure."""
import pytest
from orchestrator.memory import ConversationMemory, IntermediateResultsCache


class TestConversationMemory:
    """Test ConversationMemory class."""
    
    def test_memory_initialization(self):
        """Test memory initialization."""
        memory = ConversationMemory(agent_name="planner")
        assert memory.agent_name == "planner"
        assert memory.memory_key == "chat_history"
        assert len(memory) == 0
    
    def test_add_human_message(self):
        """Test adding human message."""
        memory = ConversationMemory(agent_name="content")
        memory.add_message("human", "Generate content for AI presentation")
        
        assert len(memory) == 1
        context = memory.get_context()
        assert "Human: Generate content for AI presentation" in context
    
    def test_add_ai_message(self):
        """Test adding AI message."""
        memory = ConversationMemory(agent_name="reviewer")
        memory.add_message("ai", "I will review the content for quality")
        
        assert len(memory) == 1
        context = memory.get_context()
        assert "AI: I will review the content for quality" in context
    
    def test_conversation_flow(self):
        """Test multi-turn conversation."""
        memory = ConversationMemory(agent_name="design")
        memory.add_message("human", "Assign layouts to slides")
        memory.add_message("ai", "I'll analyze the content structure")
        memory.add_message("human", "Focus on visual balance")
        memory.add_message("ai", "I'll use the balance checker tool")
        
        assert len(memory) == 4
        context = memory.get_context()
        assert "Human: Assign layouts to slides" in context
        assert "AI: I'll analyze the content structure" in context
        assert "Human: Focus on visual balance" in context
        assert "AI: I'll use the balance checker tool" in context
    
    def test_get_messages(self):
        """Test getting raw messages."""
        memory = ConversationMemory(agent_name="planner")
        memory.add_message("human", "Create outline")
        memory.add_message("ai", "Working on it")
        
        messages = memory.get_messages()
        assert len(messages) == 2
        assert messages[0].type == "human"
        assert messages[1].type == "ai"
    
    def test_get_langchain_memory(self):
        """Test getting LangChain memory object."""
        memory = ConversationMemory(agent_name="content")
        langchain_memory = memory.get_langchain_memory()
        
        assert langchain_memory is not None
        assert hasattr(langchain_memory, "chat_memory")
    
    def test_clear_memory(self):
        """Test clearing memory."""
        memory = ConversationMemory(agent_name="reviewer")
        memory.add_message("human", "Review content")
        memory.add_message("ai", "Reviewing...")
        
        assert len(memory) == 2
        memory.clear()
        assert len(memory) == 0
    
    def test_empty_context(self):
        """Test getting context from empty memory."""
        memory = ConversationMemory(agent_name="design")
        context = memory.get_context()
        assert context == ""
    
    def test_unknown_role(self):
        """Test adding message with unknown role."""
        memory = ConversationMemory(agent_name="planner")
        memory.add_message("unknown", "Test message")
        
        # Should treat as user message
        assert len(memory) == 1
        context = memory.get_context()
        assert "Human: Test message" in context


class TestIntermediateResultsCache:
    """Test IntermediateResultsCache class."""
    
    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = IntermediateResultsCache()
        assert len(cache) == 0
        assert cache.list_keys() == []
    
    def test_store_and_retrieve(self):
        """Test storing and retrieving values."""
        cache = IntermediateResultsCache()
        test_data = {"title": "AI Presentation", "slides": 10}
        
        cache.store("outline", test_data, agent_name="planner")
        retrieved = cache.retrieve("outline")
        
        assert retrieved == test_data
        assert len(cache) == 1
    
    def test_store_with_metadata(self):
        """Test storing with custom metadata."""
        cache = IntermediateResultsCache()
        test_data = ["slide1", "slide2", "slide3"]
        metadata = {"quality_score": 0.85, "iterations": 3}
        
        cache.store("content", test_data, agent_name="content", metadata=metadata)
        
        retrieved_metadata = cache.get_metadata("content")
        assert retrieved_metadata["agent_name"] == "content"
        assert retrieved_metadata["metadata"]["quality_score"] == 0.85
        assert retrieved_metadata["metadata"]["iterations"] == 3
    
    def test_retrieve_nonexistent_key(self):
        """Test retrieving non-existent key."""
        cache = IntermediateResultsCache()
        result = cache.retrieve("nonexistent")
        assert result is None
    
    def test_has_key(self):
        """Test checking if key exists."""
        cache = IntermediateResultsCache()
        cache.store("reviewed", {"data": "test"}, agent_name="reviewer")
        
        assert cache.has("reviewed") is True
        assert cache.has("nonexistent") is False
        assert "reviewed" in cache
        assert "nonexistent" not in cache
    
    def test_list_keys(self):
        """Test listing all keys."""
        cache = IntermediateResultsCache()
        cache.store("outline", {}, agent_name="planner")
        cache.store("content", {}, agent_name="content")
        cache.store("reviewed", {}, agent_name="reviewer")
        
        keys = cache.list_keys()
        assert len(keys) == 3
        assert "outline" in keys
        assert "content" in keys
        assert "reviewed" in keys
    
    def test_remove_entry(self):
        """Test removing specific entry."""
        cache = IntermediateResultsCache()
        cache.store("designed", {}, agent_name="design")
        
        assert len(cache) == 1
        result = cache.remove("designed")
        assert result is True
        assert len(cache) == 0
    
    def test_remove_nonexistent_entry(self):
        """Test removing non-existent entry."""
        cache = IntermediateResultsCache()
        result = cache.remove("nonexistent")
        assert result is False
    
    def test_clear_cache(self):
        """Test clearing entire cache."""
        cache = IntermediateResultsCache()
        cache.store("outline", {}, agent_name="planner")
        cache.store("content", {}, agent_name="content")
        cache.store("reviewed", {}, agent_name="reviewer")
        cache.store("designed", {}, agent_name="design")
        
        assert len(cache) == 4
        cache.clear()
        assert len(cache) == 0
        assert cache.list_keys() == []
    
    def test_pipeline_simulation(self):
        """Test simulating full pipeline cache usage."""
        cache = IntermediateResultsCache()
        
        # Planner stores outline
        outline = {"title": "AI Presentation", "slides": ["Intro", "Body", "Conclusion"]}
        cache.store("outline", outline, agent_name="planner")
        
        # Content reads outline and stores content
        retrieved_outline = cache.retrieve("outline")
        assert retrieved_outline == outline
        
        content = {"slides": [{"title": "Intro", "bullets": ["Point 1", "Point 2"]}]}
        cache.store("content", content, agent_name="content")
        
        # Reviewer reads content and stores reviewed
        retrieved_content = cache.retrieve("content")
        assert retrieved_content == content
        
        reviewed = {"slides": [{"title": "Intro", "bullets": ["Refined Point 1", "Refined Point 2"]}]}
        cache.store("reviewed", reviewed, agent_name="reviewer")
        
        # Design reads reviewed and stores designed
        retrieved_reviewed = cache.retrieve("reviewed")
        assert retrieved_reviewed == reviewed
        
        designed = {"slides": [{"title": "Intro", "layout": "bullet_list"}]}
        cache.store("designed", designed, agent_name="design")
        
        # Verify all entries exist
        assert len(cache) == 4
        assert cache.has("outline")
        assert cache.has("content")
        assert cache.has("reviewed")
        assert cache.has("designed")
        
        # Clear after pipeline
        cache.clear()
        assert len(cache) == 0
    
    def test_get_metadata_nonexistent(self):
        """Test getting metadata for non-existent key."""
        cache = IntermediateResultsCache()
        metadata = cache.get_metadata("nonexistent")
        assert metadata is None
    
    def test_store_different_types(self):
        """Test storing different data types."""
        cache = IntermediateResultsCache()
        
        # Store string
        cache.store("string_data", "test string", agent_name="test")
        assert cache.retrieve("string_data") == "test string"
        
        # Store list
        cache.store("list_data", [1, 2, 3], agent_name="test")
        assert cache.retrieve("list_data") == [1, 2, 3]
        
        # Store dict
        cache.store("dict_data", {"key": "value"}, agent_name="test")
        assert cache.retrieve("dict_data") == {"key": "value"}
        
        # Store number
        cache.store("number_data", 42, agent_name="test")
        assert cache.retrieve("number_data") == 42
        
        assert len(cache) == 4
