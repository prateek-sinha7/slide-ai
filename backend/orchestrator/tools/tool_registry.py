"""Centralized tool registry for agent tool management."""
import logging
from typing import Dict, List, Optional, Type
from orchestrator.tools.base_tool import BaseTool


logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Centralized registry for managing agent tools.
    
    The ToolRegistry provides:
    - Tool registration and discovery
    - Tool retrieval by name or agent type
    - Tool validation and metadata management
    
    Usage:
        # Register tools
        registry = ToolRegistry()
        registry.register(WebSearchTool())
        registry.register(FactCheckerTool())
        
        # Get tools for specific agent
        planner_tools = registry.get_tools_for_agent("planner")
        
        # Get specific tool by name
        search_tool = registry.get_tool("web_search")
    """
    
    def __init__(self):
        """Initialize empty tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._agent_tools: Dict[str, List[str]] = {
            "planner": [],
            "content": [],
            "reviewer": [],
            "design": []
        }
        logger.info("ToolRegistry initialized")
    
    def register(self, tool: BaseTool, agent_type: Optional[str] = None) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool instance to register
            agent_type: Optional agent type (planner, content, reviewer, design)
                       If provided, tool is associated with that agent
                       
        Raises:
            ValueError: If tool name already registered or agent_type invalid
        """
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already registered, overwriting")
        
        self._tools[tool.name] = tool
        logger.info(f"Registered tool '{tool.name}': {tool.description}")
        
        if agent_type:
            if agent_type not in self._agent_tools:
                raise ValueError(
                    f"Invalid agent_type '{agent_type}'. "
                    f"Must be one of: {list(self._agent_tools.keys())}"
                )
            
            if tool.name not in self._agent_tools[agent_type]:
                self._agent_tools[agent_type].append(tool.name)
                logger.info(f"Associated tool '{tool.name}' with {agent_type} agent")
    
    def register_multiple(
        self,
        tools: List[BaseTool],
        agent_type: Optional[str] = None
    ) -> None:
        """
        Register multiple tools at once.
        
        Args:
            tools: List of tool instances to register
            agent_type: Optional agent type for all tools
        """
        for tool in tools:
            self.register(tool, agent_type)
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a specific tool by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            Tool instance or None if not found
        """
        tool = self._tools.get(tool_name)
        if tool is None:
            logger.warning(f"Tool '{tool_name}' not found in registry")
        return tool
    
    def get_tools_for_agent(self, agent_type: str) -> List[BaseTool]:
        """
        Get all tools registered for a specific agent.
        
        Args:
            agent_type: Agent type (planner, content, reviewer, design)
            
        Returns:
            List of tool instances for the agent
            
        Raises:
            ValueError: If agent_type is invalid
        """
        if agent_type not in self._agent_tools:
            raise ValueError(
                f"Invalid agent_type '{agent_type}'. "
                f"Must be one of: {list(self._agent_tools.keys())}"
            )
        
        tool_names = self._agent_tools[agent_type]
        tools = [self._tools[name] for name in tool_names if name in self._tools]
        
        logger.info(
            f"Retrieved {len(tools)} tools for {agent_type} agent: "
            f"{[t.name for t in tools]}"
        )
        return tools
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        Get all registered tools.
        
        Returns:
            List of all tool instances
        """
        return list(self._tools.values())
    
    def list_tools(self) -> Dict[str, str]:
        """
        List all registered tools with their descriptions.
        
        Returns:
            Dictionary mapping tool names to descriptions
        """
        return {name: tool.description for name, tool in self._tools.items()}
    
    def list_agent_tools(self, agent_type: str) -> Dict[str, str]:
        """
        List tools for a specific agent with descriptions.
        
        Args:
            agent_type: Agent type (planner, content, reviewer, design)
            
        Returns:
            Dictionary mapping tool names to descriptions
            
        Raises:
            ValueError: If agent_type is invalid
        """
        tools = self.get_tools_for_agent(agent_type)
        return {tool.name: tool.description for tool in tools}
    
    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool from the registry.
        
        Args:
            tool_name: Name of the tool to unregister
            
        Returns:
            True if tool was unregistered, False if not found
        """
        if tool_name not in self._tools:
            logger.warning(f"Cannot unregister tool '{tool_name}': not found")
            return False
        
        # Remove from main registry
        del self._tools[tool_name]
        
        # Remove from agent associations
        for agent_type in self._agent_tools:
            if tool_name in self._agent_tools[agent_type]:
                self._agent_tools[agent_type].remove(tool_name)
        
        logger.info(f"Unregistered tool '{tool_name}'")
        return True
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        for agent_type in self._agent_tools:
            self._agent_tools[agent_type].clear()
        logger.info("ToolRegistry cleared")
    
    def __len__(self) -> int:
        """Return number of registered tools."""
        return len(self._tools)
    
    def __contains__(self, tool_name: str) -> bool:
        """Check if a tool is registered."""
        return tool_name in self._tools
    
    def __repr__(self) -> str:
        """String representation of registry."""
        return f"ToolRegistry(tools={len(self._tools)})"


# Global tool registry instance
tool_registry = ToolRegistry()
