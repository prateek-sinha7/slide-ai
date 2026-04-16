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
from orchestrator.exceptions import (
    GenerationError,
    GenerationTimeoutError,
    LLMServiceUnavailableError,
    ValidationError
)


logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    LLM Orchestrator - Coordinates multi-agent pipeline.
    
    Pipeline: Planner → Content → Reviewer → Design
    
    Features:
    - Sequential agent execution
    - 120-second timeout protection
    - Intermediate result caching
    - Comprehensive error handling
    - Execution time and token usage logging
    """
    
    def __init__(self, llm=None):
        """
        Initialize LLM Orchestrator.
        
        Args:
            llm: Optional shared LLM instance for all agents
        """
        self.planner = PlannerAgent(llm)
        self.content_agent = ContentAgent(llm)
        self.reviewer = ReviewerAgent(llm)
        self.design_agent = DesignAgent(llm)
        
        # Cache for intermediate results (for retry scenarios)
        self.cache: Dict[str, Any] = {}
        
    async def generate_presentation_content(
        self,
        topic: str,
        tone: Optional[str] = None,
        slide_count: int = 8
    ) -> PresentationContent:
        """
        Generate complete presentation content using multi-agent pipeline.
        
        Pipeline:
        1. Planner Agent: Create outline
        2. Content Agent: Generate bullet points
        3. Reviewer Agent: Refine and clean content
        4. Design Agent: Assign layouts and metadata
        5. Aggregate into PresentationContent model
        
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
        
        logger.info(
            f"LLM Orchestrator: Starting generation pipeline for '{topic}' "
            f"({slide_count} slides, {tone} tone)"
        )
        
        try:
            # Set overall pipeline timeout (120 seconds)
            # Note: Using wait_for for Python 3.9 compatibility (asyncio.timeout requires 3.11+)
            async def run_pipeline():
                # Step 1: Planning (30s timeout)
                outline = await self._execute_with_logging(
                    "Planner",
                    self.planner.generate_outline(topic, slide_count, tone)
                )
                self.cache['outline'] = outline
                
                # Step 2: Content Generation (40s timeout)
                content = await self._execute_with_logging(
                    "Content",
                    self.content_agent.generate_content(outline, tone)
                )
                self.cache['content'] = content
                
                # Step 3: Review (40s timeout) - with fallback
                try:
                    reviewed_content = await self._execute_with_logging(
                        "Reviewer",
                        self.reviewer.review_content(content, tone)
                    )
                    self.cache['reviewed'] = reviewed_content
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
                    self.cache['reviewed'] = reviewed_content
                
                # Step 4: Design (30s timeout) - with fallback
                try:
                    designed_content = await self._execute_with_logging(
                        "Design",
                        self.design_agent.assign_design(reviewed_content, outline)
                    )
                    self.cache['designed'] = designed_content
                except asyncio.TimeoutError:
                    logger.warning(
                        "Design Agent timed out, using default layouts"
                    )
                    # Fallback: Create DesignedContent with defaults
                    designed_content = self._create_default_design(
                        reviewed_content, outline
                    )
                    self.cache['designed'] = designed_content
                
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
            logger.info(
                f"LLM Orchestrator: Successfully generated presentation in {duration:.2f}s"
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
    
    async def _execute_with_logging(self, agent_name: str, coro):
        """
        Execute agent coroutine with timing and error logging.
        
        Args:
            agent_name: Name of the agent for logging
            coro: Coroutine to execute
            
        Returns:
            Result from coroutine
            
        Raises:
            Exception: Any exception from the coroutine
        """
        start_time = time.time()
        logger.info(f"{agent_name} Agent: Starting execution")
        
        try:
            result = await coro
            duration = time.time() - start_time
            logger.info(
                f"{agent_name} Agent: Completed in {duration:.2f}s"
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"{agent_name} Agent: Failed after {duration:.2f}s: {str(e)}"
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
        """Clear intermediate result cache."""
        self.cache.clear()
        logger.debug("LLM Orchestrator: Cache cleared")
