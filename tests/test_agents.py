"""Test cases for agent functionality."""

from annual_report_analysis.agents import (
    BaseSectionAgent,
    SupervisorAgent,
    TaskDecomposer,
    ShortTermMemory,
    LongTermMemory
)
from annual_report_analysis.core.state import DocumentChunk, SectionName, WorkflowState

def test_supervisor_routing():
    """Test supervisor's routing logic."""
    supervisor = SupervisorAgent(ltm=LongTermMemory())
    
    # Test MDnA routing
    mdna_chunk = DocumentChunk(
        chunk_id="test_1",
        section_hint=None,
        content="Management's Discussion and Analysis of Operations"
    )
    assert supervisor.route(mdna_chunk) == SectionName.mdna
    
    # Test financial statements routing
    fin_chunk = DocumentChunk(
        chunk_id="test_2",
        section_hint=None,
        content="Balance Sheet and Income Statement"
    )
    assert supervisor.route(fin_chunk) == SectionName.financial_statements

def test_task_decomposition():
    """Test task decomposition logic."""
    decomposer = TaskDecomposer()
    
    content = """
    Financial Analysis:
    Revenue grew by 15% to $100M.
    Market share increased to 25%.
    
    Risk Assessment:
    Identified potential market risks.
    """
    
    tasks = decomposer.decompose_content(content)
    assert len(tasks) >= 2
    assert any(task.task_type.value == "financial_analysis" for task in tasks)
    assert any(task.task_type.value == "risk_assessment" for task in tasks)

def test_memory_operations():
    """Test memory operations."""
    stm = ShortTermMemory()
    assert len(stm.messages) == 0
    
    # Test adding messages
    for i in range(25):  # More than capacity
        stm.add({"id": i, "content": f"Message {i}"})
    
    assert len(stm.messages) == 20  # Default capacity
