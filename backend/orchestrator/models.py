"""Data models for LLM Orchestrator agents and presentation content."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# Planner Agent Models
# ============================================================================

class SlideOutlineItem(BaseModel):
    """Single slide in the outline from Planner Agent."""
    slide_number: int = Field(..., ge=1, description="Slide number (1-indexed)")
    title: str = Field(..., min_length=1, max_length=100, description="Slide title")
    key_points: List[str] = Field(..., min_items=3, max_items=4, description="3-4 key points")


class SlideOutline(BaseModel):
    """Output from Planner Agent."""
    title: str = Field(..., min_length=1, max_length=100, description="Presentation title")
    subtitle: Optional[str] = Field(None, max_length=150, description="Optional subtitle")
    outline: List[SlideOutlineItem] = Field(..., min_items=5, max_items=20, description="Slide outline")
    summary_points: List[str] = Field(..., min_items=3, max_items=5, description="Key takeaways")


# ============================================================================
# Content Agent Models
# ============================================================================

class SlideContentItem(BaseModel):
    """Content for a single slide from Content Agent."""
    slide_number: int
    title: str
    bullets: List[str] = Field(..., min_items=3, max_items=6, description="3-6 bullet points")


class GeneratedContent(BaseModel):
    """Output from Content Agent."""
    slides: List[SlideContentItem]


# ============================================================================
# Reviewer Agent Models
# ============================================================================

class ReviewedSlide(BaseModel):
    """Reviewed slide content from Reviewer Agent."""
    slide_number: int
    title: str
    bullets: List[str] = Field(..., min_items=3, max_items=6)
    review_notes: str


class ReviewedContent(BaseModel):
    """Output from Reviewer Agent."""
    slides: List[ReviewedSlide]


# ============================================================================
# Design Agent Models
# ============================================================================

class SlideMetadata(BaseModel):
    """Design metadata for a slide from Design Agent."""
    slide_number: int
    title: str
    bullets: List[str]
    layout: str = Field(..., description="Layout type: bullet_list, two_column, title_only, image_placeholder")
    slide_type: str = Field(..., description="Slide type: content_slide, comparison_slide, conclusion_slide")
    speaker_notes: str = Field(..., min_length=10, description="Speaker notes (2-3 sentences)")


class TitleSlideDesign(BaseModel):
    """Title slide design metadata."""
    title: str
    subtitle: Optional[str]
    layout: str = "title_slide"


class AgendaSlideDesign(BaseModel):
    """Agenda slide design metadata."""
    title: str = "Agenda"
    items: List[str]
    layout: str = "bullet_list"


class SummarySlideDesign(BaseModel):
    """Summary slide design metadata."""
    title: str = "Key Takeaways"
    takeaways: List[str]
    layout: str = "bullet_list"
    slide_type: str = "summary_slide"


class DesignedContent(BaseModel):
    """Output from Design Agent."""
    title_slide: TitleSlideDesign
    agenda_slide: AgendaSlideDesign
    content_slides: List[SlideMetadata]
    summary_slide: SummarySlideDesign


# ============================================================================
# Final Presentation Content Models (for PPT Generator)
# ============================================================================

class TitleSlide(BaseModel):
    """Title slide data for presentation."""
    main_title: str
    subtitle: Optional[str] = None


class AgendaSlide(BaseModel):
    """Agenda slide data for presentation."""
    items: List[str]


class SlideContent(BaseModel):
    """Content slide data for presentation."""
    title: str
    content: List[str]  # Bullet points
    notes: Optional[str] = None  # Speaker notes
    layout: Optional[str] = "bullet_list"
    slide_type: Optional[str] = "content_slide"


class SummarySlide(BaseModel):
    """Summary slide data for presentation."""
    title: str
    takeaways: List[str]


class PresentationContent(BaseModel):
    """
    Complete presentation content model.
    
    This is the final output from the LLM Orchestrator that gets passed
    to the PPT Generator for file creation.
    """
    title: TitleSlide
    agenda: AgendaSlide
    slides: List[SlideContent]
    summary: SummarySlide
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize PresentationContent to dictionary.
        
        Returns:
            Dictionary representation of the presentation content
        """
        return {
            "title": {
                "main_title": self.title.main_title,
                "subtitle": self.title.subtitle
            },
            "agenda": {
                "items": self.agenda.items
            },
            "slides": [
                {
                    "title": slide.title,
                    "content": slide.content,
                    "notes": slide.notes,
                    "layout": slide.layout,
                    "slide_type": slide.slide_type
                }
                for slide in self.slides
            ],
            "summary": {
                "title": self.summary.title,
                "takeaways": self.summary.takeaways
            }
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PresentationContent":
        """
        Deserialize PresentationContent from dictionary.
        
        Args:
            data: Dictionary representation of presentation content
            
        Returns:
            PresentationContent instance
        """
        return PresentationContent(
            title=TitleSlide(
                main_title=data["title"]["main_title"],
                subtitle=data["title"].get("subtitle")
            ),
            agenda=AgendaSlide(
                items=data["agenda"]["items"]
            ),
            slides=[
                SlideContent(
                    title=slide["title"],
                    content=slide["content"],
                    notes=slide.get("notes"),
                    layout=slide.get("layout", "bullet_list"),
                    slide_type=slide.get("slide_type", "content_slide")
                )
                for slide in data["slides"]
            ],
            summary=SummarySlide(
                title=data["summary"]["title"],
                takeaways=data["summary"]["takeaways"]
            )
        )
