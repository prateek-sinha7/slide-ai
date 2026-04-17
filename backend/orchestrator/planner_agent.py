"""Planner Agent for presentation structure generation using ReAct pattern."""
import logging
import asyncio
import json
from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropicMessages as ChatAnthropic
from langchain_community.llms import Ollama
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate

from orchestrator.models import SlideOutline
from orchestrator.config import config
from orchestrator.memory import ConversationMemory, IntermediateResultsCache
from orchestrator.exceptions import GenerationError
from orchestrator.tools.planner_tools import (
    WebSearchTool,
    StructureValidatorTool,
    OutlineQualityCheckerTool
)


logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Planner Agent - Defines presentation structure and flow using ReAct pattern.
    
    Responsibilities:
    - Create logical outline with slide titles
    - Define key points for each slide
    - Ensure coherent narrative flow
    - Use tools autonomously (web search, structure validation, quality checking)
    - Iterate until quality threshold is met or max iterations reached
    
    ReAct Pattern:
    - Think: Reason about the current state and what to do next
    - Act: Use tools to gather information or validate output
    - Observe: Analyze tool results and decide next steps
    - Repeat: Continue until quality threshold met or max iterations reached
    """
    
    def __init__(
        self,
        llm=None,
        memory: Optional[ConversationMemory] = None,
        cache: Optional[IntermediateResultsCache] = None
    ):
        """
        Initialize Planner Agent with ReAct capabilities.
        
        Args:
            llm: Optional LangChain LLM instance. If None, creates default.
            memory: Optional conversation memory for context retention
            cache: Optional intermediate results cache for cross-agent sharing
        """
        self.llm = llm or self._create_llm()
        self.memory = memory or ConversationMemory(agent_name="planner")
        self.cache = cache
        self.parser = PydanticOutputParser(pydantic_object=SlideOutline)
        
        # Initialize tools
        self.tools = self._create_tools()
        
        # Create ReAct agent and executor
        self.agent = self._create_react_agent()
        self.agent_executor = self._create_agent_executor()
        
        # Fallback chain for final output parsing
        self.fallback_prompt = self._create_fallback_prompt()
        self.fallback_chain = self._create_fallback_chain()
        
    def _create_llm(self):
        """
        Create LLM instance based on configuration.
        
        Returns:
            LangChain LLM instance
            
        Raises:
            ValueError: If unsupported LLM provider is specified
        """
        if config.LLM_PROVIDER == "openai":
            return ChatOpenAI(
                model=config.LLM_MODEL,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                openai_api_key=config.OPENAI_API_KEY
            )
        elif config.LLM_PROVIDER == "anthropic":
            return ChatAnthropic(
                model_name=config.LLM_MODEL,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                anthropic_api_key=config.ANTHROPIC_API_KEY
            )
        elif config.LLM_PROVIDER == "groq":
            from groq import RateLimitError, APIError, APITimeoutError
            
            # Create Groq LLM with error handling
            llm = ChatGroq(
                model=config.GROQ_MODEL,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                groq_api_key=config.GROQ_API_KEY,
                max_retries=config.MAX_RETRIES
            )
            
            logger.info(
                f"Planner Agent: Created Groq LLM with model {config.GROQ_MODEL} "
                f"(max_retries={config.MAX_RETRIES})"
            )
            
            return llm
        elif config.LLM_PROVIDER == "ollama":
            return Ollama(
                model=config.LLM_MODEL,
                temperature=config.LLM_TEMPERATURE,
                base_url=config.OLLAMA_BASE_URL
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {config.LLM_PROVIDER}")
    
    def _create_tools(self) -> List[Tool]:
        """
        Create tools for Planner Agent.
        
        Returns:
            List of LangChain Tool instances
        """
        # Instantiate tool implementations
        web_search = WebSearchTool()
        structure_validator = StructureValidatorTool()
        quality_checker = OutlineQualityCheckerTool()
        
        # Wrap in LangChain Tool format (WebSearchTool removed to avoid rate limits)
        tools = [
            Tool(
                name=structure_validator.name,
                func=structure_validator.execute,
                description=structure_validator.description
            ),
            Tool(
                name=quality_checker.name,
                func=quality_checker.execute,
                description=quality_checker.description
            )
        ]
        
        logger.info(
            f"Planner Agent: Initialized {len(tools)} tools: "
            f"{[t.name for t in tools]}"
        )
        return tools
    
    def _create_react_agent(self):
        """
        Create ReAct agent for Planner.
        
        Returns:
            ReAct agent instance
        """
        # ReAct prompt template
        react_prompt = PromptTemplate.from_template(
            """You are an expert presentation planner agent. Your task is to create a logical, 
