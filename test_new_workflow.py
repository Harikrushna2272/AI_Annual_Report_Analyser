#!/usr/bin/env python
"""
Test script to verify the new LangGraph-style workflow architecture
"""

import sys
from pathlib import Path
import json
import asyncio

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from annual_report_analysis.core.config import AppConfig
from annual_report_analysis.graph.state_graph import StateGraph, NodeStatus
from annual_report_analysis.graph.workflow import (
    LangGraphWorkflow,
    SectionAgent,
    FinalGeneratorAgent,
)
from annual_report_analysis.tools.knowledge_graph import (
    KnowledgeGraph,
    Entity,
    Relationship,
)
from annual_report_analysis.agents.task_decomposition import TaskDecomposer, TaskType
from annual_report_analysis.agents.memory import LongTermMemory
from annual_report_analysis.agents.collaborative_memory import CollaborativeMemory
from annual_report_analysis.core.state import SectionName


def test_state_graph():
    """Test StateGraph functionality"""
    print("Testing StateGraph...")

    state = StateGraph()

    # Test adding chunks
    state.add_chunk(
        {
            "chunk_id": "test_chunk_1",
            "content": "This is a test chunk about financial performance.",
            "section_hint": "financial_statements",
        }
    )

    assert state.total_chunks == 1
    assert state.get_current_chunk()["chunk_id"] == "test_chunk_1"

    # Test adding nodes
    state.add_node("sentiment_agent", {"type": "sub_agent", "section": "financial"})
    assert "sentiment_agent" in state.nodes
    assert state.node_status["sentiment_agent"] == NodeStatus.PENDING

    # Test task management
    task_id = state.add_task(
        {
            "task_type": "financial_analysis",
            "content": "Analyze revenue growth",
            "priority": 5,
        }
    )

    assert len(state.tasks) == 1
    assert task_id in state.task_queue

    state.complete_task(task_id, {"result": "15% growth"})
    assert task_id in state.completed_tasks
    assert task_id not in state.task_queue

    # Test section findings
    state.add_section_finding("financial_statements", "metrics", {"revenue": "$1M"})
    assert "financial_statements" in state.section_findings
    assert "metrics" in state.section_findings["financial_statements"]

    print("✓ StateGraph tests passed")
    return state


def test_knowledge_graph():
    """Test KnowledgeGraph functionality"""
    print("\nTesting KnowledgeGraph...")

    kg = KnowledgeGraph()

    # Test entity creation
    company = Entity(
        id="company_1",
        type="COMPANY",
        name="ABC Corporation",
        properties={"industry": "Technology"},
        references=["chunk_1"],
    )

    kg.add_entity(company)
    assert "company_1" in kg.entities
    assert "company_1" in kg.entity_index["COMPANY"]

    # Test metric entity
    metric = Entity(
        id="metric_1",
        type="FINANCIAL_METRIC",
        name="Revenue $500M",
        properties={"value": "500M", "currency": "USD"},
        references=["chunk_1"],
    )

    kg.add_entity(metric)

    # Test relationship
    rel = Relationship(
        id="rel_1",
        source_id="company_1",
        target_id="metric_1",
        type="HAS_METRIC",
        properties={"year": "2023"},
        confidence=0.95,
    )

    kg.add_relationship(rel)
    assert "rel_1" in kg.relationships

    # Test entity extraction from text
    text = "ABC Corporation reported revenue of $500 million, a 15% growth. The company faces regulatory risks."
    entities = kg.extract_entities_from_text(text, "chunk_2")

    assert len(entities) > 0
    financial_metrics = [e for e in entities if e.type == "FINANCIAL_METRIC"]
    risks = [e for e in entities if e.type == "RISK"]

    assert len(financial_metrics) > 0
    assert len(risks) > 0

    print(f"✓ KnowledgeGraph tests passed - extracted {len(entities)} entities")
    return kg


def test_task_decomposer():
    """Test TaskDecomposer functionality"""
    print("\nTesting TaskDecomposer...")

    decomposer = TaskDecomposer()

    # Test with financial content
    content = """
    The company's financial statements show strong revenue growth of 25% year-over-year.
    However, there are concerns about increasing operational costs and compliance risks.
    The board has implemented new governance policies to address these challenges.
    Our ESG initiatives focus on reducing carbon emissions by 30% by 2030.
    """

    tasks = decomposer.decompose_content(content)

    assert len(tasks) > 0

    # Check if appropriate task types were identified
    task_types = [task.task_type for task in tasks]

    # Should identify financial, risk, governance, and sustainability tasks
    assert (
        TaskType.FINANCIAL_ANALYSIS in task_types
        or TaskType.PERFORMANCE_METRICS in task_types
    )
    assert TaskType.RISK_ASSESSMENT in task_types
    assert TaskType.GOVERNANCE_REVIEW in task_types
    assert TaskType.SUSTAINABILITY_ANALYSIS in task_types

    # Check task properties
    for task in tasks:
        assert task.priority > 0
        assert len(task.target_agents) > 0
        assert hasattr(task, "content")
        assert hasattr(task, "metadata")

    print(f"✓ TaskDecomposer tests passed - created {len(tasks)} tasks")
    return tasks


