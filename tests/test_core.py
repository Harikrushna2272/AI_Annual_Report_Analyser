"""Test cases for core functionality."""

from annual_report_analysis.core.state import SectionName, DocumentChunk

def test_section_name_enum():
    """Test SectionName enum values."""
    assert SectionName.letter_to_shareholders.value == "letter_to_shareholders"
    assert SectionName.mdna.value == "mdna"
    assert SectionName.financial_statements.value == "financial_statements"
    assert SectionName.audit_report.value == "audit_report"

def test_document_chunk():
    """Test DocumentChunk creation and attributes."""
    chunk = DocumentChunk(
        chunk_id="test_1",
        section_hint=SectionName.mdna,
        content="Test content",
        meta={"source": "test"}
    )
    assert chunk.chunk_id == "test_1"
    assert chunk.section_hint == SectionName.mdna
    assert chunk.content == "Test content"
    assert chunk.meta == {"source": "test"}