well-structured outline for a presentation using the ReAct (Reasoning + Acting) pattern.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: Your Final Answer MUST be a valid JSON object matching this schema:
{format_instructions}

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
        )
        
        # Create agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=react_prompt
        )
        
        logger.info("Planner Agent: ReAct agent created")
        return agent
    
    def _create_agent_executor(self) -> AgentExecutor:
        """
        Create AgentExecutor with iteration limits and quality control.
        
        Returns:
            AgentExecutor instance
        """
        executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=config.MAX_ITERATIONS,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        logger.info(
            f"Planner Agent: AgentExecutor created "
            f"(max_iterations={config.MAX_ITERATIONS})"
        )
        return executor
    
    def _create_fallback_prompt(self) -> ChatPromptTemplate:
        """
        Create fallback prompt for direct outline generation.
        
        This is used when the agent completes its reasoning but needs
        to format the final output as structured JSON.
        
        Returns:
            ChatPromptTemplate for fallback generation
        """
        template = """You are an expert presentation planner. Create a logical, 
well-structured outline for a presentation.

Topic: {topic}
Number of slides: {slide_count}
Tone: {tone}

Create a presentation outline with:
1. A compelling title and subtitle
2. Exactly {slide_count} content slides with clear titles
3. 3-4 key points for each slide (these will be expanded later)
4. A summary with 3-5 key takeaways

Guidelines:
- Ensure logical flow and coherent narrative
- Make titles clear and descriptive
- Keep key points concise (one sentence each)
- Build towards a strong conclusion

{format_instructions}

Return ONLY valid JSON, no additional text."""

        return ChatPromptTemplate.from_messages([
            ("system", "You are an expert presentation planner."),
            ("human", template)
        ])
    
    def _create_fallback_chain(self):
        """
        Create fallback LangChain chain for direct generation.
        
        Returns:
            Runnable chain
        """
        return (
            {
                "topic": lambda x: x["topic"],
                "slide_count": lambda x: x["slide_count"],
                "tone": lambda x: x["tone"],
                "format_instructions": lambda x: self.parser.get_format_instructions()
            }
            | self.fallback_prompt
            | self.llm
            | self.parser
        )
    
    async def generate_outline(
        self,
        topic: str,
        slide_count: int,
        tone: Optional[str] = None
    ) -> SlideOutline:
        """
        Generate presentation outline using ReAct pattern.
        
        The agent will:
        1. Think about the presentation structure
        2. Optionally use web search to research the topic
        3. Create an initial outline
        4. Use structure validator to check logical flow
        5. Use quality checker to score the outline
        6. Iterate to improve quality if below threshold
        7. Return final outline when quality threshold met or max iterations reached
        
        Args:
            topic: Presentation topic
            slide_count: Number of content slides (5-20)
            tone: Optional tone (formal, casual, fun, professional)
            
        Returns:
            SlideOutline with structured presentation plan
            
        Raises:
            asyncio.TimeoutError: If generation exceeds timeout
            ValueError: If output validation fails
        """
        tone = tone or "professional"
        
        logger.info(
            f"Planner Agent: Generating outline for '{topic}' "
            f"({slide_count} slides, {tone} tone) using ReAct pattern"
        )
        
        try:
            # Run with timeout (Python 3.9 compatible)
            outline = await asyncio.wait_for(
                self._generate_with_react(
                    topic=topic,
                    slide_count=slide_count,
                    tone=tone
                ),
                timeout=config.PLANNER_TIMEOUT
            )
                
            # Validate output
            if len(outline.outline) != slide_count:
                logger.warning(
                    f"Expected {slide_count} slides, got {len(outline.outline)}, "
                    f"attempting to adjust..."
                )
                # Allow slight mismatch but log it
                if abs(len(outline.outline) - slide_count) > 2:
                    raise ValueError(
                        f"Expected {slide_count} slides, got {len(outline.outline)}"
                    )
            
            # Store in cache if available
            if self.cache:
                self.cache.store(
                    key="outline",
                    value=outline,
                    agent_name="planner"
                )
                logger.info("Planner Agent: Stored outline in cache")
            
            logger.info(
                f"Planner Agent: Successfully generated outline with "
                f"{len(outline.outline)} slides"
            )
            
            return outline
            
        except asyncio.TimeoutError:
            logger.error(
                f"Planner Agent: Timeout after {config.PLANNER_TIMEOUT}s"
            )
            raise
        except Exception as e:
            logger.error(f"Planner Agent: Failed to generate outline: {str(e)}")
            raise
    
    async def _generate_with_react(
        self,
        topic: str,
        slide_count: int,
        tone: str
    ) -> SlideOutline:
        """
        Generate outline using ReAct agent with quality-based iteration.
        
        Args:
            topic: Presentation topic
            slide_count: Number of slides
            tone: Presentation tone
            
        Returns:
            SlideOutline
            
        Raises:
            Exception: If generation fails
        """
        # Prepare agent input
        agent_input = (
            f"Create a {tone} presentation outline about '{topic}' "
            f"with exactly {slide_count} content slides. "
            f"Use the available tools to research the topic, validate structure, "
            f"and check quality. Iterate until the quality score is at least "
            f"{int(config.QUALITY_THRESHOLD * 100)}/100 or you reach the maximum iterations."
        )
        
        # Add format instructions to agent input
        format_instructions = self.parser.get_format_instructions()
        agent_input += f"\n\n{format_instructions}"
        
        # Add memory context if available
        if self.memory and len(self.memory) > 0:
            context = self.memory.get_context()
            agent_input = f"Previous context:\n{context}\n\n{agent_input}"
        
        logger.info("Planner Agent: Starting ReAct reasoning loop")
        
        try:
            # Invoke agent executor with Groq error handling
            if config.LLM_PROVIDER == "groq":
                from groq import RateLimitError, APIError, APITimeoutError
                
                try:
                    result = await self.agent_executor.ainvoke({
                        "input": agent_input,
                        "format_instructions": format_instructions
                    })
                except RateLimitError as e:
                    logger.error(
                        f"Planner Agent: Groq API rate limit exceeded: {str(e)}"
                    )
                    raise GenerationError(
                        "Groq API rate limit exceeded. Please wait a moment and try again.",
                        agent="Planner"
                    )
                except APITimeoutError as e:
                    logger.error(
                        f"Planner Agent: Groq API timeout: {str(e)}"
                    )
                    raise GenerationError(
                        "Groq API request timed out. The service may be slow or unavailable.",
                        agent="Planner"
                    )
                except APIError as e:
                    logger.error(
                        f"Planner Agent: Groq API error: {str(e)}"
                    )
                    if hasattr(e, 'status_code') and e.status_code == 503:
                        raise GenerationError(
                            "Groq API service is temporarily unavailable. Please try again later.",
                            agent="Planner"
                        )
                    else:
                        raise GenerationError(
                            f"Groq API error: {str(e)}",
                            agent="Planner"
                        )
            else:
                # Non-Groq providers
                result = await self.agent_executor.ainvoke({
                    "input": agent_input,
                    "format_instructions": format_instructions
                })
            
            # Log reasoning trace
            self._log_reasoning_trace(result)
            
            # Extract and parse final answer
            final_answer = result.get("output", "")
            
            # Try to parse the final answer as JSON
            outline = self._parse_agent_output(final_answer, topic, slide_count, tone)
            
            # Store interaction in memory
            self.memory.add_message("human", agent_input)
            self.memory.add_message("ai", final_answer)
            
            return outline
            
        except Exception as e:
            logger.error(f"Planner Agent: ReAct generation failed: {str(e)}")
            logger.info("Planner Agent: Falling back to direct generation")
            
            # Fallback to direct generation
            return await self._fallback_generation(topic, slide_count, tone)
    
    def _parse_agent_output(
        self,
        output: str,
        topic: str,
        slide_count: int,
        tone: str
    ) -> SlideOutline:
        """
        Parse agent output into SlideOutline.
        
        Args:
            output: Agent's final answer
            topic: Presentation topic (for fallback)
            slide_count: Number of slides (for fallback)
            tone: Presentation tone (for fallback)
            
        Returns:
            SlideOutline
            
        Raises:
            Exception: If parsing fails completely
        """
        try:
            # Try to extract JSON from the output
            # Look for JSON object in the text
            import re
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                outline_dict = json.loads(json_str)
                outline = self.parser.parse(json_str)
                logger.info("Planner Agent: Successfully parsed agent output")
                return outline
            else:
                logger.warning("Planner Agent: No JSON found in agent output")
                raise ValueError("No JSON found in output")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                f"Planner Agent: Failed to parse agent output: {str(e)}, "
                f"using fallback generation"
            )
            # Use fallback - this will be handled by caller
            raise
    
    async def _fallback_generation(
        self,
        topic: str,
        slide_count: int,
        tone: str
    ) -> SlideOutline:
        """
        Fallback to direct generation without ReAct loop.
        
        Args:
            topic: Presentation topic
            slide_count: Number of slides
            tone: Presentation tone
            
        Returns:
            SlideOutline
        """
        logger.info("Planner Agent: Using fallback chain for direct generation")
        
        try:
            outline = await self.fallback_chain.ainvoke({
                "topic": topic,
                "slide_count": slide_count,
                "tone": tone
            })
            
            logger.info("Planner Agent: Fallback generation successful")
            return outline
            
        except Exception as e:
            logger.error(f"Planner Agent: Fallback generation failed: {str(e)}")
            raise
    
    def _log_reasoning_trace(self, result: Dict[str, Any]) -> None:
        """
        Log the agent's reasoning trace.
        
        Args:
            result: Agent execution result with intermediate steps
        """
        intermediate_steps = result.get("intermediate_steps", [])
        
        if not intermediate_steps:
            logger.info("Planner Agent: No intermediate steps recorded")
            return
        
        logger.info(
            f"Planner Agent: Reasoning trace ({len(intermediate_steps)} steps):"
        )
        
        tool_invocation_count = 0
        tool_durations = {}
        
        for i, (action, observation) in enumerate(intermediate_steps, 1):
            tool_name = action.tool if hasattr(action, 'tool') else 'unknown'
            tool_input = action.tool_input if hasattr(action, 'tool_input') else ''
            
            logger.info(f"  Step {i}:")
            logger.info(f"    Action: {tool_name}")
            logger.info(f"    Input: {str(tool_input)[:100]}...")
            logger.info(f"    Observation: {str(observation)[:200]}...")
            
            # Count tool invocations
            if tool_name != 'unknown':
                tool_invocation_count += 1
                tool_durations[tool_name] = tool_durations.get(tool_name, 0) + 1
        
        # Log iteration count
        logger.info(
            f"Planner Agent: Completed in {len(intermediate_steps)} iterations "
            f"(max: {config.MAX_ITERATIONS})"
        )
        
        # Log tool invocation summary
        logger.info(f"Planner Agent: Total tool invocations: {tool_invocation_count}")
        for tool_name, count in tool_durations.items():
            logger.info(f"Planner Agent: Tool '{tool_name}' invoked {count} times")
