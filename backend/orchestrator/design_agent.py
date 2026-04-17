"""Design Agent for assigning slide types and layout metadata using ReAct pattern."""
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

from orchestrator.models import ReviewedContent, DesignedContent, SlideOutline
from orchestrator.config import config
from orchestrator.memory import ConversationMemory, IntermediateResultsCache
from orchestrator.exceptions import GenerationError
from orchestrator.tools.design_tools import (
    LayoutRecommenderTool,
    BalanceCheckerTool,
    NotesGeneratorTool
)


logger = logging.getLogger(__name__)


class DesignAgent:
    """
    Design Agent - Assigns slide types and provides layout recommendations using ReAct pattern.
    
    Responsibilities:
    - Assign slide types (content_slide, comparison_slide, conclusion_slide)
    - Recommend layouts (bullet_list, two_column, title_only, image_placeholder)
    - Generate speaker notes for each slide
    - Create title, agenda, and summary slide metadata
    - Use tools autonomously (layout recommender, balance checker, notes generator)
    - Iterate until quality threshold is met or max iterations reached
    
    ReAct Pattern:
    - Think: Reason about design choices and what to improve
    - Act: Use tools to recommend layouts, check balance, and generate notes
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
        Initialize Design Agent with ReAct capabilities.
        
        Args:
            llm: Optional LangChain LLM instance. If None, creates default.
            memory: Optional conversation memory for context retention
            cache: Optional intermediate results cache for cross-agent sharing
        """
        self.llm = llm or self._create_llm()
        self.memory = memory or ConversationMemory(agent_name="design")
        self.cache = cache
        self.parser = PydanticOutputParser(pydantic_object=DesignedContent)
        
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
                f"Design Agent: Created Groq LLM with model {config.GROQ_MODEL} "
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
        Create tools for Design Agent.
        
        Returns:
            List of LangChain Tool instances
        """
        # Instantiate tool implementations
        layout_recommender = LayoutRecommenderTool()
        balance_checker = BalanceCheckerTool()
        notes_generator = NotesGeneratorTool()
        
        # Wrap in LangChain Tool format
        tools = [
            Tool(
                name=layout_recommender.name,
                func=layout_recommender.execute,
                description=layout_recommender.description
            ),
            Tool(
                name=balance_checker.name,
                func=balance_checker.execute,
                description=balance_checker.description
            ),
            Tool(
                name=notes_generator.name,
                func=notes_generator.execute,
                description=notes_generator.description
            )
        ]
        
        logger.info(
            f"Design Agent: Initialized {len(tools)} tools: "
            f"{[t.name for t in tools]}"
        )
        return tools
    
    def _create_react_agent(self):
        """
        Create ReAct agent for Design.
        
        Returns:
            ReAct agent instance
        """
        # ReAct prompt template
        react_prompt = PromptTemplate.from_template(
            """You are an expert presentation design agent. Your task is to assign slide types, 
recommend layouts, and generate speaker notes using the ReAct (Reasoning + Acting) pattern.

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

