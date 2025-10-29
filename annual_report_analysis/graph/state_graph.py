"""
LangGraph-style State Graph for Annual Report Analysis
Manages workflow state and orchestrates agent execution
"""

from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
from pathlib import Path
import uuid


class NodeStatus(Enum):
    """Status of a node in the graph"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class MessageType(Enum):
    """Types of messages in the state graph"""

    TASK = "task"
    RESULT = "result"
    ERROR = "error"
    INFO = "info"
    QUERY = "query"
    INSIGHT = "insight"


@dataclass
class GraphMessage:
    """Message passed between nodes in the graph"""

    id: str
    type: MessageType
    sender: str
    recipient: str
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class NodeResult:
    """Result from a node execution"""

    node_id: str
    status: NodeStatus
    output: Any
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "output": self.output,
            "errors": self.errors,
            "metadata": self.metadata,
            "execution_time": self.execution_time,
        }


@dataclass
class StateGraph:
    """
    Main state graph managing the workflow
    Acts as a blackboard/shared state for all agents
    """

    # Core state
    graph_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    # Document state
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    current_chunk_index: int = 0
    total_chunks: int = 0

    # Agent/Node state
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    node_status: Dict[str, NodeStatus] = field(default_factory=dict)
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    node_dependencies: Dict[str, Set[str]] = field(default_factory=dict)

    # Decomposed tasks
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    task_queue: List[str] = field(default_factory=list)
    completed_tasks: Set[str] = field(default_factory=set)

    # Section analysis results
    section_summaries: Dict[str, str] = field(default_factory=dict)
    section_findings: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    section_metrics: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    section_risks: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    section_opportunities: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    # Cross-section insights
    cross_references: Dict[str, List[str]] = field(default_factory=dict)
    collaborative_insights: List[Dict[str, Any]] = field(default_factory=list)

    # Knowledge graph references
    kg_entities: Dict[str, List[str]] = field(
        default_factory=dict
    )  # chunk_id -> entity_ids
    kg_relationships: Dict[str, List[str]] = field(
        default_factory=dict
    )  # chunk_id -> relationship_ids
    kg_summary: Dict[str, Any] = field(default_factory=dict)

    # Messages and communication
    message_queue: List[GraphMessage] = field(default_factory=list)
    message_history: List[GraphMessage] = field(default_factory=list)

    # Global outputs
    global_report: Optional[str] = None
    executive_summary: Optional[str] = None
    key_highlights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_chunk(self, chunk: Dict[str, Any]) -> None:
        """Add a document chunk to the state"""
        chunk["index"] = len(self.chunks)
        chunk["processed"] = False
        self.chunks.append(chunk)
        self.total_chunks = len(self.chunks)

    def get_current_chunk(self) -> Optional[Dict[str, Any]]:
        """Get the current chunk being processed"""
        if 0 <= self.current_chunk_index < len(self.chunks):
            return self.chunks[self.current_chunk_index]
        return None

    def mark_chunk_processed(self, chunk_index: int) -> None:
        """Mark a chunk as processed"""
        if 0 <= chunk_index < len(self.chunks):
            self.chunks[chunk_index]["processed"] = True

    def add_node(self, node_id: str, node_config: Dict[str, Any]) -> None:
        """Register a node in the graph"""
        self.nodes[node_id] = node_config
        self.node_status[node_id] = NodeStatus.PENDING
        if "dependencies" in node_config:
            self.node_dependencies[node_id] = set(node_config["dependencies"])

    def update_node_status(self, node_id: str, status: NodeStatus) -> None:
        """Update the status of a node"""
        self.node_status[node_id] = status

    def add_node_result(self, result: NodeResult) -> None:
        """Add a result from node execution"""
        self.node_results[result.node_id] = result
        self.update_node_status(result.node_id, result.status)

    def can_execute_node(self, node_id: str) -> bool:
        """Check if a node can be executed based on dependencies"""
        if node_id not in self.node_dependencies:
            return True

        for dep in self.node_dependencies[node_id]:
            if (
                dep not in self.node_results
                or self.node_results[dep].status != NodeStatus.COMPLETED
            ):
                return False
        return True

    def add_task(self, task: Dict[str, Any]) -> str:
        """Add a decomposed task to the state"""
        task_id = task.get("id", str(uuid.uuid4()))
        task["id"] = task_id
        task["status"] = "pending"
        self.tasks.append(task)
        self.task_queue.append(task_id)
        return task_id

    def complete_task(self, task_id: str, result: Any) -> None:
        """Mark a task as completed"""
        self.completed_tasks.add(task_id)
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)

        # Update task with result
        for task in self.tasks:
            if task["id"] == task_id:
                task["status"] = "completed"
                task["result"] = result
                break

    def add_section_summary(self, section: str, summary: str) -> None:
        """Add or update a section summary"""
        if section in self.section_summaries:
            # Append to existing summary
            self.section_summaries[section] += "\n\n" + summary
        else:
            self.section_summaries[section] = summary

    def add_section_finding(
        self, section: str, finding_type: str, finding: Any
    ) -> None:
        """Add a finding to a section"""
        if section not in self.section_findings:
            self.section_findings[section] = {}

        if finding_type not in self.section_findings[section]:
            self.section_findings[section][finding_type] = []

        self.section_findings[section][finding_type].append(finding)

    def add_metric(self, section: str, metric: Dict[str, Any]) -> None:
        """Add a metric to a section"""
        if section not in self.section_metrics:
            self.section_metrics[section] = []
        self.section_metrics[section].append(metric)

    def add_risk(self, section: str, risk: Dict[str, Any]) -> None:
        """Add a risk to a section"""
        if section not in self.section_risks:
            self.section_risks[section] = []
        self.section_risks[section].append(risk)

    def add_opportunity(self, section: str, opportunity: Dict[str, Any]) -> None:
        """Add an opportunity to a section"""
        if section not in self.section_opportunities:
            self.section_opportunities[section] = []
        self.section_opportunities[section].append(opportunity)

    def add_cross_reference(self, source_section: str, target_section: str) -> None:
        """Add a cross-reference between sections"""
        if source_section not in self.cross_references:
            self.cross_references[source_section] = []
        if target_section not in self.cross_references[source_section]:
            self.cross_references[source_section].append(target_section)

    def add_collaborative_insight(self, insight: Dict[str, Any]) -> None:
        """Add a collaborative insight from multiple sections"""
        insight["timestamp"] = datetime.now().isoformat()
        self.collaborative_insights.append(insight)

    def add_kg_entities(self, chunk_id: str, entity_ids: List[str]) -> None:
        """Track knowledge graph entities for a chunk"""
        self.kg_entities[chunk_id] = entity_ids

    def add_kg_relationships(self, chunk_id: str, relationship_ids: List[str]) -> None:
        """Track knowledge graph relationships for a chunk"""
        self.kg_relationships[chunk_id] = relationship_ids

    def update_kg_summary(self, summary: Dict[str, Any]) -> None:
        """Update knowledge graph summary statistics"""
        self.kg_summary = summary

    def send_message(self, message: GraphMessage) -> None:
        """Send a message through the graph"""
        self.message_queue.append(message)
        self.message_history.append(message)

    def receive_messages(self, recipient: str) -> List[GraphMessage]:
        """Receive messages for a specific recipient"""
        messages = [m for m in self.message_queue if m.recipient == recipient]
        # Remove from queue
        self.message_queue = [m for m in self.message_queue if m.recipient != recipient]
        return messages

    def broadcast_message(
        self, sender: str, content: Any, message_type: MessageType = MessageType.INFO
    ) -> None:
        """Broadcast a message to all nodes"""
        message = GraphMessage(
            id=str(uuid.uuid4()),
            type=message_type,
            sender=sender,
            recipient="*",  # Broadcast
            content=content,
        )
        self.message_history.append(message)

        # Add to all node queues
        for node_id in self.nodes:
            if node_id != sender:
                self.message_queue.append(
                    GraphMessage(
                        id=message.id,
                        type=message.type,
                        sender=sender,
                        recipient=node_id,
                        content=content,
                    )
                )

    def get_next_pending_node(self) -> Optional[str]:
        """Get the next node that can be executed"""
        for node_id, status in self.node_status.items():
            if status == NodeStatus.PENDING and self.can_execute_node(node_id):
                return node_id
        return None

    def is_complete(self) -> bool:
        """Check if all nodes have been processed"""
        return all(
            status in [NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.SKIPPED]
            for status in self.node_status.values()
        )

    def get_failed_nodes(self) -> List[str]:
        """Get list of failed nodes"""
        return [
            node_id
            for node_id, status in self.node_status.items()
            if status == NodeStatus.FAILED
        ]

    def add_error(self, error: str) -> None:
        """Add an error to the state"""
        self.errors.append(f"[{datetime.now().isoformat()}] {error}")

    def add_warning(self, warning: str) -> None:
        """Add a warning to the state"""
        self.warnings.append(f"[{datetime.now().isoformat()}] {warning}")

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state"""
        return {
            "graph_id": self.graph_id,
            "created_at": self.created_at.isoformat(),
            "chunks_processed": sum(
                1 for c in self.chunks if c.get("processed", False)
            ),
            "total_chunks": self.total_chunks,
            "nodes_completed": sum(
                1 for s in self.node_status.values() if s == NodeStatus.COMPLETED
            ),
            "total_nodes": len(self.nodes),
            "tasks_completed": len(self.completed_tasks),
            "total_tasks": len(self.tasks),
            "sections_analyzed": list(self.section_summaries.keys()),
            "kg_entities_count": sum(len(e) for e in self.kg_entities.values()),
            "kg_relationships_count": sum(
                len(r) for r in self.kg_relationships.values()
            ),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
        }

    def save_checkpoint(self, path: Path) -> None:
        """Save state checkpoint to disk"""
        checkpoint_data = {
            "graph_id": self.graph_id,
            "created_at": self.created_at.isoformat(),
            "chunks": self.chunks,
            "current_chunk_index": self.current_chunk_index,
            "section_summaries": self.section_summaries,
            "section_findings": self.section_findings,
            "section_metrics": self.section_metrics,
            "section_risks": self.section_risks,
            "section_opportunities": self.section_opportunities,
            "collaborative_insights": self.collaborative_insights,
            "kg_summary": self.kg_summary,
            "global_report": self.global_report,
            "executive_summary": self.executive_summary,
            "key_highlights": self.key_highlights,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
        }

        with open(path, "w") as f:
            json.dump(checkpoint_data, f, indent=2, default=str)

    def load_checkpoint(self, path: Path) -> None:
        """Load state checkpoint from disk"""
        with open(path, "r") as f:
            data = json.load(f)

        self.graph_id = data.get("graph_id", self.graph_id)
        self.chunks = data.get("chunks", [])
        self.current_chunk_index = data.get("current_chunk_index", 0)
        self.section_summaries = data.get("section_summaries", {})
        self.section_findings = data.get("section_findings", {})
        self.section_metrics = data.get("section_metrics", {})
        self.section_risks = data.get("section_risks", {})
        self.section_opportunities = data.get("section_opportunities", {})
        self.collaborative_insights = data.get("collaborative_insights", [])
        self.kg_summary = data.get("kg_summary", {})
        self.global_report = data.get("global_report")
        self.executive_summary = data.get("executive_summary")
        self.key_highlights = data.get("key_highlights", [])
        self.recommendations = data.get("recommendations", [])
        self.metadata = data.get("metadata", {})

        self.total_chunks = len(self.chunks)
