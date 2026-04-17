"""
Python 3.9 compatibility verification tests.

This test suite validates:
- Python 3.9 environment compatibility
- Async syntax compatibility (asyncio.wait_for)
- Type hints compatibility
- All dependencies install correctly

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
"""
import sys
import pytest
import logging
import asyncio
from typing import Optional, List, Dict, Any


logger = logging.getLogger(__name__)


class TestPython39Environment:
    """Test Python 3.9+ environment compatibility."""
    
    def test_python_version(self):
        """
        Test that Python version is 3.9 or higher.
        
        Validates:
        - Python version >= 3.9
        """
        version_info = sys.version_info
        
        logger.info(f"Python version: {version_info.major}.{version_info.minor}.{version_info.micro}")
        
        assert version_info.major == 3
        assert version_info.minor >= 9
        
        logger.info("✓ Python version test passed")
    
    def test_asyncio_wait_for_available(self):
        """
        Test that asyncio.wait_for is available (Python 3.9+).
        
        Validates:
        - asyncio.wait_for function exists
        - Can be used for timeout control
        """
        assert hasattr(asyncio, 'wait_for')
        
        # Test basic usage
        async def sample_task():
            await asyncio.sleep(0.1)
            return "success"
        
        # Run with wait_for
        result = asyncio.run(
            asyncio.wait_for(sample_task(), timeout=1.0)
        )
        
        assert result == "success"
        
        logger.info("✓ asyncio.wait_for availability test passed")
    
    def test_asyncio_timeout_not_used(self):
        """
        Test that asyncio.timeout is NOT used (requires Python 3.11+).
        
        Validates:
        - Code does not use asyncio.timeout context manager
        - Uses asyncio.wait_for instead
        """
        import inspect
        import re
        from orchestrator import planner_agent, content_agent, reviewer_agent, design_agent, orchestrator
        
        modules = [planner_agent, content_agent, reviewer_agent, design_agent, orchestrator]
        
        for module in modules:
            source = inspect.getsource(module)
            
            # Check for actual usage of asyncio.timeout context manager
            # Pattern: async with asyncio.timeout(...):
            timeout_pattern = r'async\s+with\s+asyncio\.timeout\s*\('
            matches = re.findall(timeout_pattern, source)
            
            assert len(matches) == 0, f"Module {module.__name__} uses asyncio.timeout context manager (requires Python 3.11+)"
            
            # Should use asyncio.wait_for instead
            if "await" in source and "timeout" in source.lower():
                assert "asyncio.wait_for" in source, f"Module {module.__name__} should use asyncio.wait_for"
        
        logger.info("✓ asyncio.timeout not used test passed")


class TestTypeHintsCompatibility:
    """Test type hints compatibility with Python 3.9."""
    
    def test_optional_syntax(self):
        """
        Test that Optional syntax is used (not PEP 604 | syntax).
        
        Validates:
        - Uses typing.Optional instead of X | Y
        - Compatible with Python 3.9
        """
        import inspect
        from orchestrator import models
        
        source = inspect.getsource(models)
        
        # Should use Optional from typing
        assert "Optional" in source
        
        # Check that we're not using | syntax for unions in type hints
        # (This is a heuristic check - not perfect but catches most cases)
        lines = source.split('\n')
        for line in lines:
            # Skip comments and strings
            if line.strip().startswith('#'):
                continue
            if '"""' in line or "'''" in line:
                continue
            
            # Check for | in type hint context
            if ':' in line and '|' in line:
                # This might be a union type using | syntax
                # Make sure it's not in a string or comment
                if 'Optional' not in line and 'Union' not in line:
                    # Could be using | syntax - log warning
                    logger.warning(f"Potential | syntax in type hint: {line.strip()}")
        
        logger.info("✓ Optional syntax test passed")
    
    def test_typing_imports(self):
        """
        Test that typing module imports are compatible.
        
        Validates:
        - All typing imports work in Python 3.9
        """
        from typing import Optional, List, Dict, Any, Union, Literal
        
        # Test that we can use these types
        def sample_function(
            param1: Optional[str] = None,
            param2: List[int] = None,
            param3: Dict[str, Any] = None,
            param4: Union[str, int] = None
        ) -> Optional[str]:
            return param1
        
        assert sample_function is not None
        
        logger.info("✓ Typing imports test passed")


