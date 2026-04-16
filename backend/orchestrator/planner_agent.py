"""Planner Agent for presentation structure generation."""
import logging
import asyncio
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropicMessages as ChatAnthropic
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.schema.runnable import RunnablePassthrough

from orchestrator.models import SlideOutline
from orchestrator.config import config


logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Planner Agent - Defines presentation structure and flow.
    
    Responsibilities:
    - Create logical outline with slide titles
    - Define key points for each slide
    - Ensure coherent narrative flow
    """
    
    def __init__(self, llm=None):
        """
        Initialize Planner Agent.
        
        Args:
            llm: Optional LangChain LLM instance. If None, creates default.
        """
        self.llm = llm or self._create_llm()
        self.parser = PydanticOutputParser(pydantic_object=SlideOutline)
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
        Create prompt template for Planner Agent.
        
        Returns:
            ChatPromptTemplate for planning
        """
        template = """You are an expert presentation planner. Your task is to create a logical, 
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
    
    def _create_chain(self):
        """
        Create LangChain chain for Planner Agent.
        
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
            | self.prompt
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
        Generate presentation outline.
        
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
            f"({slide_count} slides, {tone} tone)"
        )
        
        try:
            # Run with timeout (Python 3.9 compatible)
            outline = await asyncio.wait_for(
                self._generate_with_retry(
                    topic=topic,
                    slide_count=slide_count,
                    tone=tone
                ),
                timeout=config.PLANNER_TIMEOUT
            )
                
            # Validate output
            if len(outline.outline) != slide_count:
                raise ValueError(
                    f"Expected {slide_count} slides, got {len(outline.outline)}"
                )
            
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
    
    async def _generate_with_retry(
        self,
        topic: str,
        slide_count: int,
        tone: str,
        attempt: int = 1
    ) -> SlideOutline:
        """
        Generate outline with retry logic for malformed responses.
        
        Args:
            topic: Presentation topic
            slide_count: Number of slides
            tone: Presentation tone
            attempt: Current attempt number
            
        Returns:
            SlideOutline
            
        Raises:
            Exception: If all retries fail
        """
        try:
            # Invoke chain
            outline = await self.chain.ainvoke({
                "topic": topic,
                "slide_count": slide_count,
                "tone": tone
            })
            
            return outline
            
        except (json.JSONDecodeError, ValueError) as e:
            if attempt < config.MAX_RETRIES:
                logger.warning(
                    f"Planner Agent: Attempt {attempt} failed with malformed response, retrying... "
                    f"Error: {str(e)}"
                )
                await asyncio.sleep(config.RETRY_DELAY)
                return await self._generate_with_retry(
                    topic, slide_count, tone, attempt + 1
                )
            else:
                logger.error(
                    f"Planner Agent: All {config.MAX_RETRIES} attempts failed"
                )
                raise
        except Exception as e:
            logger.error(f"Planner Agent: Unexpected error: {str(e)}")
            raise
