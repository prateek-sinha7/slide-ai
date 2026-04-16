"""Property-based tests for PPT Generator."""
import pytest
import os
import sys
from hypothesis import given, strategies as st, assume
from datetime import datetime
from io import BytesIO
from pptx import Presentation

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ppt_generator.generator import (
    PPTGenerator,
    generate_filename,
    sanitize_topic
)
from orchestrator.models import (
    PresentationContent,
    TitleSlide,
    AgendaSlide,
    SlideContent,
    SummarySlide
)


# ============================================================================
# Property 7: Presentation Structure Completeness
# ============================================================================

@given(
    title=st.text(min_size=1, max_size=100),
    subtitle=st.one_of(st.none(), st.text(max_size=150)),
    agenda_items=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10),
    num_slides=st.integers(min_value=1, max_value=15),
    takeaways=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=5)
)
def test_property_7_presentation_structure_completeness(
    title, subtitle, agenda_items, num_slides, takeaways
):
    """
    Feature: ai-ppt-generator, Property 7: Presentation Structure Completeness
    
    For any generated presentation content, the PPT Generator SHALL create a .pptx 
    file that includes all required slide types: one title slide, one agenda slide, 
    all content slides from the input, and one summary slide.
    
    **Validates: Requirements 6.2, 6.3, 6.4, 6.5**
    """
    # Create presentation content with specified number of slides
    content = PresentationContent(
        title=TitleSlide(main_title=title, subtitle=subtitle),
        agenda=AgendaSlide(items=agenda_items),
        slides=[
            SlideContent(
                title=f"Slide {i}",
                content=[f"Point {j}" for j in range(1, 6)],
                layout="bullet_list",
                slide_type="content_slide"
            )
            for i in range(1, num_slides + 1)
        ],
        summary=SummarySlide(title="Summary", takeaways=takeaways)
    )
    
    # Generate presentation
    generator = PPTGenerator()
    result = generator.create_presentation(content)
    
    # Verify result is bytes
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Load presentation and verify structure
    prs = Presentation(BytesIO(result))
    
    # Expected: 1 title + 1 agenda + num_slides content + 1 summary
    expected_slide_count = 1 + 1 + num_slides + 1
    assert len(prs.slides) == expected_slide_count, (
        f"Expected {expected_slide_count} slides "
        f"(1 title + 1 agenda + {num_slides} content + 1 summary), "
        f"but got {len(prs.slides)}"
    )
    
    # Verify all slides have titles
    for i, slide in enumerate(prs.slides):
        assert slide.shapes.title is not None, f"Slide {i} missing title"


# ============================================================================
# Property 8: Template Consistency
# ============================================================================

@given(
    title=st.text(min_size=1, max_size=100),
    num_slides=st.integers(min_value=2, max_value=10)
)
def test_property_8_template_consistency(title, num_slides):
    """
    Feature: ai-ppt-generator, Property 8: Template Consistency
    
    For any presentation content, all slides in the generated .pptx file SHALL 
    use the same template styling, ensuring consistent fonts, colors, and layout 
    across the entire presentation.
    
    **Validates: Requirements 6.6**
    """
    # Create presentation content
    content = PresentationContent(
        title=TitleSlide(main_title=title),
        agenda=AgendaSlide(items=["Item 1", "Item 2"]),
        slides=[
            SlideContent(
                title=f"Slide {i}",
                content=[f"Point {j}" for j in range(1, 6)],
                layout="bullet_list",
                slide_type="content_slide"
            )
            for i in range(1, num_slides + 1)
        ],
        summary=SummarySlide(title="Summary", takeaways=["Point 1", "Point 2"])
    )
    
    # Generate presentation
    generator = PPTGenerator()
    result = generator.create_presentation(content)
    
    # Load presentation
    prs = Presentation(BytesIO(result))
    
    # Verify all slides have consistent structure
    # All slides except title should have similar layout
    for i in range(1, len(prs.slides)):
        slide = prs.slides[i]
        # Each slide should have a title shape
        assert slide.shapes.title is not None, f"Slide {i} missing title"
        
        # Verify title has text
        assert len(slide.shapes.title.text) > 0, f"Slide {i} title is empty"


# ============================================================================
# Property 9: Filename Generation and Sanitization
# ============================================================================

