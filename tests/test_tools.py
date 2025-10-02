"""Test cases for document processing tools."""

from pathlib import Path
from annual_report_analysis.tools import (
    load_parsed_document_chunks,
    guess_section,
    extract_good_bad_points
)

def test_guess_section():
    """Test section guessing from content."""
    mdna_text = "Management's Discussion and Analysis of Financial Results"
    assert guess_section(mdna_text).value == "mdna"
    
    letter_text = "Letter to Shareholders: Annual Review"
    assert guess_section(letter_text).value == "letter_to_shareholders"

def test_extract_good_bad_points():
    """Test extraction of positive and negative points."""
    text = """
    Revenue growth exceeded expectations.
    Market share declined in Q3.
    Strong cash position maintained.
    """
    points = extract_good_bad_points(text)
    
    assert len(points["good"]) == 2
    assert len(points["bad"]) == 1
    assert any("growth" in point for point in points["good"])
    assert any("declined" in point for point in points["bad"])

def test_load_parsed_document_chunks(temp_dir):
    """Test loading document chunks from files."""
    # Create a test file
    test_file = temp_dir / "test_report.md"
    test_file.write_text("""
    Letter to Shareholders
    
    Dear Shareholders,
    We are pleased to report strong growth...
    """)
    
    chunks = load_parsed_document_chunks(output_dir=str(temp_dir))
    assert len(chunks) > 0
    assert chunks[0].section_hint.value == "letter_to_shareholders"
