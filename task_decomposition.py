from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class TaskType(Enum):
    FINANCIAL_ANALYSIS = "financial_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    PERFORMANCE_METRICS = "performance_metrics"
    GOVERNANCE_REVIEW = "governance_review"
    SUSTAINABILITY_ANALYSIS = "sustainability_analysis"
    MARKET_ANALYSIS = "market_analysis"
    STRATEGY_REVIEW = "strategy_review"
    COMPLIANCE_CHECK = "compliance_check"

@dataclass
class DecomposedTask:
    task_type: TaskType
    content: str
    priority: int
    dependencies: List[str]
    metadata: Dict[str, Any]
    target_agents: List[str]

class TaskDecomposer:
    def __init__(self):
        self.task_patterns = {
            TaskType.FINANCIAL_ANALYSIS: [
                "financial statements", "balance sheet", "income statement",
                "cash flow", "ratios", "metrics"
            ],
            TaskType.RISK_ASSESSMENT: [
                "risk factors", "uncertainties", "challenges",
                "threats", "mitigation"
            ],
            TaskType.PERFORMANCE_METRICS: [
                "KPI", "performance indicator", "benchmark",
                "growth rate", "market share"
            ],
            TaskType.GOVERNANCE_REVIEW: [
                "board", "directors", "committees",
                "governance structure", "policies"
            ],
            TaskType.SUSTAINABILITY_ANALYSIS: [
                "ESG", "sustainable", "environmental",
                "social responsibility", "carbon"
            ],
            TaskType.MARKET_ANALYSIS: [
                "market conditions", "competition", "industry trends",
                "market share", "competitive advantage"
            ],
            TaskType.STRATEGY_REVIEW: [
                "strategic initiatives", "objectives", "future plans",
                "expansion", "development"
            ],
            TaskType.COMPLIANCE_CHECK: [
                "regulatory", "compliance", "legal requirements",
                "standards", "regulations"
            ]
        }

        # Map tasks to relevant agents
        self.task_agent_mapping = {
            TaskType.FINANCIAL_ANALYSIS: ["financial_statements", "mdna"],
            TaskType.RISK_ASSESSMENT: ["mdna", "audit_report"],
            TaskType.PERFORMANCE_METRICS: ["mdna", "financial_statements"],
            TaskType.GOVERNANCE_REVIEW: ["corporate_governance"],
            TaskType.SUSTAINABILITY_ANALYSIS: ["esg", "sdg_17"],
            TaskType.MARKET_ANALYSIS: ["mdna", "letter_to_shareholders"],
            TaskType.STRATEGY_REVIEW: ["letter_to_shareholders", "mdna"],
            TaskType.COMPLIANCE_CHECK: ["audit_report", "corporate_governance"]
        }

    def decompose_content(self, content: str) -> List[DecomposedTask]:
        """
        Decompose content into specific tasks based on content analysis
        """
        decomposed_tasks = []
        
        # Analyze content and identify relevant task types
        for task_type, patterns in self.task_patterns.items():
            if any(pattern.lower() in content.lower() for pattern in patterns):
                # Create task with relevant metadata
                task = DecomposedTask(
                    task_type=task_type,
                    content=content,
                    priority=self._determine_priority(task_type, content),
                    dependencies=self._identify_dependencies(task_type),
                    metadata=self._extract_metadata(content, task_type),
                    target_agents=self.task_agent_mapping[task_type]
                )
                decomposed_tasks.append(task)

        return self._optimize_task_sequence(decomposed_tasks)

    def _determine_priority(self, task_type: TaskType, content: str) -> int:
        """
        Determine task priority based on type and content
        """
        priority_weights = {
            TaskType.FINANCIAL_ANALYSIS: 5,
            TaskType.RISK_ASSESSMENT: 4,
            TaskType.PERFORMANCE_METRICS: 4,
            TaskType.GOVERNANCE_REVIEW: 3,
            TaskType.SUSTAINABILITY_ANALYSIS: 3,
            TaskType.MARKET_ANALYSIS: 3,
            TaskType.STRATEGY_REVIEW: 4,
            TaskType.COMPLIANCE_CHECK: 3
        }
        return priority_weights.get(task_type, 2)

    def _identify_dependencies(self, task_type: TaskType) -> List[str]:
        """
        Identify dependencies for each task type
        """
        dependency_map = {
            TaskType.FINANCIAL_ANALYSIS: [],
            TaskType.RISK_ASSESSMENT: ["financial_analysis"],
            TaskType.PERFORMANCE_METRICS: ["financial_analysis"],
            TaskType.GOVERNANCE_REVIEW: [],
            TaskType.SUSTAINABILITY_ANALYSIS: [],
            TaskType.MARKET_ANALYSIS: ["financial_analysis"],
            TaskType.STRATEGY_REVIEW: ["market_analysis", "financial_analysis"],
            TaskType.COMPLIANCE_CHECK: ["governance_review"]
        }
        return dependency_map.get(task_type, [])

    def _extract_metadata(self, content: str, task_type: TaskType) -> Dict[str, Any]:
        """
        Extract relevant metadata for the task
        """
        metadata = {
            "content_length": len(content),
            "task_type": task_type.value,
            "extracted_entities": self._extract_key_entities(content),
            "timestamp": "",  # Add timestamp if needed
        }
        return metadata

    def _extract_key_entities(self, content: str) -> List[str]:
        """
        Extract key entities from content
        """
        # Implement entity extraction logic here
        # This could use NER or other extraction techniques
        return []

    def _optimize_task_sequence(self, tasks: List[DecomposedTask]) -> List[DecomposedTask]:
        """
        Optimize the sequence of tasks based on dependencies and priorities
        """
        # Sort tasks by priority and dependencies
        return sorted(tasks, key=lambda x: (-x.priority, len(x.dependencies)))