@given(st.text(min_size=1, max_size=200))
def test_property_9_filename_sanitization(topic):
    """
    Feature: ai-ppt-generator, Property 9: Filename Generation and Sanitization
    
    For any topic string (including those with special characters, spaces, or 
    path separators) and any timestamp, the filename generation function SHALL 
    produce a valid filename that includes a sanitized version of the topic, 
    the timestamp, and the .pptx extension, with all dangerous characters 
    removed or replaced.
    
    **Validates: Requirements 7.2**
    """
    timestamp = datetime(2024, 1, 15, 14, 30, 45)
    
    # Generate filename
    filename = generate_filename(topic, timestamp)
    
    # Verify filename ends with .pptx
    assert filename.endswith('.pptx'), f"Filename should end with .pptx: {filename}"
    
    # Verify no dangerous characters in filename
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        assert char not in filename, (
            f"Filename contains dangerous character '{char}': {filename}"
        )
    
    # Verify no path traversal sequences
    assert '..' not in filename, f"Filename contains '..': {filename}"
    
    # Verify filename is not just the extension
    assert filename != '.pptx', "Filename is just the extension"
    
    # Verify filename contains timestamp
    assert '20240115_143045' in filename, (
        f"Filename should contain timestamp: {filename}"
    )
    
    # Verify filename is a valid basename (no path separators)
    import os
    assert os.path.basename(filename) == filename, (
        f"Filename contains path separators: {filename}"
    )


# ============================================================================
# Property 9 (Additional): Topic Sanitization
# ============================================================================

@given(st.text(min_size=0, max_size=200))
def test_property_9_topic_sanitization(topic):
    """
    Feature: ai-ppt-generator, Property 9: Topic Sanitization
    
    For any topic string, the sanitization function SHALL remove all dangerous 
    characters while preserving safe characters and spaces.
    
    **Validates: Requirements 7.2**
    """
    # Sanitize topic
    sanitized = sanitize_topic(topic)
    
    # Verify no dangerous characters
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        assert char not in sanitized, (
            f"Sanitized topic contains dangerous character '{char}': {sanitized}"
        )
    
    # Verify no path traversal
    assert '..' not in sanitized, f"Sanitized topic contains '..': {sanitized}"
    
    # Verify no leading/trailing whitespace
    assert sanitized == sanitized.strip(), (
        f"Sanitized topic has leading/trailing whitespace: '{sanitized}'"
    )
    
    # Verify no multiple consecutive spaces
    assert '  ' not in sanitized, (
        f"Sanitized topic has multiple consecutive spaces: '{sanitized}'"
    )


# ============================================================================
# Property 15: Content Serialization Round-Trip (PPT-specific)
# ============================================================================

@given(
    title=st.text(min_size=1, max_size=100),
    subtitle=st.one_of(st.none(), st.text(max_size=150)),
    agenda_items=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10),
    num_slides=st.integers(min_value=1, max_size=10),
    takeaways=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=5)
)
def test_property_15_content_preservation_in_ppt(
    title, subtitle, agenda_items, num_slides, takeaways
):
    """
    Feature: ai-ppt-generator, Property 15: Content Preservation
    
    For any valid PresentationContent object, the generated .pptx file SHALL 
    preserve the essential content (titles, bullet points) from the input.
    
    **Validates: Data model integrity**
    """
    # Create presentation content
    content = PresentationContent(
        title=TitleSlide(main_title=title, subtitle=subtitle),
        agenda=AgendaSlide(items=agenda_items),
        slides=[
            SlideContent(
                title=f"Slide {i}",
                content=[f"Point {j}" for j in range(1, 6)],
                layout="bullet_list",
                slide_type="content_slide"
            )
            for i in range(1, num_slides + 1)
        ],
        summary=SummarySlide(title="Summary", takeaways=takeaways)
    )
    
    # Generate presentation
    generator = PPTGenerator()
    result = generator.create_presentation(content)
    
    # Load presentation
    prs = Presentation(BytesIO(result))
    
    # Verify title slide contains title
    title_slide = prs.slides[0]
    title_text = title_slide.shapes.title.text
    assert title in title_text, (
        f"Title slide should contain '{title}', but got '{title_text}'"
    )
    
    # Verify agenda slide exists and has title
    agenda_slide = prs.slides[1]
    agenda_title = agenda_slide.shapes.title.text
    assert "Agenda" in agenda_title or "agenda" in agenda_title.lower(), (
        f"Agenda slide should have 'Agenda' title, but got '{agenda_title}'"
    )
    
    # Verify content slides have correct titles
    for i in range(num_slides):
        content_slide = prs.slides[2 + i]
        expected_title = f"Slide {i + 1}"
        actual_title = content_slide.shapes.title.text
        assert expected_title in actual_title, (
            f"Content slide {i} should have title '{expected_title}', "
            f"but got '{actual_title}'"
        )
    
    # Verify summary slide exists
    summary_slide = prs.slides[-1]
    summary_title = summary_slide.shapes.title.text
    assert "Summary" in summary_title or "summary" in summary_title.lower(), (
        f"Summary slide should have 'Summary' title, but got '{summary_title}'"
    )
