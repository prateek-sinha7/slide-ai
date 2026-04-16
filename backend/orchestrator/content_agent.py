"""Content Agent for generating detailed slide content."""
import logging
import asyncio
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropicMessages as ChatAnthropic
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from orchestrator.models import SlideOutline, GeneratedContent
from orchestrator.config import config


logger = logging.getLogger(__name__)


class ContentAgent:
    """
    Content Agent - Generates detailed bullet points for each slide.
    
    Responsibilities:
    - Generate exactly 5-6 concise bullet points per slide
    - Apply tone parameter to content generation
    - Ensure content is relevant and actionable
    """
    
    def __init__(self, llm=None):
        """
        Initialize Content Agent.
        
        Args:
            llm: Optional LangChain LLM instance. If None, creates default.
        """
        self.llm = llm or self._create_llm()
        self.parser = PydanticOutputParser(pydantic_object=GeneratedContent)
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
        Create prompt template for Content Agent.
        
        Returns:
            ChatPromptTemplate for content generation
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
    
    def _create_chain(self):
        """
        Create LangChain chain for Content Agent.
        
        Returns:
            Runnable chain
        """
        return (
            {
                "outline": lambda x: x["outline"],
                "tone": lambda x: x["tone"],
                "format_instructions": lambda x: self.parser.get_format_instructions()
            }
            | self.prompt
            | self.llm
            | self.parser
        )
    
    async def generate_content(
        self,
        outline: SlideOutline,
        tone: Optional[str] = None
    ) -> GeneratedContent:
        """
        Generate detailed content for each slide.
        
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
            f"({tone} tone)"
        )
        
        try:
            # Run with timeout (Python 3.9 compatible)
            content = await asyncio.wait_for(
                self._generate_with_retry(
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
    
    async def _generate_with_retry(
        self,
        outline: SlideOutline,
        tone: str,
        attempt: int = 1
    ) -> GeneratedContent:
        """
        Generate content with retry logic for malformed responses.
        
        Args:
            outline: Slide outline
            tone: Presentation tone
            attempt: Current attempt number
            
        Returns:
            GeneratedContent
            
        Raises:
            Exception: If all retries fail
        """
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
            
            # Invoke chain
            content = await self.chain.ainvoke({
                "outline": outline_str,
                "tone": tone
            })
            
            return content
            
        except (json.JSONDecodeError, ValueError) as e:
            if attempt < config.MAX_RETRIES:
                logger.warning(
                    f"Content Agent: Attempt {attempt} failed with malformed response, retrying... "
                    f"Error: {str(e)}"
                )
                await asyncio.sleep(config.RETRY_DELAY)
                return await self._generate_with_retry(
                    outline, tone, attempt + 1
                )
            else:
                logger.error(
                    f"Content Agent: All {config.MAX_RETRIES} attempts failed"
                )
                raise
        except Exception as e:
            logger.error(f"Content Agent: Unexpected error: {str(e)}")
            raise
