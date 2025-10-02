from __future__ import annotations

from typing import Dict, List, Optional, Any  # noqa: F401

from .memory import LongTermMemory, ShortTermMemory
from .prompts import SECTION_GUIDANCE, AGNO_SYSTEM_PROMPTS
from .state import AgentMessage, DocumentChunk, SectionName, WorkflowState
from .tools import (
    analyze_sentiment_finbert_stub,
    detect_risk_fingpt_stub,
    guess_section,
    extract_good_bad_points,
)
from .transformer_tools import analyze_sentiment_finbert, detect_risk_fingpt, detect_financial_shenanigans
from .enhanced_tools import WebSearchTool, FinanceDataTool, WebCrawlerTool, NewsTool
from .task_decomposition import TaskDecomposer, DecomposedTask, TaskType


class SupervisorAgent:
    def __init__(self, ltm: LongTermMemory) -> None:
        self.ltm = ltm
        self.stm = ShortTermMemory(capacity=20)
        self.task_decomposer = TaskDecomposer()
        self.section_agents: Dict[str, BaseSectionAgent] = {}

    def process_chunk(self, chunk: DocumentChunk, state: WorkflowState) -> None:
        # First, decompose the chunk into specific tasks
        decomposed_tasks = self.task_decomposer.decompose_content(chunk.content)
        
        # Sort tasks by priority and dependencies
        sorted_tasks = self._organize_tasks(decomposed_tasks)
        
        # Process each task with appropriate agents
        for task in sorted_tasks:
            self._process_task(task, chunk, state)
            
        # Collect and synthesize results
        self._synthesize_results(chunk, state)

    def _organize_tasks(self, tasks: List[DecomposedTask]) -> List[DecomposedTask]:
        """
        Organize tasks based on dependencies and priorities
        """
        # Create dependency graph
        dependency_graph = {}
        for task in tasks:
            dependency_graph[task.task_type.value] = task.dependencies

        # Topologically sort tasks considering dependencies and priorities
        processed = set()
        result = []

        def process_task(task):
            if task.task_type.value in processed:
                return
            for dep in task.dependencies:
                dep_task = next((t for t in tasks if t.task_type.value == dep), None)
                if dep_task:
                    process_task(dep_task)
            processed.add(task.task_type.value)
            result.append(task)

        # Process all tasks
        sorted_tasks = sorted(tasks, key=lambda x: -x.priority)
        for task in sorted_tasks:
            process_task(task)

        return result

    def _process_task(self, task: DecomposedTask, chunk: DocumentChunk, state: WorkflowState) -> None:
        """
        Process a single decomposed task using appropriate agents
        """
        for agent_name in task.target_agents:
            if agent_name not in self.section_agents:
                self.section_agents[agent_name] = BaseSectionAgent(
                    SectionName(agent_name), self.ltm
                )
            
            agent = self.section_agents[agent_name]
            # Create a task-specific chunk with relevant metadata
            task_chunk = DocumentChunk(
                content=chunk.content,
                metadata={
                    **chunk.metadata,
                    "task_type": task.task_type.value,
                    "task_priority": task.priority,
                    "task_metadata": task.metadata
                }
            )
            agent.handle(task_chunk, state)

    def _synthesize_results(self, chunk: DocumentChunk, state: WorkflowState) -> None:
        """
        Synthesize results from all agents that processed the chunk
        """
        synthesis = {
            "section_analyses": {},
            "cross_section_insights": [],
            "key_findings": [],
            "recommendations": []
        }
        
        # Collect results from each agent
        for agent_name, agent in self.section_agents.items():
            if agent_results := agent.get_latest_results():
                synthesis["section_analyses"][agent_name] = agent_results

        # Add synthesis to state
        state.add_synthesis(chunk.id, synthesis)


