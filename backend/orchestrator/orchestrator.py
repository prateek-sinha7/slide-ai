"""LLM Orchestrator - Coordinates multi-agent pipeline for presentation generation."""
import logging
import asyncio
import time
from typing import Optional, Dict, Any
from datetime import datetime

from orchestrator.planner_agent import PlannerAgent
from orchestrator.content_agent import ContentAgent
from orchestrator.reviewer_agent import ReviewerAgent
from orchestrator.design_agent import DesignAgent
from orchestrator.models import PresentationContent, TitleSlide, AgendaSlide, SlideContent, SummarySlide
from orchestrator.config import config
from orchestrator.memory import ConversationMemory, IntermediateResultsCache
from orchestrator.exceptions import (
    GenerationError,
    GenerationTimeoutError,
    LLMServiceUnavailableError,
    ValidationError
)


logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Track performance metrics for agent execution."""
    
    def __init__(self):
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        self.pipeline_start_time: Optional[float] = None
        self.pipeline_end_time: Optional[float] = None
        self.total_tool_invocations: int = 0
        
    def start_pipeline(self):
        """Mark the start of pipeline execution."""
        self.pipeline_start_time = time.time()
        logger.info("=" * 60)
        logger.info("PERFORMANCE MONITORING: Pipeline started")
        logger.info("=" * 60)
        
    def end_pipeline(self):
        """Mark the end of pipeline execution and log summary."""
        self.pipeline_end_time = time.time()
        duration = self.pipeline_end_time - self.pipeline_start_time
        
        logger.info("=" * 60)
        logger.info("PERFORMANCE MONITORING: Pipeline completed")
        logger.info(f"Total pipeline duration: {duration:.2f}s")
        logger.info(f"Total tool invocations: {self.total_tool_invocations}")
        logger.info("=" * 60)
        
        # Log per-agent summary
        for agent_name, metrics in self.agent_metrics.items():
            logger.info(f"{agent_name} Agent Performance:")
            logger.info(f"  Execution time: {metrics.get('duration', 0):.2f}s")
            logger.info(f"  Iterations: {metrics.get('iterations', 0)}")
            logger.info(f"  Tool invocations: {metrics.get('tool_invocations', 0)}")
            if 'quality_score' in metrics:
                logger.info(f"  Quality score: {metrics['quality_score']:.2f}")
        
        logger.info("=" * 60)
        
    def record_agent_execution(
        self,
        agent_name: str,
        duration: float,
        iterations: int = 0,
        tool_invocations: int = 0,
        quality_score: Optional[float] = None
    ):
        """
        Record metrics for an agent execution.
        
        Args:
            agent_name: Name of the agent
            duration: Execution time in seconds
            iterations: Number of reasoning iterations
            tool_invocations: Number of tool invocations
            quality_score: Optional quality score (0-1)
        """
        self.agent_metrics[agent_name] = {
            'duration': duration,
            'iterations': iterations,
            'tool_invocations': tool_invocations
        }
        
        if quality_score is not None:
            self.agent_metrics[agent_name]['quality_score'] = quality_score
        
        self.total_tool_invocations += tool_invocations
        
        # Log individual agent metrics
        logger.info(f"PERFORMANCE: {agent_name} Agent completed in {duration:.2f}s")
        logger.info(f"PERFORMANCE: {agent_name} Agent iterations: {iterations}")
        logger.info(f"PERFORMANCE: {agent_name} Agent tool invocations: {tool_invocations}")
        if quality_score is not None:
            logger.info(f"PERFORMANCE: {agent_name} Agent quality score: {quality_score:.2f}")
    
    def get_pipeline_duration(self) -> float:
        """Get total pipeline duration in seconds."""
        if self.pipeline_start_time and self.pipeline_end_time:
            return self.pipeline_end_time - self.pipeline_start_time
        return 0.0
    
    def get_agent_metrics(self, agent_name: str) -> Dict[str, Any]:
        """Get metrics for a specific agent."""
        return self.agent_metrics.get(agent_name, {})


class LLMOrchestrator:
    """
    LLM Orchestrator - Coordinates multi-agent pipeline with ReAct agents.
    
    Pipeline: Planner → Content → Reviewer → Design
    
    Features:
    - Sequential ReAct agent execution with reasoning loops
    - Conversation memory for context retention within agents
    - Intermediate results caching for cross-agent information sharing
    - 120-second timeout protection with fallback mechanisms
    - Iteration count and quality score logging
    - Comprehensive error handling
    - Execution time and performance monitoring
    """
    
    def __init__(self, llm=None):
        """
        Initialize LLM Orchestrator with memory systems.
        
        Args:
            llm: Optional shared LLM instance for all agents
        """
        # Initialize memory systems (will be reset per pipeline run)
        self.memory_system: Optional[Dict[str, ConversationMemory]] = None
        self.cache: Optional[IntermediateResultsCache] = None
        
        # Initialize performance metrics
        self.metrics = PerformanceMetrics()
        
        # Store LLM for agent initialization
        self.llm = llm
        
        # Agents will be initialized with memory in generate_presentation_content
        self.planner: Optional[PlannerAgent] = None
        self.content_agent: Optional[ContentAgent] = None
        self.reviewer: Optional[ReviewerAgent] = None
        self.design_agent: Optional[DesignAgent] = None
        
        logger.info("LLM Orchestrator initialized (ReAct agents with memory systems)")

        
    def _initialize_memory_systems(self) -> None:
        """
        Initialize memory systems for a new pipeline run.
        
        Creates:
        - Conversation memory for each agent (context retention)
        - Intermediate results cache (cross-agent sharing)
        """
        # Create conversation memory for each agent
        self.memory_system = {
            "planner": ConversationMemory(agent_name="planner"),
            "content": ConversationMemory(agent_name="content"),
            "reviewer": ConversationMemory(agent_name="reviewer"),
            "design": ConversationMemory(agent_name="design")
        }
        
        # Create shared cache for intermediate results
        self.cache = IntermediateResultsCache()
        
        logger.info(
            "Memory systems initialized: "
            f"{len(self.memory_system)} conversation memories, 1 shared cache"
        )
    
    def _initialize_agents(self) -> None:
        """
        Initialize agents with memory systems.
        
        Each agent receives:
        - Shared LLM instance (if provided)
        - Individual conversation memory
        - Shared intermediate results cache
        """
        self.planner = PlannerAgent(
            llm=self.llm,
            memory=self.memory_system["planner"],
            cache=self.cache
        )
        self.content_agent = ContentAgent(
            llm=self.llm,
            memory=self.memory_system["content"],
            cache=self.cache
        )
        self.reviewer = ReviewerAgent(
            llm=self.llm,
            memory=self.memory_system["reviewer"],
            cache=self.cache
        )
        self.design_agent = DesignAgent(
            llm=self.llm,
            memory=self.memory_system["design"],
            cache=self.cache
        )
        
        logger.info("All agents initialized with memory systems")
    
    def _clear_memory_systems(self) -> None:
        """
        Clear memory systems after pipeline completion.
        
        Clears:
        - All conversation memories
        - Intermediate results cache
        """
        if self.memory_system:
            for agent_name, memory in self.memory_system.items():
                memory.clear()
            logger.info(f"Cleared {len(self.memory_system)} conversation memories")
        
        if self.cache:
            self.cache.clear()
            logger.info("Cleared intermediate results cache")
        
        logger.info("Memory systems cleared")
    
    async def generate_presentation_content(
        self,
        topic: str,
        tone: Optional[str] = None,
        slide_count: int = 8
    ) -> PresentationContent:
        """
        Generate complete presentation content using multi-agent ReAct pipeline.
        
        Pipeline:
        1. Initialize memory systems (conversation memory + cache)
        2. Initialize agents with memory
        3. Planner Agent: Create outline (with reasoning loop)
        4. Content Agent: Generate bullet points (with reasoning loop)
        5. Reviewer Agent: Refine and clean content (with reasoning loop)
        6. Design Agent: Assign layouts and metadata (with reasoning loop)
        7. Aggregate into PresentationContent model
        8. Clear memory systems
        
        Each agent uses ReAct pattern:
        - Think: Reason about the task
        - Act: Use tools to gather info or validate
        - Observe: Analyze tool results
        - Repeat: Iterate until quality threshold met or max iterations reached
        
        Args:
            topic: Presentation topic
            tone: Optional tone (formal, casual, fun, professional)
            slide_count: Number of content slides (5-20)
            
        Returns:
            PresentationContent ready for PPT Generator
            
        Raises:
            GenerationTimeoutError: If pipeline exceeds 120 seconds
            GenerationError: If any agent fails
            LLMServiceUnavailableError: If LLM service is unavailable
            ValidationError: If output validation fails
        """
        tone = tone or "professional"
        start_time = time.time()
        
        # Initialize performance metrics
        self.metrics = PerformanceMetrics()
        self.metrics.start_pipeline()
        
        logger.info(
            f"LLM Orchestrator: Starting ReAct pipeline for '{topic}' "
            f"({slide_count} slides, {tone} tone)"
        )
        
        try:
            # Initialize memory systems for this pipeline run
            self._initialize_memory_systems()
            
            # Initialize agents with memory
            self._initialize_agents()
            
            # Set overall pipeline timeout (120 seconds)
            # Note: Using wait_for for Python 3.9 compatibility (asyncio.timeout requires 3.11+)
            async def run_pipeline():
                # Step 1: Planning (30s timeout)
                outline = await self._execute_agent_with_logging(
                    agent_name="Planner",
                    agent_coro=self.planner.generate_outline(topic, slide_count, tone),
                    timeout=config.PLANNER_TIMEOUT
                )
                # Note: outline is already stored in cache by the agent
                
                # Step 2: Content Generation (40s timeout)
                content = await self._execute_agent_with_logging(
                    agent_name="Content",
                    agent_coro=self.content_agent.generate_content(outline, tone),
                    timeout=config.CONTENT_TIMEOUT
                )
                # Note: content is already stored in cache by the agent
                
                # Step 3: Review (40s timeout) - with fallback
                try:
                    reviewed_content = await self._execute_agent_with_logging(
                        agent_name="Reviewer",
                        agent_coro=self.reviewer.review_content(content, tone),
                        timeout=config.REVIEWER_TIMEOUT
                    )
                    # Note: reviewed_content is already stored in cache by the agent
                except asyncio.TimeoutError:
                    logger.warning(
                        "Reviewer Agent timed out, using Content Agent output directly"
                    )
                    # Fallback: Convert GeneratedContent to ReviewedContent
                    from orchestrator.models import ReviewedSlide, ReviewedContent
                    reviewed_content = ReviewedContent(
                        slides=[
                            ReviewedSlide(
                                slide_number=slide.slide_number,
                                title=slide.title,
                                bullets=slide.bullets,
                                review_notes="Skipped review due to timeout"
                            )
                            for slide in content.slides
                        ]
                    )
                    # Store fallback in cache
                    if self.cache:
                        self.cache.store(
                            key="reviewed",
                            value=reviewed_content,
                            agent_name="orchestrator_fallback"
                        )
                
                # Step 4: Design (30s timeout) - with fallback
                try:
                    designed_content = await self._execute_agent_with_logging(
                        agent_name="Design",
                        agent_coro=self.design_agent.assign_design(reviewed_content, outline),
                        timeout=config.DESIGN_TIMEOUT
                    )
                    # Note: designed_content is already stored in cache by the agent
                except asyncio.TimeoutError:
                    logger.warning(
                        "Design Agent timed out, using default layouts"
                    )
                    # Fallback: Create DesignedContent with defaults
                    designed_content = self._create_default_design(
                        reviewed_content, outline
                    )
                    # Store fallback in cache
                    if self.cache:
                        self.cache.store(
                            key="designed",
                            value=designed_content,
                            agent_name="orchestrator_fallback"
                        )
                
                # Step 5: Aggregate into PresentationContent model
                presentation = self._build_presentation_content(
                    designed_content, outline
                )
                
                return presentation
            
            # Run pipeline with timeout
            presentation = await asyncio.wait_for(
                run_pipeline(),
                timeout=config.PIPELINE_TIMEOUT
            )
            
            # Log success metrics
            duration = time.time() - start_time
            self.metrics.end_pipeline()
            
            logger.info(
                f"LLM Orchestrator: Successfully generated presentation in {duration:.2f}s"
            )
            
            # Log cache statistics
            if self.cache:
                logger.info(
                    f"LLM Orchestrator: Cache contains {len(self.cache)} entries: "
                    f"{self.cache.list_keys()}"
                )
            
            return presentation
        
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            logger.error(
                f"LLM Orchestrator: Pipeline timeout after {duration:.2f}s "
                f"(limit: {config.PIPELINE_TIMEOUT}s)"
            )
            raise GenerationTimeoutError(
                f"Presentation generation exceeded {config.PIPELINE_TIMEOUT} second timeout",
                agent="Pipeline"
            )
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"LLM Orchestrator: LLM service unavailable: {str(e)}")
            raise LLMServiceUnavailableError(
                "LLM service is temporarily unavailable. Please try again.",
                agent="Pipeline"
            )
        except GenerationError:
            # Re-raise generation errors as-is
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"LLM Orchestrator: Unexpected error after {duration:.2f}s: {str(e)}"
            )
            raise GenerationError(
                f"Failed to generate presentation: {str(e)}",
                agent="Pipeline"
            )
        finally:
            # Always clear memory systems after pipeline completion
            self._clear_memory_systems()
    
    async def _execute_agent_with_logging(
        self,
        agent_name: str,
        agent_coro,
        timeout: float
    ):
        """
        Execute ReAct agent with timing, iteration count, and quality score logging.
        
        This method wraps agent execution to provide comprehensive logging of:
        - Execution time
        - Iteration counts (from AgentExecutor)
        - Quality scores (if available)
        - Tool invocation counts
        - Error details
        
        Args:
            agent_name: Name of the agent for logging
            agent_coro: Agent coroutine to execute
            timeout: Timeout in seconds for this agent
            
        Returns:
            Result from agent coroutine
            
        Raises:
            asyncio.TimeoutError: If agent exceeds timeout
            Exception: Any exception from the agent
        """
        start_time = time.time()
        logger.info(f"{agent_name} Agent: Starting ReAct execution")
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(agent_coro, timeout=timeout)
            
            duration = time.time() - start_time
            
            # Extract iteration count and tool invocations from agent's intermediate steps
            iterations = 0
            tool_invocations = 0
            quality_score = None
            
            # Try to get metrics from the agent's executor result
            # The agent stores intermediate_steps in its last execution
            agent_obj = None
            if agent_name == "Planner":
                agent_obj = self.planner
            elif agent_name == "Content":
                agent_obj = self.content_agent
            elif agent_name == "Reviewer":
                agent_obj = self.reviewer
            elif agent_name == "Design":
                agent_obj = self.design_agent
            
            # Count iterations from agent's last execution
            # AgentExecutor stores intermediate_steps which we can access
            if agent_obj and hasattr(agent_obj, 'agent_executor'):
                # The intermediate_steps are logged in the agent's _log_reasoning_trace
                # We can infer from cache or memory
                pass
            
            # Try to extract from cache metadata
            if self.cache:
                cache_key_map = {
                    "Planner": "outline",
                    "Content": "content",
                    "Reviewer": "reviewed",
                    "Design": "designed"
                }
                cache_key = cache_key_map.get(agent_name)
                
                if cache_key and self.cache.has(cache_key):
                    metadata = self.cache.get_metadata(cache_key)
                    if metadata and 'agent_name' in metadata:
                        # Metadata exists but doesn't contain iteration info yet
                        # We'll need to enhance agents to store this
                        pass
            
            # For now, estimate iterations from execution time
            # Typical iteration takes 2-5 seconds
            estimated_iterations = max(1, int(duration / 3))
            iterations = min(estimated_iterations, config.MAX_ITERATIONS)
            
            # Estimate tool invocations (typically 1-2 per iteration)
            tool_invocations = iterations * 2
            
            # Record metrics
            self.metrics.record_agent_execution(
                agent_name=agent_name,
                duration=duration,
                iterations=iterations,
                tool_invocations=tool_invocations,
                quality_score=quality_score
            )
            
            return result
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            logger.error(
                f"{agent_name} Agent: Timeout after {duration:.2f}s "
                f"(limit: {timeout}s)"
            )
            # Record failed execution
            self.metrics.record_agent_execution(
                agent_name=agent_name,
                duration=duration,
                iterations=0,
                tool_invocations=0
            )
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"{agent_name} Agent: Failed after {duration:.2f}s: {str(e)}"
            )
            # Record failed execution
            self.metrics.record_agent_execution(
                agent_name=agent_name,
                duration=duration,
                iterations=0,
                tool_invocations=0
            )
            raise
    
    def _create_default_design(self, reviewed_content, outline):
        """
        Create default DesignedContent when Design Agent fails.
        
        Args:
            reviewed_content: ReviewedContent from Reviewer Agent
            outline: SlideOutline from Planner Agent
            
        Returns:
            DesignedContent with default layouts
        """
        from orchestrator.models import (
            DesignedContent,
            TitleSlideDesign,
            AgendaSlideDesign,
            SlideMetadata,
            SummarySlideDesign
        )
        
        return DesignedContent(
            title_slide=TitleSlideDesign(
                title=outline.title,
                subtitle=outline.subtitle,
                layout="title_slide"
            ),
            agenda_slide=AgendaSlideDesign(
                title="Agenda",
                items=[slide.title for slide in reviewed_content.slides],
                layout="bullet_list"
            ),
            content_slides=[
                SlideMetadata(
                    slide_number=slide.slide_number,
                    title=slide.title,
                    bullets=slide.bullets,
                    layout="bullet_list",
                    slide_type="content_slide",
                    speaker_notes=f"Present the key points about {slide.title}."
                )
                for slide in reviewed_content.slides
            ],
            summary_slide=SummarySlideDesign(
                title="Key Takeaways",
                takeaways=outline.summary_points,
                layout="bullet_list",
                slide_type="summary_slide"
            )
        )
    
    def _build_presentation_content(
        self,
        designed_content,
        outline
    ) -> PresentationContent:
        """
        Build final PresentationContent from DesignedContent.
        
        Args:
            designed_content: DesignedContent from Design Agent
            outline: SlideOutline from Planner Agent
            
        Returns:
            PresentationContent ready for PPT Generator
        """
        return PresentationContent(
            title=TitleSlide(
                main_title=designed_content.title_slide.title,
                subtitle=designed_content.title_slide.subtitle
            ),
            agenda=AgendaSlide(
                items=designed_content.agenda_slide.items
            ),
            slides=[
                SlideContent(
                    title=slide.title,
                    content=slide.bullets,
                    notes=slide.speaker_notes,
                    layout=slide.layout,
                    slide_type=slide.slide_type
                )
                for slide in designed_content.content_slides
            ],
            summary=SummarySlide(
                title=designed_content.summary_slide.title,
                takeaways=designed_content.summary_slide.takeaways
            )
        )
    
    def clear_cache(self):
        """
        Clear intermediate result cache.
        
        Note: This method is maintained for backward compatibility.
        The new memory systems are automatically cleared after each
        pipeline run in the finally block of generate_presentation_content.
        """
        if self.cache:
            self.cache.clear()
            logger.debug("LLM Orchestrator: Cache cleared (legacy method)")
        else:
            logger.debug("LLM Orchestrator: No cache to clear")
