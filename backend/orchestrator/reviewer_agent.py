"""Reviewer Agent for refining and cleaning presentation content using ReAct pattern."""
import logging
import asyncio
import json
import re
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

from orchestrator.models import GeneratedContent, ReviewedContent
from orchestrator.config import config
from orchestrator.memory import ConversationMemory, IntermediateResultsCache
from orchestrator.exceptions import GenerationError
from orchestrator.tools.reviewer_tools import (
    GrammarCheckerTool,
    RedundancyDetectorTool,
    ToneValidatorTool
)


logger = logging.getLogger(__name__)


class ReviewerAgent:
    """
    Reviewer Agent - Refines content for clarity, consistency, and tone adherence using ReAct pattern.
    
    Responsibilities:
    - Remove redundancy across slides
    - Improve clarity and conciseness
    - Enforce tone consistency
    - Check for logical flow between slides
    - Use tools autonomously (grammar checker, redundancy detector, tone validator)
    - Iterate until quality threshold is met or max iterations reached
    
    ReAct Pattern:
    - Think: Reason about content quality and what to improve
    - Act: Use tools to check grammar, detect redundancy, and validate tone
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
        Initialize Reviewer Agent with ReAct capabilities.
        
        Args:
            llm: Optional LangChain LLM instance. If None, creates default.
            memory: Optional conversation memory for context retention
            cache: Optional intermediate results cache for cross-agent sharing
        """
        self.llm = llm or self._create_llm()
        self.memory = memory or ConversationMemory(agent_name="reviewer")
        self.cache = cache
        self.parser = PydanticOutputParser(pydantic_object=ReviewedContent)
        
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
                f"Reviewer Agent: Created Groq LLM with model {config.GROQ_MODEL} "
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
        Create tools for Reviewer Agent.
        
        Returns:
            List of LangChain Tool instances
        """
        # Instantiate tool implementations
        grammar_checker = GrammarCheckerTool()
        redundancy_detector = RedundancyDetectorTool()
        tone_validator = ToneValidatorTool()
        
        # Wrap in LangChain Tool format
        tools = [
            Tool(
                name=grammar_checker.name,
                func=grammar_checker.execute,
                description=grammar_checker.description
            ),
            Tool(
                name=redundancy_detector.name,
                func=redundancy_detector.execute,
                description=redundancy_detector.description
            ),
            Tool(
                name=tone_validator.name,
                func=tone_validator.execute,
                description=tone_validator.description
            )
        ]
        
        logger.info(
            f"Reviewer Agent: Initialized {len(tools)} tools: "
            f"{[t.name for t in tools]}"
        )
        return tools
    
    def _create_react_agent(self):
        """
        Create ReAct agent for Reviewer.
        
        Returns:
            ReAct agent instance
        """
        # ReAct prompt template
        react_prompt = PromptTemplate.from_template(
            """You are an expert content reviewer and editor agent. Your task is to refine and clean 
presentation content using the ReAct (Reasoning + Acting) pattern.

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