class BaseSectionAgent:
    def __init__(self, name: SectionName, ltm: LongTermMemory, collaborative_memory=None) -> None:
        self.name = name
        self.ltm = ltm
        self.stm = ShortTermMemory(capacity=20)
        self.latest_results = None
        self.collaborative_memory = collaborative_memory
        
        # Initialize enhanced tools
        self.web_search = WebSearchTool()
        self.finance_data = FinanceDataTool()
        self.web_crawler = WebCrawlerTool()
        self.news_tool = NewsTool()
        
        # Define related sections for collaboration
        self.related_sections = {
            'letter_to_shareholders': ['mdna', 'financial_statements'],
            'mdna': ['financial_statements', 'letter_to_shareholders', 'risk_assessment'],
            'financial_statements': ['mdna', 'audit_report'],
            'audit_report': ['financial_statements', 'corporate_governance'],
            'corporate_governance': ['esg', 'audit_report'],
            'sdg_17': ['esg'],
            'esg': ['corporate_governance', 'sdg_17'],
            'other': ['letter_to_shareholders', 'mdna', 'financial_statements']
        }
        
        # Set up collaborations if collaborative memory is provided
        if self.collaborative_memory:
            # Subscribe to related sections
            for related_section in self.related_sections.get(self.name.value, []):
                self.collaborative_memory.subscribe_to_agent(self.name.value, related_section)
                # Add cross-references
                self.collaborative_memory.add_cross_reference(self.name.value, related_section)
                
    def _analyze_with_collaboration(self, text: str, collaborative_insights: Dict[str, List[Any]]) -> Dict[str, List[str]]:
        """Analyze text with awareness of related sections' insights"""
        # Get base analysis
        base_analysis = extract_good_bad_points(text)
        
        # Enhance analysis with collaborative insights
        for section, insights in collaborative_insights.items():
            if section != self.name.value:  # Don't process own insights
                for insight in insights:
                    # Add relevant good points from related sections
                    if 'good_points' in insight:
                        base_analysis['good'].extend([
                            f"[{section}] {point}" 
                            for point in insight['good_points']
                            if self._is_relevant_to_current_section(point)
                        ])
                    
                    # Add relevant bad points from related sections
                    if 'bad_points' in insight:
                        base_analysis['bad'].extend([
                            f"[{section}] {point}" 
                            for point in insight['bad_points']
                            if self._is_relevant_to_current_section(point)
                        ])
        
        # Deduplicate points while preserving section tags
        base_analysis['good'] = list(set(base_analysis['good']))
        base_analysis['bad'] = list(set(base_analysis['bad']))
        
        return base_analysis
    
    def _is_relevant_to_current_section(self, point: str) -> bool:
        """Determine if an insight from another section is relevant to current section"""
        # This could be enhanced with more sophisticated relevance checking
        section_keywords = {
            'letter_to_shareholders': ['strategy', 'vision', 'outlook', 'leadership'],
            'mdna': ['performance', 'operations', 'results', 'trends'],
            'financial_statements': ['revenue', 'profit', 'assets', 'liabilities'],
            'audit_report': ['opinion', 'compliance', 'controls', 'procedures'],
            'corporate_governance': ['board', 'committee', 'policies', 'oversight'],
            'sdg_17': ['sustainability', 'partnership', 'development', 'goals'],
            'esg': ['environmental', 'social', 'governance', 'sustainability'],
        }
        
        # Check if point contains keywords relevant to current section
        current_keywords = section_keywords.get(self.name.value, [])
        return any(keyword.lower() in point.lower() for keyword in current_keywords)

    def handle(self, chunk: DocumentChunk, state: WorkflowState) -> None:
        guidance = SECTION_GUIDANCE.get(self.name.value, SECTION_GUIDANCE["other"])
        # Load prior decisions from LTM as context
        prior_records = self.ltm.query_all(agent_name=self.name.value, section=self.name)
        prior_good: list[str] = []
        prior_bad: list[str] = []
        for r in prior_records[-20:]:
            v = r.get("value", {}) if isinstance(r, dict) else {}
            good_list = v.get("good_points") or []
            bad_list = v.get("bad_points") or []
            if isinstance(good_list, list):
                prior_good.extend([str(x) for x in good_list][:3])
            if isinstance(bad_list, list):
                prior_bad.extend([str(x) for x in bad_list][:3])

        # Process current chunk with task-specific context
        text = chunk.content.strip()
        task_type = chunk.metadata.get("task_type", "general_analysis")
        task_priority = chunk.metadata.get("task_priority", 3)
        task_metadata = chunk.metadata.get("task_metadata", {})
        
        decisions = extract_good_bad_points(text)
        good_points = decisions["good"]
        bad_points = decisions["bad"]
        
        context_header = ""
        if prior_good or prior_bad:
            context_header = f"Previous decisions context ({task_type}):\n- GOOD: " + "; ".join(prior_good[:5]) + "\n- BAD: " + "; ".join(prior_bad[:5]) + "\n\n"
        
        summary_body = (text[:800] + ("..." if len(text) > 800 else ""))
        summary = f"[{self.name.value}] {guidance} - Task: {task_type}\n\n{context_header}{summary_body}"

        # Include task-specific analysis with financial shenanigans detection
        sentiment = analyze_sentiment_finbert(chunk.content) or analyze_sentiment_finbert_stub(chunk.content)
        shenanigans_patterns = detect_financial_shenanigans(chunk.content) or {}
        risks = detect_risk_fingpt(chunk.content) or detect_risk_fingpt_stub(chunk.content)
        
        # Enhance risk detection with shenanigans patterns
        if shenanigans_patterns:
            high_risk_patterns = [
                pattern for pattern, score in shenanigans_patterns.items()
                if score > 0.7  # High confidence threshold
            ]
            if high_risk_patterns:
                if isinstance(risks, list):
                    risks.extend([f"Potential financial shenanigan detected: {pattern}" for pattern in high_risk_patterns])
                else:
                    risks = [f"Potential financial shenanigan detected: {pattern}" for pattern in high_risk_patterns]
        
        # Store results
        self.latest_results = {
            "task_type": task_type,
            "priority": task_priority,
            "good_points": good_points,
            "bad_points": bad_points,
            "sentiment": sentiment,
            "risks": risks,
            "task_metadata": task_metadata,
            "summary": summary
        }

        prev_summary = state.section_summaries.get(self.name, "")
        combined_summary = (prev_summary + "\n\n" + summary).strip() if prev_summary else summary
        state.section_summaries[self.name] = combined_summary
        state.section_findings.setdefault(self.name, {})
        state.section_findings[self.name].setdefault("sentiment", []).append(sentiment)
        state.section_findings[self.name].setdefault("risks", []).append(risks)

        self.ltm.upsert(
            agent_name=self.name.value,
            section=self.name,
            key=chunk.chunk_id,
            value={
                "summary": summary,
                "sentiment": sentiment,
                "risks": risks,
                "good_points": good_points,
                "bad_points": bad_points,
            },
        )

        self.stm.add(AgentMessage(sender=self.name.value, recipient=self.name.value, content=summary))


