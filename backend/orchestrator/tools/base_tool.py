"""Base tool abstract class for LangChain agents."""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class BaseTool(LangChainBaseTool, ABC):
    """
    Abstract base class for all agent tools.
    
    This class extends LangChain's BaseTool to provide a consistent interface
    for all tools used by the four agents (Planner, Content, Reviewer, Design).
    
    All tools must implement:
    - name: Unique tool identifier
    - description: Clear description for agent to understand tool purpose
    - _run: Synchronous execution logic
    - _arun: Asynchronous execution logic (optional, defaults to sync)
    
    Tools should:
    - Log invocations with input parameters and results
    - Handle errors gracefully and return meaningful error messages
    - Return structured data when possible
    - Be stateless (no instance variables that change between calls)
    """
    
    # Tool metadata (must be overridden by subclasses)
    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Tool description for agent")
    
    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Synchronous tool execution.
        
        This method must be implemented by all tool subclasses.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Tool execution result (string, dict, or structured data)
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        logger.info(f"Tool '{self.name}' invoked with args={args}, kwargs={kwargs}")
        
        try:
            result = self.execute(*args, **kwargs)
            logger.info(f"Tool '{self.name}' completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool '{self.name}' failed: {str(e)}")
            return self._format_error(str(e))
    
    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """
        Asynchronous tool execution.
        
        Default implementation calls synchronous _run method.
        Override this method for truly async tools.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Tool execution result
        """
        return self._run(*args, **kwargs)
    
    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        Core tool execution logic.
        
        This method must be implemented by all tool subclasses.
        It contains the actual tool logic without error handling boilerplate.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Tool execution result
            
        Raises:
            Exception: Any exception during execution
        """
        raise NotImplementedError("Tool subclasses must implement execute()")
    
    def _format_error(self, error_message: str) -> str:
        """
        Format error message for agent consumption.
        
        Args:
            error_message: Raw error message
            
        Returns:
            Formatted error message
        """
        return f"Error in {self.name}: {error_message}"
    
    def _format_result(self, result: Any) -> str:
        """
        Format tool result for agent consumption.
        
        Args:
            result: Raw tool result
            
        Returns:
            Formatted result string
        """
        if isinstance(result, dict):
            return "\n".join([f"{k}: {v}" for k, v in result.items()])
        elif isinstance(result, list):
            return "\n".join([str(item) for item in result])
        else:
            return str(result)