Guidelines for design assignment:
- Assign appropriate slide types: content_slide, comparison_slide, conclusion_slide
- Recommend layouts: bullet_list, two_column, title_only, image_placeholder
- Generate 2-3 sentence speaker notes for each slide
- Create title slide with given title and subtitle
- Create agenda slide from slide titles
- Create summary slide with given summary points
- Ensure visual balance across slides

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
        
        logger.info("Design Agent: ReAct agent created")
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
            f"Design Agent: AgentExecutor created "
            f"(max_iterations={config.MAX_ITERATIONS})"
        )
        return executor
    
    def _create_fallback_prompt(self) -> ChatPromptTemplate:
        """
        Create fallback prompt for direct design assignment.
        
        This is used when the agent completes its reasoning but needs
        to format the final output as structured JSON.
        
        Returns:
            ChatPromptTemplate for fallback generation
        """
        template = """You are a presentation design expert. Analyze the content and assign 
appropriate slide types and layouts.

Title: {title}
Subtitle: {subtitle}

Content:
{content}

Summary Points:
{summary_points}

Your tasks:
1. Create title slide with the given title and subtitle
2. Create agenda slide from the slide titles
3. Assign slide types: content_slide, comparison_slide, conclusion_slide
4. Recommend layouts: bullet_list, two_column, title_only, image_placeholder
5. Generate speaker notes for each slide (2-3 sentences)
6. Create summary slide with the given summary points

{format_instructions}

Return ONLY valid JSON, no additional text."""

        return ChatPromptTemplate.from_messages([
            ("system", "You are a presentation design expert."),
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
                "title": lambda x: x["title"],
                "subtitle": lambda x: x["subtitle"],
                "content": lambda x: x["content"],
                "summary_points": lambda x: x["summary_points"],
                "format_instructions": lambda x: self.parser.get_format_instructions()
            }
            | self.fallback_prompt
            | self.llm
            | self.parser
        )
    
    async def assign_design(
        self,
        reviewed_content: ReviewedContent,
        outline: SlideOutline
    ) -> DesignedContent:
        """
        Assign design metadata to reviewed content using ReAct pattern.
        
        The agent will:
        1. Think about appropriate slide types and layouts
        2. Use layout recommender to suggest layouts for each slide
        3. Use balance checker to evaluate content distribution
        4. Use notes generator to create speaker notes
        5. Iterate to improve design quality if below threshold
        6. Return final design when quality threshold met or max iterations reached
        
        Args:
            reviewed_content: Reviewed content from Reviewer Agent
            outline: Original outline from Planner Agent (for title and summary)
            
        Returns:
            DesignedContent with slide types, layouts, and speaker notes
            
        Raises:
            asyncio.TimeoutError: If design assignment exceeds timeout
            ValueError: If output validation fails
        """
        logger.info(
            f"Design Agent: Assigning design metadata for {len(reviewed_content.slides)} slides "
            f"using ReAct pattern"
        )
        
        try:
            # Run with timeout (Python 3.9 compatible)
            designed = await asyncio.wait_for(
                self._assign_with_react(
                    reviewed_content=reviewed_content,
                    outline=outline
                ),
                timeout=config.DESIGN_TIMEOUT
            )
                
            # Validate structure (allow slight mismatch for local models)
            expected_count = len(reviewed_content.slides)
            actual_count = len(designed.content_slides)
            
            if actual_count < expected_count - 1 or actual_count > expected_count:
                # If more than 1 slide off, it's a real error
                raise ValueError(
                    f"Slide count mismatch: "
                    f"{expected_count} -> {actual_count}"
                )
            
            # If we're missing exactly 1 slide, create a default one
            if actual_count == expected_count - 1:
                logger.warning(
                    f"Design Agent: Missing 1 slide, creating default design for slide {expected_count}"
                )
                # Add default design for missing slide
                missing_slide = reviewed_content.slides[actual_count]
                from orchestrator.models import SlideMetadata
                default_slide = SlideMetadata(
                    slide_number=missing_slide.slide_number,
                    title=missing_slide.title,
                    bullets=missing_slide.bullets,
                    layout="bullet_list",
                    slide_type="content_slide",
                    speaker_notes=f"Present the key points about {missing_slide.title}."
                )
                designed.content_slides.append(default_slide)
            
            # Validate all slides have speaker notes
            for slide in designed.content_slides:
                if not slide.speaker_notes or len(slide.speaker_notes) < 10:
                    # Add default speaker notes if missing
                    slide.speaker_notes = f"Present the key points about {slide.title}."
            
            # Store in cache if available
            if self.cache:
                self.cache.store(
                    key="designed",
                    value=designed,
                    agent_name="design"
                )
                logger.info("Design Agent: Stored designed content in cache")
            
            logger.info(
                f"Design Agent: Successfully assigned design metadata for "
                f"{len(designed.content_slides)} slides"
            )
            
            return designed
            
        except asyncio.TimeoutError:
            logger.error(
                f"Design Agent: Timeout after {config.DESIGN_TIMEOUT}s"
            )
            raise
        except Exception as e:
            logger.error(f"Design Agent: Failed to assign design: {str(e)}")
            raise
    
    async def _assign_with_react(
        self,
        reviewed_content: ReviewedContent,
        outline: SlideOutline
    ) -> DesignedContent:
        """
        Assign design using ReAct agent with quality-based iteration.
        
        Args:
            reviewed_content: Reviewed content
            outline: Original outline
            
        Returns:
            DesignedContent
            
        Raises:
            Exception: If generation fails
        """
        # Format content as JSON string for prompt
        content_str = json.dumps({
            "slides": [
                {
                    "slide_number": slide.slide_number,
                    "title": slide.title,
                    "bullets": slide.bullets
                }
                for slide in reviewed_content.slides
            ]
        }, indent=2)
        
        # Retrieve cached Reviewer results if available
        cached_reviewer_context = ""
        if self.cache and self.cache.has("reviewed"):
            cached_reviewer_context = "\n\nNote: The content was reviewed by the Reviewer Agent and is available in the cache."
        
        # Prepare agent input
        agent_input = (
            f"Assign design metadata (slide types, layouts, speaker notes) for a presentation. "
            f"Use the available tools to recommend layouts, check balance, and generate notes. "
            f"Iterate until the design quality is at least {int(config.QUALITY_THRESHOLD * 100)}/100 "
            f"or you reach the maximum iterations.{cached_reviewer_context}\n\n"
            f"Title: {outline.title}\n"
            f"Subtitle: {outline.subtitle or ''}\n\n"
            f"Content:\n{content_str}\n\n"
            f"Summary Points: {json.dumps(outline.summary_points)}"
        )
        
        # Add format instructions to agent input
        format_instructions = self.parser.get_format_instructions()
        agent_input += f"\n\n{format_instructions}"
        
        # Add memory context if available
        if self.memory and len(self.memory) > 0:
            context = self.memory.get_context()
            agent_input = f"Previous context:\n{context}\n\n{agent_input}"
        
        logger.info("Design Agent: Starting ReAct reasoning loop")
        
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
                        f"Design Agent: Groq API rate limit exceeded: {str(e)}"
                    )
                    raise GenerationError(
                        "Groq API rate limit exceeded. Please wait a moment and try again.",
                        agent="Design"
                    )
                except APITimeoutError as e:
                    logger.error(
                        f"Design Agent: Groq API timeout: {str(e)}"
                    )
                    raise GenerationError(
                        "Groq API request timed out. The service may be slow or unavailable.",
                        agent="Design"
                    )
                except APIError as e:
                    logger.error(
                        f"Design Agent: Groq API error: {str(e)}"
                    )
                    if hasattr(e, 'status_code') and e.status_code == 503:
                        raise GenerationError(
                            "Groq API service is temporarily unavailable. Please try again later.",
                            agent="Design"
                        )
                    else:
                        raise GenerationError(
                            f"Groq API error: {str(e)}",
                            agent="Design"
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
            designed = self._parse_agent_output(
                final_answer,
                reviewed_content,
                outline
            )
            
            # Store interaction in memory
            self.memory.add_message("human", agent_input)
            self.memory.add_message("ai", final_answer)
            
            return designed
            
        except Exception as e:
            logger.error(f"Design Agent: ReAct generation failed: {str(e)}")
            logger.info("Design Agent: Falling back to direct generation")
            
            # Fallback to direct generation
            return await self._fallback_generation(
                reviewed_content,
                outline
            )
    
    def _parse_agent_output(
        self,
        output: str,
        reviewed_content: ReviewedContent,
        outline: SlideOutline
    ) -> DesignedContent:
        """
        Parse agent output into DesignedContent.
        
        Args:
            output: Agent's final answer
            reviewed_content: Reviewed content (for fallback)
            outline: Slide outline (for fallback)
            
        Returns:
            DesignedContent
            
        Raises:
            Exception: If parsing fails completely
        """
        try:
            # Try to extract JSON from the output
            # Look for JSON object in the text
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                designed_dict = json.loads(json_str)
                designed = self.parser.parse(json_str)
                logger.info("Design Agent: Successfully parsed agent output")
                return designed
            else:
                logger.warning("Design Agent: No JSON found in agent output")
                raise ValueError("No JSON found in output")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                f"Design Agent: Failed to parse agent output: {str(e)}, "
                f"using fallback generation"
            )
            # Use fallback - this will be handled by caller
            raise
    
    async def _fallback_generation(
        self,
        reviewed_content: ReviewedContent,
        outline: SlideOutline
    ) -> DesignedContent:
        """
        Fallback to direct generation without ReAct loop.
        
        Args:
            reviewed_content: Reviewed content
            outline: Original outline
            
        Returns:
            DesignedContent
        """
        logger.info("Design Agent: Using fallback chain for direct generation")
        
        try:
            # Format content as JSON string for prompt
            content_str = json.dumps({
                "slides": [
                    {
                        "slide_number": slide.slide_number,
                        "title": slide.title,
                        "bullets": slide.bullets
                    }
                    for slide in reviewed_content.slides
                ]
            }, indent=2)
            
            designed = await self.fallback_chain.ainvoke({
                "title": outline.title,
                "subtitle": outline.subtitle or "",
                "content": content_str,
                "summary_points": json.dumps(outline.summary_points)
            })
            
            logger.info("Design Agent: Fallback generation successful")
            return designed
            
        except Exception as e:
            logger.error(f"Design Agent: Fallback generation failed: {str(e)}")
            raise
    
    def _log_reasoning_trace(self, result: Dict[str, Any]) -> None:
        """
        Log the agent's reasoning trace.
        
        Args:
            result: Agent execution result with intermediate steps
        """
        intermediate_steps = result.get("intermediate_steps", [])
        
        if not intermediate_steps:
            logger.info("Design Agent: No intermediate steps recorded")
            return
        
        logger.info(
            f"Design Agent: Reasoning trace ({len(intermediate_steps)} steps):"
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
            f"Design Agent: Completed in {len(intermediate_steps)} iterations "
            f"(max: {config.MAX_ITERATIONS})"
        )
        
        # Log tool invocation summary
        logger.info(f"Design Agent: Total tool invocations: {tool_invocation_count}")
        for tool_name, count in tool_durations.items():
            logger.info(f"Design Agent: Tool '{tool_name}' invoked {count} times")