class SupervisorAgent:
    def __init__(self, ltm: LongTermMemory) -> None:
        self.ltm = ltm
        self.stm = ShortTermMemory(capacity=50)

    def route(self, chunk: DocumentChunk) -> SectionName:
        if chunk.section_hint:
            return chunk.section_hint
        guess = guess_section(chunk.content)
        return guess or SectionName.other

    def aggregate_global(self, state: WorkflowState) -> None:
        parts = []
        for name, summary in state.section_summaries.items():
            parts.append(f"## {name.value}\n{summary}")
        state.global_report = "\n\n".join(parts)


# Specialized agents (extending BaseSectionAgent). These can add custom tool logic later.
class LetterToShareholdersAgent(BaseSectionAgent):
    pass


class MDNAAgent(BaseSectionAgent):
    pass


class FinancialStatementsAgent(BaseSectionAgent):
    pass


class AuditReportAgent(BaseSectionAgent):
    pass


class CorporateGovernanceAgent(BaseSectionAgent):
    pass


class SDG17Agent(BaseSectionAgent):
    pass


class ESGAgent(BaseSectionAgent):
    pass



# -------- Agno (formerly Phidata) agent factories --------
try:
    from agno.agent import Agent as AgnoAgent  # type: ignore
    from agno.team import Team as AgnoTeam  # type: ignore
    _AGNO_AVAILABLE = True
except Exception:
    AgnoAgent = object  # type: ignore
    AgnoTeam = object  # type: ignore
    _AGNO_AVAILABLE = False

def agno_is_available() -> bool:
    return _AGNO_AVAILABLE


def build_agno_agents():
    if not _AGNO_AVAILABLE:
        return None
    tools = {
        "analyze_sentiment": lambda text: analyze_sentiment_finbert(text)
        or analyze_sentiment_finbert_stub(text),
        "detect_risk": lambda text: detect_risk_fingpt(text)
        or detect_risk_fingpt_stub(text),
        "extract_good_bad": extract_good_bad_points,
        "guess_section": guess_section,
    }
    # Create Agno agents per section
    section_agents = {}
    for section in SectionName:
        prompt = AGNO_SYSTEM_PROMPTS.get(section.value, AGNO_SYSTEM_PROMPTS["other"])  # type: ignore[index]
        section_agents[section] = AgnoAgent(
            name=section.value,
            instructions=prompt,
            tools=tools,
        )
    supervisor = AgnoAgent(
        name="supervisor",
        instructions=AGNO_SYSTEM_PROMPTS.get("supervisor", "Supervisor"),
        tools=tools,
    )
    return supervisor, section_agents


def build_agno_team():
    if not _AGNO_AVAILABLE:
        return None
    made = build_agno_agents()
    if not made:
        return None
    supervisor, section_agents = made
    team = AgnoTeam(agents=[supervisor] + [section_agents[s] for s in SectionName])
    return team, supervisor, section_agents

