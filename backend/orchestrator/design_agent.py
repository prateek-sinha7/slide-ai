"""Design Agent for assigning slide types and layout metadata."""
import logging
import asyncio
import json
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropicMessages as ChatAnthropic
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from orchestrator.models import ReviewedContent, DesignedContent, SlideOutline
from orchestrator.config import config


logger = logging.getLogger(__name__)


class DesignAgent:
    """
    Design Agent - Assigns slide types and provides layout recommendations.
    
    Responsibilities:
    - Assign slide types (content_slide, comparison_slide, conclusion_slide)
    - Recommend layouts (bullet_list, two_column, title_only, image_placeholder)
    - Generate speaker notes for each slide
    - Create title, agenda, and summary slide metadata
    """
    
    def __init__(self, llm=None):
        """
        Initialize Design Agent.
        
        Args:
            llm: Optional LangChain LLM instance. If None, creates default.
        """
        self.llm = llm or self._create_llm()
        self.parser = PydanticOutputParser(pydantic_object=DesignedContent)
        self.prompt = self._create_prompt()
        self.chain = self._create_chain()
        
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
                model=config.LLM_MODEL,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                anthropic_api_key=config.ANTHROPIC_API_KEY
            )
        elif config.LLM_PROVIDER == "ollama":
            return Ollama(
                model=config.LLM_MODEL,
                temperature=config.LLM_TEMPERATURE,
                base_url=config.OLLAMA_BASE_URL
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {config.LLM_PROVIDER}")
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """
        Create prompt template for Design Agent.
        
        Returns:
            ChatPromptTemplate for design assignment
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
    
    def _create_chain(self):
        """
        Create LangChain chain for Design Agent.
        
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
            | self.prompt
            | self.llm
            | self.parser
        )
    
    async def assign_design(
        self,
        reviewed_content: ReviewedContent,
        outline: SlideOutline
    ) -> DesignedContent:
        """
        Assign design metadata to reviewed content.
        
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
            f"Design Agent: Assigning design metadata for {len(reviewed_content.slides)} slides"
        )
        
        try:
            # Run with timeout (Python 3.9 compatible)
            designed = await asyncio.wait_for(
                self._assign_with_retry(
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
    
    async def _assign_with_retry(
        self,
        reviewed_content: ReviewedContent,
        outline: SlideOutline,
        attempt: int = 1
    ) -> DesignedContent:
        """
        Assign design with retry logic for malformed responses.
        
        Args:
            reviewed_content: Reviewed content
            outline: Original outline
            attempt: Current attempt number
            
        Returns:
            DesignedContent
            
        Raises:
            Exception: If all retries fail
        """
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
            
            # Invoke chain
            designed = await self.chain.ainvoke({
                "title": outline.title,
                "subtitle": outline.subtitle or "",
                "content": content_str,
                "summary_points": json.dumps(outline.summary_points)
            })
            
            return designed
            
        except (json.JSONDecodeError, ValueError) as e:
            if attempt < config.MAX_RETRIES:
                logger.warning(
                    f"Design Agent: Attempt {attempt} failed with malformed response, retrying... "
                    f"Error: {str(e)}"
                )
                await asyncio.sleep(config.RETRY_DELAY)
                return await self._assign_with_retry(
                    reviewed_content, outline, attempt + 1
                )
            else:
                logger.error(
                    f"Design Agent: All {config.MAX_RETRIES} attempts failed"
                )
                raise
        except Exception as e:
            logger.error(f"Design Agent: Unexpected error: {str(e)}")
            raise
