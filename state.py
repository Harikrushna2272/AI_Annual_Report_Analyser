from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SectionName(str, Enum):
    letter_to_shareholders = "letter_to_shareholders"
    mdna = "mdna"
    financial_statements = "financial_statements"
    audit_report = "audit_report"
    corporate_governance = "corporate_governance"
    sdg_17 = "sdg_17"
    esg = "esg"
    other = "other"


@dataclass
class DocumentChunk:
    chunk_id: str
    section_hint: Optional[SectionName]
    content: str
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMessage:
    sender: str
    recipient: str
    content: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowState:
    chunks: List[DocumentChunk] = field(default_factory=list)
    routed_chunks: Dict[SectionName, List[str]] = field(default_factory=lambda: {s: [] for s in SectionName})
    mailbox: List[AgentMessage] = field(default_factory=list)
    section_summaries: Dict[SectionName, str] = field(default_factory=dict)
    section_findings: Dict[SectionName, Dict[str, Any]] = field(default_factory=dict)
    global_report: Optional[str] = None
    cursor: int = 0
    done: bool = False


def init_state() -> WorkflowState:
    return WorkflowState()