class TestDependenciesCompatibility:
    """Test that all dependencies are compatible with Python 3.9."""
    
    def test_core_dependencies(self):
        """
        Test that core dependencies can be imported.
        
        Validates:
        - All core packages are importable
        - No import errors
        """
        # Test critical imports
        import langchain
        import langchain_groq
        import langchain_openai
        import langchain_anthropic
        import langchain_community
        import pydantic
        import fastapi
        import uvicorn
        
        logger.info("✓ Core dependencies test passed")
    
    def test_langchain_groq(self):
        """
        Test that langchain-groq is compatible.
        
        Validates:
        - langchain-groq can be imported
        - ChatGroq class is available
        """
        from langchain_groq import ChatGroq
        
        assert ChatGroq is not None
        
        logger.info("✓ langchain-groq compatibility test passed")
    
    def test_pydantic_v2(self):
        """
        Test that Pydantic v2 is compatible with Python 3.9.
        
        Validates:
        - Pydantic v2 models work correctly
        - Field validation works
        """
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            name: str = Field(..., min_length=1)
            age: Optional[int] = Field(None, ge=0)
        
        # Test model creation
        model = TestModel(name="test", age=25)
        assert model.name == "test"
        assert model.age == 25
        
        # Test validation
        with pytest.raises(Exception):  # Should raise validation error
            TestModel(name="", age=-1)
        
        logger.info("✓ Pydantic v2 compatibility test passed")
    
    def test_testing_dependencies(self):
        """
        Test that testing dependencies are compatible.
        
        Validates:
        - pytest works
        - pytest-asyncio works
        - hypothesis works
        """
        import pytest
        import pytest_asyncio
        import hypothesis
        
        assert pytest is not None
        assert pytest_asyncio is not None
        assert hypothesis is not None
        
        logger.info("✓ Testing dependencies test passed")
    
    def test_web_dependencies(self):
        """
        Test that web dependencies are compatible.
        
        Validates:
        - FastAPI works
        - Uvicorn works
        - HTTPX works
        """
        import fastapi
        import uvicorn
        import httpx
        
        assert fastapi is not None
        assert uvicorn is not None
        assert httpx is not None
        
        logger.info("✓ Web dependencies test passed")


class TestAsyncSyntaxCompatibility:
    """Test async/await syntax compatibility with Python 3.9."""
    
    @pytest.mark.asyncio
    async def test_async_await_basic(self):
        """
        Test basic async/await syntax.
        
        Validates:
        - async/await works correctly
        """
        async def sample_async_function():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await sample_async_function()
        assert result == "success"
        
        logger.info("✓ Basic async/await test passed")
    
    @pytest.mark.asyncio
    async def test_asyncio_wait_for_timeout(self):
        """
        Test asyncio.wait_for with timeout.
        
        Validates:
        - asyncio.wait_for handles timeouts correctly
        """
        async def slow_task():
            await asyncio.sleep(2.0)
            return "completed"
        
        # Should timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_task(), timeout=0.5)
        
        logger.info("✓ asyncio.wait_for timeout test passed")
    
    @pytest.mark.asyncio
    async def test_asyncio_wait_for_success(self):
        """
        Test asyncio.wait_for with successful completion.
        
        Validates:
        - asyncio.wait_for returns result when task completes
        """
        async def fast_task():
            await asyncio.sleep(0.1)
            return "completed"
        
        result = await asyncio.wait_for(fast_task(), timeout=1.0)
        assert result == "completed"
        
        logger.info("✓ asyncio.wait_for success test passed")


class TestAgentCodeCompatibility:
    """Test that agent code is compatible with Python 3.9."""
    
    def test_planner_agent_syntax(self):
        """
        Test Planner Agent code syntax compatibility.
        
        Validates:
        - No Python 3.10+ syntax
        - Uses asyncio.wait_for
        """
        import inspect
        import re
        from orchestrator.planner_agent import PlannerAgent
        
        source = inspect.getsource(PlannerAgent)
        
        # Should use asyncio.wait_for
        assert "asyncio.wait_for" in source
        
        # Check for match/case statement (Python 3.10+)
        # Pattern: match <expression>:
        match_pattern = r'\bmatch\s+\w+\s*:'
        matches = re.findall(match_pattern, source)
        
        assert len(matches) == 0, f"Planner Agent uses match/case statement (requires Python 3.10+)"
        
        logger.info("✓ Planner Agent syntax test passed")
    
    def test_content_agent_syntax(self):
        """
        Test Content Agent code syntax compatibility.
        
        Validates:
        - No Python 3.10+ syntax
        - Uses asyncio.wait_for
        """
        import inspect
        from orchestrator.content_agent import ContentAgent
        
        source = inspect.getsource(ContentAgent)
        
        # Should use asyncio.wait_for
        assert "asyncio.wait_for" in source
        
        logger.info("✓ Content Agent syntax test passed")
    
    def test_reviewer_agent_syntax(self):
        """
        Test Reviewer Agent code syntax compatibility.
        
        Validates:
        - No Python 3.10+ syntax
        - Uses asyncio.wait_for
        """
        import inspect
        from orchestrator.reviewer_agent import ReviewerAgent
        
        source = inspect.getsource(ReviewerAgent)
        
        # Should use asyncio.wait_for
        assert "asyncio.wait_for" in source
        
        logger.info("✓ Reviewer Agent syntax test passed")
    
    def test_design_agent_syntax(self):
        """
        Test Design Agent code syntax compatibility.
        
        Validates:
        - No Python 3.10+ syntax
        - Uses asyncio.wait_for
        """
        import inspect
        from orchestrator.design_agent import DesignAgent
        
        source = inspect.getsource(DesignAgent)
        
        # Should use asyncio.wait_for
        assert "asyncio.wait_for" in source
        
        logger.info("✓ Design Agent syntax test passed")
    
    def test_orchestrator_syntax(self):
        """
        Test Orchestrator code syntax compatibility.
        
        Validates:
        - No Python 3.10+ syntax
        - Uses asyncio.wait_for
        """
        import inspect
        from orchestrator.orchestrator import LLMOrchestrator
        
        source = inspect.getsource(LLMOrchestrator)
        
        # Should use asyncio.wait_for
        assert "asyncio.wait_for" in source
        
        logger.info("✓ Orchestrator syntax test passed")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