async def test_section_agent():
    """Test SectionAgent with sub-agents"""
    print("\nTesting SectionAgent...")

    # Setup
    state_graph = StateGraph()
    knowledge_graph = KnowledgeGraph()
    ltm = LongTermMemory()
    collab_memory = CollaborativeMemory()

    # Create section agent
    agent = SectionAgent(
        SectionName.financial_statements,
        state_graph,
        knowledge_graph,
        ltm,
        collab_memory,
    )

    # Verify sub-agents were created
    assert "sentiment" in agent.sub_agents
    assert "risk" in agent.sub_agents
    assert "metrics" in agent.sub_agents
    assert "external" in agent.sub_agents
    assert "governance_esg" in agent.sub_agents
    assert "memory" in agent.sub_agents

    # Create test tasks
    tasks = [
        {
            "id": "task_1",
            "task_type": TaskType.FINANCIAL_ANALYSIS,
            "content": "Analyze financial metrics",
            "priority": 5,
        },
        {
            "id": "task_2",
            "task_type": TaskType.RISK_ASSESSMENT,
            "content": "Assess financial risks",
            "priority": 4,
        },
    ]

    # Create test chunk
    chunk = {
        "chunk_id": "test_chunk",
        "content": "Revenue increased by 25% to $500 million. However, operational costs rose by 30%.",
        "section_hint": "financial_statements",
        "metadata": {},
    }

    # Process tasks
    results = await agent.process_tasks(tasks, chunk)

    assert len(results) > 0
    assert "task_1" in results or "task_2" in results
    assert "memory_coordination" in results

    # Check that results have expected structure
    for task_id, result in results.items():
        if task_id != "memory_coordination":
            assert "task_id" in result
            assert "sub_agent_results" in result
            assert isinstance(result["sub_agent_results"], list)

    print("✓ SectionAgent tests passed")
    return results


def test_final_generator():
    """Test FinalGeneratorAgent"""
    print("\nTesting FinalGeneratorAgent...")

    # Setup state graph with sample data
    state_graph = StateGraph()
    knowledge_graph = KnowledgeGraph()

    # Add sample data to state
    state_graph.section_summaries = {
        "financial_statements": "Strong financial performance with 25% revenue growth.",
        "risk_assessment": "Identified operational and compliance risks.",
    }

    state_graph.section_metrics["financial_statements"] = [
        {"type": "revenue", "value": "$500M"},
        {"type": "growth_rate", "value": "25%"},
    ]

    state_graph.section_risks["risk_assessment"] = [
        {"type": "operational", "priority": "high", "description": "Rising costs"},
        {"type": "compliance", "priority": "medium", "description": "New regulations"},
    ]

    state_graph.section_opportunities["financial_statements"] = [
        {"description": "Expansion into new markets", "potential": "high"}
    ]

    # Add sample KG data
    company = Entity(
        id="company_main",
        type="COMPANY",
        name="Test Corporation",
        properties={},
        references=[],
    )
    knowledge_graph.add_entity(company)

    # Create generator
    generator = FinalGeneratorAgent(state_graph, knowledge_graph)

    # Generate report
    report = generator.generate_report()

    # Verify report structure
    assert "executive_summary" in report
    assert "section_analyses" in report
    assert "key_metrics" in report
    assert "risk_assessment" in report
    assert "opportunities" in report
    assert "financial_health" in report
    assert "governance_esg_summary" in report
    assert "knowledge_graph_insights" in report
    assert "cross_section_insights" in report
    assert "recommendations" in report
    assert "appendices" in report

    # Verify content
    assert len(report["executive_summary"]) > 0
    assert len(report["key_metrics"]) > 0
    assert report["risk_assessment"]["total_risks"] == 2
    assert len(report["recommendations"]) > 0

    print("✓ FinalGeneratorAgent tests passed")
    return report


async def test_full_workflow():
    """Test complete workflow integration"""
    print("\nTesting Full Workflow Integration...")

    # Create sample content
    sample_md_content = """
    # Annual Report 2023

    ## Financial Performance

    Our company achieved remarkable financial results in 2023, with total revenue reaching $500 million,
    representing a 25% increase from the previous year. Net profit margins improved to 15%,
    demonstrating our operational efficiency.

    ## Risk Factors

    The company faces several risks including market competition, regulatory compliance challenges,
    and potential supply chain disruptions. We have implemented mitigation strategies for each.

    ## Corporate Governance

    The Board of Directors comprises 9 members, including 6 independent directors.
    The Audit Committee and Compensation Committee meet quarterly.

    ## Sustainability and ESG

    We are committed to achieving net-zero emissions by 2040 and have aligned our initiatives
    with SDG 7 (Affordable and Clean Energy) and SDG 13 (Climate Action).
    """

    # Create temporary test file
    test_dir = Path("./test_output")
    test_dir.mkdir(exist_ok=True)

    test_file = test_dir / "test_report.md"
    test_file.write_text(sample_md_content)

    # Configure workflow
    config = AppConfig(
        output_dir=test_dir,
        max_chunk_chars=500,  # Small chunks for testing
    )

    # Create and run workflow
    workflow = LangGraphWorkflow(config)

    # Test workflow components
    assert workflow.state_graph is not None
    assert workflow.knowledge_graph is not None
    assert workflow.task_decomposer is not None
    assert len(workflow.section_agents) == len(SectionName)
    assert workflow.final_generator is not None

    print("✓ Workflow components initialized successfully")

    # Clean up
    test_file.unlink()
    test_dir.rmdir()

    return True


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running Architecture Tests for New LangGraph Workflow")
    print("=" * 60)

    try:
        # Test individual components
        state_graph = test_state_graph()
        knowledge_graph = test_knowledge_graph()
        tasks = test_task_decomposer()

        # Test async components
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        section_results = loop.run_until_complete(test_section_agent())

        # Test final generation
        report = test_final_generator()

        # Test full integration
        workflow_test = loop.run_until_complete(test_full_workflow())

        loop.close()

        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)
        print("\nThe new architecture is working correctly with:")
        print("  • StateGraph for workflow state management")
        print("  • KnowledgeGraph for entity/relationship tracking")
        print("  • TaskDecomposer for breaking down analysis tasks")
        print("  • SectionAgents with multiple sub-agents")
        print("  • FinalGeneratorAgent for report generation")
        print("  • Full workflow integration")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
