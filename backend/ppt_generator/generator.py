"""PPT Generator module for creating PowerPoint presentations using python-pptx."""
import os
import re
import sys
from datetime import datetime
from io import BytesIO
from typing import Optional
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator.models import PresentationContent
from ppt_generator.timeout import timeout


class PPTGeneratorError(Exception):
    """Base exception for PPT Generator errors."""
    pass


class TemplateNotFoundError(PPTGeneratorError):
    """Raised when a template file is not found."""
    pass


class FileCreationError(PPTGeneratorError):
    """Raised when file creation fails."""
    pass


class PPTGenerator:
    """
    PPT Generator class for creating PowerPoint presentations.
    
    This class takes structured presentation content and generates a .pptx file
    using the python-pptx library with professional styling and templates.
    """
    
    # Professional color scheme
    TITLE_COLOR = RGBColor(31, 78, 121)  # Dark blue
    TEXT_COLOR = RGBColor(64, 64, 64)    # Dark gray
    ACCENT_COLOR = RGBColor(68, 114, 196) # Medium blue
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize PPT Generator.
        
        Args:
            template_dir: Directory containing template files (optional)
        """
        self.template_dir = template_dir or os.path.join(
            os.path.dirname(__file__), 'templates'
        )
    
    @timeout(10)
    def create_presentation(
        self,
        content: PresentationContent,
        template: str = "professional"
    ) -> bytes:
        """
        Create a .pptx file from structured content.
        
        Args:
            content: Structured presentation content
            template: Template name for styling (default: "professional")
            
        Returns:
            Binary .pptx file data
            
        Raises:
            TemplateNotFoundError: If template file is not found
            FileCreationError: If .pptx creation fails
            TimeoutError: If creation exceeds 10 seconds
        """
        try:
            # Create presentation object
            prs = self._load_template(template)
            
            # Add all slides
            self._add_title_slide(prs, content.title)
            self._add_agenda_slide(prs, content.agenda)
            
            for slide_content in content.slides:
                self._add_content_slide(prs, slide_content)
            
            self._add_summary_slide(prs, content.summary)
            
            # Save to bytes
            output = BytesIO()
            prs.save(output)
            output.seek(0)
            
            return output.getvalue()
            
        except TemplateNotFoundError:
            raise
        except Exception as e:
            raise FileCreationError(f"Failed to create presentation: {str(e)}")
    
    def _load_template(self, template: str) -> Presentation:
        """
        Load a template file or create a blank presentation.
        
        Args:
            template: Template name
            
        Returns:
            Presentation object
            
        Raises:
            TemplateNotFoundError: If template file specified but not found
        """
        template_path = os.path.join(self.template_dir, f"{template}.pptx")
        
        # If template file exists, load it
        if os.path.exists(template_path):
            try:
                return Presentation(template_path)
            except Exception as e:
                raise TemplateNotFoundError(
                    f"Failed to load template '{template}': {str(e)}"
                )
        
        # Otherwise create blank presentation with default styling
        return Presentation()
    
    def _add_title_slide(self, prs: Presentation, title_data) -> None:
        """
        Add title slide to presentation.
        
        Args:
            prs: Presentation object
            title_data: TitleSlide data with main_title and subtitle
        """
        # Use title slide layout (layout 0)
        slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(slide_layout)
        
        # Set title
        title = slide.shapes.title
        title.text = title_data.main_title
        
        # Apply title formatting
        title_frame = title.text_frame
        title_paragraph = title_frame.paragraphs[0]
        title_paragraph.font.size = Pt(44)
        title_paragraph.font.bold = True
        title_paragraph.font.color.rgb = self.TITLE_COLOR
        
        # Set subtitle if present
        if title_data.subtitle and len(slide.placeholders) > 1:
            subtitle = slide.placeholders[1]
            subtitle.text = title_data.subtitle
            
            # Apply subtitle formatting
            subtitle_frame = subtitle.text_frame
            subtitle_paragraph = subtitle_frame.paragraphs[0]
            subtitle_paragraph.font.size = Pt(24)
            subtitle_paragraph.font.color.rgb = self.TEXT_COLOR
    
    def _add_agenda_slide(self, prs: Presentation, agenda_data) -> None:
        """
        Add agenda slide to presentation.
        
        Args:
            prs: Presentation object
            agenda_data: AgendaSlide data with items list
        """
        # Use title and content layout (layout 1)
        slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)
        
        # Set title
        title = slide.shapes.title
        title.text = "Agenda"
        
        # Apply title formatting
        self._format_slide_title(title)
        
        # Add agenda items
        body = slide.placeholders[1]
        text_frame = body.text_frame
        text_frame.clear()
        
        for item in agenda_data.items:
            p = text_frame.add_paragraph()
            p.text = item
            p.level = 0
            p.font.size = Pt(20)
            p.font.color.rgb = self.TEXT_COLOR
            p.space_after = Pt(12)
    
    def _add_content_slide(self, prs: Presentation, slide_data) -> None:
        """
        Add content slide to presentation.
        
        Args:
            prs: Presentation object
            slide_data: SlideContent data with title, content, notes, layout
        """
        # Use title and content layout (layout 1)
        slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)
        
        # Set title
        title = slide.shapes.title
        title.text = slide_data.title
        
        # Apply title formatting
        self._format_slide_title(title)
        
        # Add content bullets
        body = slide.placeholders[1]
        text_frame = body.text_frame
        text_frame.clear()
        
        for bullet in slide_data.content:
            p = text_frame.add_paragraph()
            p.text = bullet
            p.level = 0
            p.font.size = Pt(18)
            p.font.color.rgb = self.TEXT_COLOR
            p.space_after = Pt(10)
        
        # Add speaker notes if present
        if slide_data.notes:
            notes_slide = slide.notes_slide
            text_frame = notes_slide.notes_text_frame
            text_frame.text = slide_data.notes
    
    def _add_summary_slide(self, prs: Presentation, summary_data) -> None:
        """
        Add summary slide to presentation.
        
        Args:
            prs: Presentation object
            summary_data: SummarySlide data with title and takeaways
        """
        # Use title and content layout (layout 1)
        slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)
        
        # Set title
        title = slide.shapes.title
        title.text = summary_data.title
        
        # Apply title formatting
        self._format_slide_title(title)
        
        # Add takeaways
        body = slide.placeholders[1]
        text_frame = body.text_frame
        text_frame.clear()
        
        for takeaway in summary_data.takeaways:
            p = text_frame.add_paragraph()
            p.text = takeaway
            p.level = 0
            p.font.size = Pt(20)
            p.font.color.rgb = self.TEXT_COLOR
            p.font.bold = True
            p.space_after = Pt(12)
    
    def _format_slide_title(self, title_shape) -> None:
        """
        Apply consistent formatting to slide titles.
        
        Args:
            title_shape: Title shape object
        """
        text_frame = title_shape.text_frame
        paragraph = text_frame.paragraphs[0]
        paragraph.font.size = Pt(32)
        paragraph.font.bold = True
        paragraph.font.color.rgb = self.TITLE_COLOR


def generate_filename(topic: str, timestamp: datetime) -> str:
    """
    Generate a safe filename from topic and timestamp.
    
    Args:
        topic: Presentation topic
        timestamp: Timestamp for filename
        
    Returns:
        Safe filename with .pptx extension
    """
    # Sanitize topic - remove dangerous characters
    # Remove path separators and special characters
    safe_topic = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', topic)
    
    # Replace spaces with underscores
    safe_topic = safe_topic.replace(' ', '_')
    
    # Remove any remaining problematic characters
    safe_topic = re.sub(r'[^\w\-_]', '', safe_topic)
    
    # Limit length to avoid filesystem issues
    safe_topic = safe_topic[:100]
    
    # Remove leading/trailing underscores or dashes
    safe_topic = safe_topic.strip('_-')
    
    # If topic is empty after sanitization, use default
    if not safe_topic:
        safe_topic = "presentation"
    
    # Format timestamp
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    
    # Combine into filename
    filename = f"{safe_topic}_{timestamp_str}.pptx"
    
    return filename


def sanitize_topic(topic: str) -> str:
    """
    Sanitize topic string to remove dangerous characters.
    
    Args:
        topic: Raw topic string
        
    Returns:
        Sanitized topic string
    """
    # Remove path separators and special characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', topic)
    
    # Remove any remaining problematic characters except spaces
    sanitized = re.sub(r'[^\w\s\-_]', '', sanitized)
    
    # Collapse multiple spaces
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    return sanitized