Guidelines for content review:
- Remove redundancy across slides
- Improve clarity and conciseness
- Ensure consistent tone throughout
- Fix grammatical errors
- Ensure logical flow between slides
- Maintain exactly 5-6 bullets per slide
- Keep the same structure (slide count, titles)
- Only modify content that needs improvement
- Preserve key information and facts

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
        
        logger.info("Reviewer Agent: ReAct agent created")
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
            f"Reviewer Agent: AgentExecutor created "
            f"(max_iterations={config.MAX_ITERATIONS})"
        )
        return executor
    
    def _create_fallback_prompt(self) -> ChatPromptTemplate:
        """
        Create fallback prompt for direct content review.
        
        This is used when the agent completes its reasoning but needs
        to format the final output as structured JSON.
        
        Returns:
            ChatPromptTemplate for fallback generation
        """
        template = """You are an expert content reviewer and editor for presentations.

Review and refine the following presentation content:

{content}

Tone: {tone}

Your tasks:
1. Remove redundancy across slides
2. Improve clarity and conciseness
3. Ensure consistent tone ({tone}) throughout
4. Fix grammatical errors
5. Ensure logical flow between slides
6. Maintain exactly 5-6 bullets per slide

Guidelines:
- Keep the same structure (slide count, titles)
- Only modify content that needs improvement
- Preserve key information and facts
- Ensure professional quality
- Add review notes explaining significant changes

{format_instructions}

Return ONLY valid JSON, no additional text."""

        return ChatPromptTemplate.from_messages([
            ("system", "You are an expert content reviewer and editor."),
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
                "content": lambda x: x["content"],
                "tone": lambda x: x["tone"],
                "format_instructions": lambda x: self.parser.get_format_instructions()
            }
            | self.fallback_prompt
            | self.llm
            | self.parser
        )
    
    async def review_content(
        self,
        content: GeneratedContent,
        tone: Optional[str] = None
    ) -> ReviewedContent:
        """
        Review and refine generated content using ReAct pattern.
        
        The agent will:
        1. Think about content quality issues
        2. Use grammar checker to identify grammatical errors
        3. Use redundancy detector to find repeated information
        4. Use tone validator to check consistency
        5. Iterate to improve quality if below threshold
        6. Return final reviewed content when quality threshold met or max iterations reached
        
        Args:
            content: Generated content from Content Agent
            tone: Optional tone (formal, casual, fun, professional)
            
        Returns:
            ReviewedContent with refined and cleaned content
            
        Raises:
            asyncio.TimeoutError: If review exceeds timeout
            ValueError: If output validation fails
        """
        tone = tone or "professional"
        
        logger.info(
            f"Reviewer Agent: Reviewing content for {len(content.slides)} slides "
            f"({tone} tone) using ReAct pattern"
        )
        
        try:
            # Run with timeout (Python 3.9 compatible)
            reviewed = await asyncio.wait_for(
                self._review_with_react(
                    content=content,
                    tone=tone
                ),
                timeout=config.REVIEWER_TIMEOUT
            )
                
            # Validate structure preservation
            if len(reviewed.slides) != len(content.slides):
                raise ValueError(
                    f"Slide count changed during review: "
                    f"{len(content.slides)} -> {len(reviewed.slides)}"
                )
            
            # Validate bullet point count (3-6 per slide)
            for slide in reviewed.slides:
                bullet_count = len(slide.bullets)
                if bullet_count < 3 or bullet_count > 6:
                    raise ValueError(
                        f"Slide {slide.slide_number} has {bullet_count} bullets after review, "
                        f"expected 3-6"
                    )
            
            # Store in cache if available
            if self.cache:
                self.cache.store(
                    key="reviewed",
                    value=reviewed,
                    agent_name="reviewer"
                )
                logger.info("Reviewer Agent: Stored reviewed content in cache")
            
            logger.info(
                f"Reviewer Agent: Successfully reviewed {len(reviewed.slides)} slides"
            )
            
            return reviewed
            
        except asyncio.TimeoutError:
            logger.error(
                f"Reviewer Agent: Timeout after {config.REVIEWER_TIMEOUT}s"
            )
            raise
        except Exception as e:
            logger.error(f"Reviewer Agent: Failed to review content: {str(e)}")
            raise
    
    async def _review_with_react(
        self,
        content: GeneratedContent,
        tone: str
    ) -> ReviewedContent:
        """
        Review content using ReAct agent with quality-based iteration.
        
        Args:
            content: Generated content
            tone: Presentation tone
            
        Returns:
            ReviewedContent
            
        Raises:
            Exception: If review fails
        """
        # Format content as JSON string for prompt
        content_str = json.dumps({
            "slides": [
                {
                    "slide_number": slide.slide_number,
                    "title": slide.title,
                    "bullets": slide.bullets
                }
                for slide in content.slides
            ]
        }, indent=2)
        
        # Retrieve cached Content results if available
        cached_content_context = ""
        if self.cache and self.cache.has("content"):
            cached_content_context = "\n\nNote: The content was generated by the Content Agent and is available in the cache."
        
        # Prepare agent input
        agent_input = (
            f"Review and refine presentation content for a {tone} presentation. "
            f"Use the available tools to check grammar, detect redundancy, and validate tone consistency. "
            f"Iterate until the quality score is at least {int(config.QUALITY_THRESHOLD * 100)}/100 "
            f"or you reach the maximum iterations.{cached_content_context}\n\n"
            f"Content:\n{content_str}"
        )
        
        # Add format instructions to agent input
        format_instructions = self.parser.get_format_instructions()
        agent_input += f"\n\n{format_instructions}"
        
        # Add memory context if available
        if self.memory and len(self.memory) > 0:
            context = self.memory.get_context()
            agent_input = f"Previous context:\n{context}\n\n{agent_input}"
        
        logger.info("Reviewer Agent: Starting ReAct reasoning loop")
        
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
                        f"Reviewer Agent: Groq API rate limit exceeded: {str(e)}"
                    )
                    raise GenerationError(
                        "Groq API rate limit exceeded. Please wait a moment and try again.",
                        agent="Reviewer"
                    )
                except APITimeoutError as e:
                    logger.error(
                        f"Reviewer Agent: Groq API timeout: {str(e)}"
                    )
                    raise GenerationError(
                        "Groq API request timed out. The service may be slow or unavailable.",
                        agent="Reviewer"
                    )
                except APIError as e:
                    logger.error(
                        f"Reviewer Agent: Groq API error: {str(e)}"
                    )
                    if hasattr(e, 'status_code') and e.status_code == 503:
                        raise GenerationError(
                            "Groq API service is temporarily unavailable. Please try again later.",
                            agent="Reviewer"
                        )
                    else:
                        raise GenerationError(
                            f"Groq API error: {str(e)}",
                            agent="Reviewer"
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
            reviewed = self._parse_agent_output(final_answer, content, tone)
            
            # Store interaction in memory
            self.memory.add_message("human", agent_input)
            self.memory.add_message("ai", final_answer)
            
            return reviewed
            
        except Exception as e:
            logger.error(f"Reviewer Agent: ReAct generation failed: {str(e)}")
            logger.info("Reviewer Agent: Falling back to direct generation")
            
            # Fallback to direct generation
            return await self._fallback_generation(content, tone)
    
    def _parse_agent_output(
        self,
        output: str,
        content: GeneratedContent,
        tone: str
    ) -> ReviewedContent:
        """
        Parse agent output into ReviewedContent.
        
        Args:
            output: Agent's final answer
            content: Generated content (for fallback)
            tone: Presentation tone (for fallback)
            
        Returns:
            ReviewedContent
            
        Raises:
            Exception: If parsing fails completely
        """
        try:
            # Try to extract JSON from the output
            # Look for JSON object in the text
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                reviewed_dict = json.loads(json_str)
                reviewed = self.parser.parse(json_str)
                logger.info("Reviewer Agent: Successfully parsed agent output")
                return reviewed
            else:
                logger.warning("Reviewer Agent: No JSON found in agent output")
                raise ValueError("No JSON found in output")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                f"Reviewer Agent: Failed to parse agent output: {str(e)}, "
                f"using fallback generation"
            )
            # Use fallback - this will be handled by caller
            raise
    
    async def _fallback_generation(
        self,
        content: GeneratedContent,
        tone: str
    ) -> ReviewedContent:
        """
        Fallback to direct generation without ReAct loop.
        
        Args:
            content: Generated content
            tone: Presentation tone
            
        Returns:
            ReviewedContent
        """
        logger.info("Reviewer Agent: Using fallback chain for direct generation")
        
        try:
            # Format content as JSON string for prompt
            content_str = json.dumps({
                "slides": [
                    {
                        "slide_number": slide.slide_number,
                        "title": slide.title,
                        "bullets": slide.bullets
                    }
                    for slide in content.slides
                ]
            }, indent=2)
            
            reviewed = await self.fallback_chain.ainvoke({
                "content": content_str,
                "tone": tone
            })
            
            logger.info("Reviewer Agent: Fallback generation successful")
            return reviewed
            
        except Exception as e:
            logger.error(f"Reviewer Agent: Fallback generation failed: {str(e)}")
            raise
    
    def _log_reasoning_trace(self, result: Dict[str, Any]) -> None:
        """
        Log the agent's reasoning trace.
        
        Args:
            result: Agent execution result with intermediate steps
        """
        intermediate_steps = result.get("intermediate_steps", [])
        
        if not intermediate_steps:
            logger.info("Reviewer Agent: No intermediate steps recorded")
            return
        
        logger.info(
            f"Reviewer Agent: Reasoning trace ({len(intermediate_steps)} steps):"
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
            f"Reviewer Agent: Completed in {len(intermediate_steps)} iterations "
            f"(max: {config.MAX_ITERATIONS})"
        )
        
        # Log tool invocation summary
        logger.info(f"Reviewer Agent: Total tool invocations: {tool_invocation_count}")
        for tool_name, count in tool_durations.items():
            logger.info(f"Reviewer Agent: Tool '{tool_name}' invoked {count} times")
