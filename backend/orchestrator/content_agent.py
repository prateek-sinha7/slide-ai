"""Content Agent for generating detailed slide content using ReAct pattern."""
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

from orchestrator.models import SlideOutline, GeneratedContent
from orchestrator.config import config
from orchestrator.memory import ConversationMemory, IntermediateResultsCache
from orchestrator.exceptions import GenerationError
from orchestrator.tools.content_tools import (
    FactCheckerTool,
    LengthValidatorTool,
    BulletQualityScorer
)


logger = logging.getLogger(__name__)


class ContentAgent:
    """
    Content Agent - Generates detailed bullet points for each slide using ReAct pattern.
    
    Responsibilities:
    - Generate exactly 5-6 concise bullet points per slide
    - Apply tone parameter to content generation
    - Ensure content is relevant and actionable
    - Use tools autonomously (fact checking, length validation, quality scoring)
    - Iterate until quality threshold is met or max iterations reached
    
    ReAct Pattern:
    - Think: Reason about content quality and what to improve
    - Act: Use tools to verify facts, validate length, and score quality
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
        Initialize Content Agent with ReAct capabilities.
        
        Args:
            llm: Optional LangChain LLM instance. If None, creates default.
            memory: Optional conversation memory for context retention
            cache: Optional intermediate results cache for cross-agent sharing
        """
        self.llm = llm or self._create_llm()
        self.memory = memory or ConversationMemory(agent_name="content")
        self.cache = cache
        self.parser = PydanticOutputParser(pydantic_object=GeneratedContent)
        
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
                f"Content Agent: Created Groq LLM with model {config.GROQ_MODEL} "
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
        Create tools for Content Agent.
        
        Returns:
            List of LangChain Tool instances
        """
        # Instantiate tool implementations
        fact_checker = FactCheckerTool()
        length_validator = LengthValidatorTool()
        quality_scorer = BulletQualityScorer()
        
        # Wrap in LangChain Tool format (FactCheckerTool removed to avoid rate limits)
        tools = [
            Tool(
                name=length_validator.name,
                func=length_validator.execute,
                description=length_validator.description
            ),
            Tool(
                name=quality_scorer.name,
                func=quality_scorer.execute,
                description=quality_scorer.description
            )
        ]
        
        logger.info(
            f"Content Agent: Initialized {len(tools)} tools: "
            f"{[t.name for t in tools]}"
        )
        return tools
    
    def _create_react_agent(self):
        """
        Create ReAct agent for Content.
        
        Returns:
            ReAct agent instance
        """
        # ReAct prompt template
        react_prompt = PromptTemplate.from_template(
            """You are an expert content writer agent for presentation slides. Your task is to generate 
detailed, high-quality bullet points for each slide using the ReAct (Reasoning + Acting) pattern.

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

