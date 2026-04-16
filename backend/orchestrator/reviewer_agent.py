"""Reviewer Agent for refining and cleaning presentation content."""
import logging
import asyncio
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropicMessages as ChatAnthropic
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from orchestrator.models import GeneratedContent, ReviewedContent
from orchestrator.config import config


logger = logging.getLogger(__name__)


class ReviewerAgent:
    """
    Reviewer Agent - Refines content for clarity, consistency, and tone adherence.
    
    Responsibilities:
    - Remove redundancy across slides
    - Improve clarity and conciseness
    - Enforce tone consistency
    - Check for logical flow between slides
    """
    
    def __init__(self, llm=None):
        """
        Initialize Reviewer Agent.
        
        Args:
            llm: Optional LangChain LLM instance. If None, creates default.
        """
        self.llm = llm or self._create_llm()
        self.parser = PydanticOutputParser(pydantic_object=ReviewedContent)
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
        Create prompt template for Reviewer Agent.
        
        Returns:
            ChatPromptTemplate for content review
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
    
    def _create_chain(self):
        """
        Create LangChain chain for Reviewer Agent.
        
        Returns:
            Runnable chain
        """
        return (
            {
                "content": lambda x: x["content"],
                "tone": lambda x: x["tone"],
                "format_instructions": lambda x: self.parser.get_format_instructions()
            }
            | self.prompt
            | self.llm
            | self.parser
        )
    
    async def review_content(
        self,
        content: GeneratedContent,
        tone: Optional[str] = None
    ) -> ReviewedContent:
        """
        Review and refine generated content.
        
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
            f"({tone} tone)"
        )
        
        try:
            # Run with timeout (Python 3.9 compatible)
            reviewed = await asyncio.wait_for(
                self._review_with_retry(
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
    
    async def _review_with_retry(
        self,
        content: GeneratedContent,
        tone: str,
        attempt: int = 1
    ) -> ReviewedContent:
        """
        Review content with retry logic for malformed responses.
        
        Args:
            content: Generated content
            tone: Presentation tone
            attempt: Current attempt number
            
        Returns:
            ReviewedContent
            
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
                    for slide in content.slides
                ]
            }, indent=2)
            
            # Invoke chain
            reviewed = await self.chain.ainvoke({
                "content": content_str,
                "tone": tone
            })
            
            return reviewed
            
        except (json.JSONDecodeError, ValueError) as e:
            if attempt < config.MAX_RETRIES:
                logger.warning(
                    f"Reviewer Agent: Attempt {attempt} failed with malformed response, retrying... "
                    f"Error: {str(e)}"
                )
                await asyncio.sleep(config.RETRY_DELAY)
                return await self._review_with_retry(
                    content, tone, attempt + 1
                )
            else:
                logger.error(
                    f"Reviewer Agent: All {config.MAX_RETRIES} attempts failed"
                )
                raise
        except Exception as e:
            logger.error(f"Reviewer Agent: Unexpected error: {str(e)}")
            raise