Guidelines for content generation:
- Each bullet point should be 10-15 words maximum
- Focus on clarity and impact
- Use active voice
- Include specific details, statistics, or examples where relevant
- Ensure bullets flow logically within each slide
- Each slide must have exactly 5-6 bullet points

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
        
        logger.info("Content Agent: ReAct agent created")
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
            f"Content Agent: AgentExecutor created "
            f"(max_iterations={config.MAX_ITERATIONS})"
        )
        return executor
    
    def _create_fallback_prompt(self) -> ChatPromptTemplate:
        """
        Create fallback prompt for direct content generation.
        
        This is used when the agent completes its reasoning but needs
        to format the final output as structured JSON.
        
        Returns:
            ChatPromptTemplate for fallback generation
        """
        template = """You are an expert content writer specializing in presentation slides.

For each slide in the outline below, generate EXACTLY 5-6 concise bullet points.

Outline:
{outline}

Tone: {tone}

Guidelines:
- Each bullet point should be 10-15 words maximum
- Focus on clarity and impact
- Use active voice
- Include specific details, statistics, or examples where relevant
- Ensure bullets flow logically within each slide
- Match the {tone} tone throughout

{format_instructions}

CRITICAL: Each slide must have exactly 5-6 bullet points, no more, no less.
Return ONLY valid JSON, no additional text."""

        return ChatPromptTemplate.from_messages([
            ("system", "You are an expert content writer for presentations."),
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
                "outline": lambda x: x["outline"],
                "tone": lambda x: x["tone"],
                "format_instructions": lambda x: self.parser.get_format_instructions()
            }
            | self.fallback_prompt
            | self.llm
            | self.parser
        )
    
    async def generate_content(
        self,
        outline: SlideOutline,
        tone: Optional[str] = None
    ) -> GeneratedContent:
        """
        Generate detailed content for each slide using ReAct pattern.
        
        The agent will:
        1. Think about the content requirements for each slide
        2. Generate initial bullet points
        3. Optionally use fact checker to verify claims
        4. Use length validator to ensure bullet points are 10-15 words
        5. Use quality scorer to evaluate clarity, impact, and specificity
        6. Iterate to improve quality if below threshold
        7. Return final content when quality threshold met or max iterations reached
        
        Args:
            outline: Slide outline from Planner Agent
            tone: Optional tone (formal, casual, fun, professional)
            
        Returns:
            GeneratedContent with 5-6 bullet points per slide
            
        Raises:
            asyncio.TimeoutError: If generation exceeds timeout
            ValueError: If bullet point count constraint is violated
        """
        tone = tone or "professional"
        
        logger.info(
            f"Content Agent: Generating content for {len(outline.outline)} slides "
            f"({tone} tone) using ReAct pattern"
        )
        
        try:
            # Run with timeout (Python 3.9 compatible)
            content = await asyncio.wait_for(
                self._generate_with_react(
                    outline=outline,
                    tone=tone
                ),
                timeout=config.CONTENT_TIMEOUT
            )
                
            # Validate bullet point count (3-6 per slide)
            for slide in content.slides:
                bullet_count = len(slide.bullets)
                if bullet_count < 3 or bullet_count > 6:
                    raise ValueError(
                        f"Slide {slide.slide_number} has {bullet_count} bullets, "
                        f"expected 3-6"
                    )
            
            # Store in cache if available
            if self.cache:
                self.cache.store(
                    key="content",
                    value=content,
                    agent_name="content"
                )
                logger.info("Content Agent: Stored content in cache")
            
            logger.info(
                f"Content Agent: Successfully generated content for "
                f"{len(content.slides)} slides"
            )
            
            return content
            
        except asyncio.TimeoutError:
            logger.error(
                f"Content Agent: Timeout after {config.CONTENT_TIMEOUT}s"
            )
            raise
        except Exception as e:
            logger.error(f"Content Agent: Failed to generate content: {str(e)}")
            raise
    
    async def _generate_with_react(
        self,
        outline: SlideOutline,
        tone: str
    ) -> GeneratedContent:
        """
        Generate content using ReAct agent with quality-based iteration.
        
        Args:
            outline: Slide outline
            tone: Presentation tone
            
        Returns:
            GeneratedContent
            
        Raises:
            Exception: If generation fails
        """
        # Format outline as JSON string for prompt
        outline_str = json.dumps({
            "title": outline.title,
            "subtitle": outline.subtitle,
            "slides": [
                {
                    "slide_number": item.slide_number,
                    "title": item.title,
                    "key_points": item.key_points
                }
                for item in outline.outline
            ]
        }, indent=2)
        
        # Retrieve cached Planner results if available
        cached_outline_context = ""
        if self.cache and self.cache.has("outline"):
            cached_outline_context = "\n\nNote: The outline was created by the Planner Agent and is available in the cache."
        
        # Prepare agent input
        agent_input = (
            f"Generate detailed slide content with 5-6 bullet points per slide for a {tone} presentation. "
            f"Use the available tools to validate length, check quality, and optionally verify facts. "
            f"Iterate until the quality score is at least {int(config.QUALITY_THRESHOLD * 100)}/100 "
            f"or you reach the maximum iterations.{cached_outline_context}\n\n"
            f"Outline:\n{outline_str}"
        )
        
        # Add format instructions to agent input
        format_instructions = self.parser.get_format_instructions()
        agent_input += f"\n\n{format_instructions}"
        
        # Add memory context if available
        if self.memory and len(self.memory) > 0:
            context = self.memory.get_context()
            agent_input = f"Previous context:\n{context}\n\n{agent_input}"
        
        logger.info("Content Agent: Starting ReAct reasoning loop")
        
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
                        f"Content Agent: Groq API rate limit exceeded: {str(e)}"
                    )
                    raise GenerationError(
                        "Groq API rate limit exceeded. Please wait a moment and try again.",
                        agent="Content"
                    )
                except APITimeoutError as e:
                    logger.error(
                        f"Content Agent: Groq API timeout: {str(e)}"
                    )
                    raise GenerationError(
                        "Groq API request timed out. The service may be slow or unavailable.",
                        agent="Content"
                    )
                except APIError as e:
                    logger.error(
                        f"Content Agent: Groq API error: {str(e)}"
                    )
                    if hasattr(e, 'status_code') and e.status_code == 503:
                        raise GenerationError(
                            "Groq API service is temporarily unavailable. Please try again later.",
                            agent="Content"
                        )
                    else:
                        raise GenerationError(
                            f"Groq API error: {str(e)}",
                            agent="Content"
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
            content = self._parse_agent_output(final_answer, outline, tone)
            
            # Store interaction in memory
            self.memory.add_message("human", agent_input)
            self.memory.add_message("ai", final_answer)
            
            return content
            
        except Exception as e:
            logger.error(f"Content Agent: ReAct generation failed: {str(e)}")
            logger.info("Content Agent: Falling back to direct generation")
            
            # Fallback to direct generation
            return await self._fallback_generation(outline, tone)
    
    def _parse_agent_output(
        self,
        output: str,
        outline: SlideOutline,
        tone: str
    ) -> GeneratedContent:
        """
        Parse agent output into GeneratedContent.
        
        Args:
            output: Agent's final answer
            outline: Slide outline (for fallback)
            tone: Presentation tone (for fallback)
            
        Returns:
            GeneratedContent
            
        Raises:
            Exception: If parsing fails completely
        """
        try:
            # Try to extract JSON from the output
            # Look for JSON object in the text
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                content_dict = json.loads(json_str)
                content = self.parser.parse(json_str)
                logger.info("Content Agent: Successfully parsed agent output")
                return content
            else:
                logger.warning("Content Agent: No JSON found in agent output")
                raise ValueError("No JSON found in output")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                f"Content Agent: Failed to parse agent output: {str(e)}, "
                f"using fallback generation"
            )
            # Use fallback - this will be handled by caller
            raise
    
    async def _fallback_generation(
        self,
        outline: SlideOutline,
        tone: str
    ) -> GeneratedContent:
        """
        Fallback to direct generation without ReAct loop.
        
        Args:
            outline: Slide outline
            tone: Presentation tone
            
        Returns:
            GeneratedContent
        """
        logger.info("Content Agent: Using fallback chain for direct generation")
        
        try:
            # Format outline as JSON string for prompt
            outline_str = json.dumps({
                "title": outline.title,
                "subtitle": outline.subtitle,
                "slides": [
                    {
                        "slide_number": item.slide_number,
                        "title": item.title,
                        "key_points": item.key_points
                    }
                    for item in outline.outline
                ]
            }, indent=2)
            
            content = await self.fallback_chain.ainvoke({
                "outline": outline_str,
                "tone": tone
            })
            
            logger.info("Content Agent: Fallback generation successful")
            return content
            
        except Exception as e:
            logger.error(f"Content Agent: Fallback generation failed: {str(e)}")
            raise
    
    def _log_reasoning_trace(self, result: Dict[str, Any]) -> None:
        """
        Log the agent's reasoning trace.
        
        Args:
            result: Agent execution result with intermediate steps
        """
        intermediate_steps = result.get("intermediate_steps", [])
        
        if not intermediate_steps:
            logger.info("Content Agent: No intermediate steps recorded")
            return
        
        logger.info(
            f"Content Agent: Reasoning trace ({len(intermediate_steps)} steps):"
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
            f"Content Agent: Completed in {len(intermediate_steps)} iterations "
            f"(max: {config.MAX_ITERATIONS})"
        )
        
        # Log tool invocation summary
        logger.info(f"Content Agent: Total tool invocations: {tool_invocation_count}")
        for tool_name, count in tool_durations.items():
            logger.info(f"Content Agent: Tool '{tool_name}' invoked {count} times")
