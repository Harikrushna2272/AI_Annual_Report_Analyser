from __future__ import annotations

import os
from typing import Dict

from .agents import (
    AuditReportAgent,
    BaseSectionAgent,
    CorporateGovernanceAgent,
    ESGAgent,
    FinancialStatementsAgent,
    LetterToShareholdersAgent,
    MDNAAgent,
    SDG17Agent,
    SupervisorAgent,
)
from .memory import LongTermMemory
from .state import SectionName, WorkflowState, init_state
from .tools import load_parsed_document_chunks
from .agno_support import is_agno_available, run_with_agno


def build_workflow():
    ltm = LongTermMemory()
    supervisor = SupervisorAgent(ltm=ltm)
    section_agents: Dict[SectionName, BaseSectionAgent] = {
        SectionName.letter_to_shareholders: LetterToShareholdersAgent(SectionName.letter_to_shareholders, ltm),
        SectionName.mdna: MDNAAgent(SectionName.mdna, ltm),
        SectionName.financial_statements: FinancialStatementsAgent(SectionName.financial_statements, ltm),
        SectionName.audit_report: AuditReportAgent(SectionName.audit_report, ltm),
        SectionName.corporate_governance: CorporateGovernanceAgent(SectionName.corporate_governance, ltm),
        SectionName.sdg_17: SDG17Agent(SectionName.sdg_17, ltm),
        SectionName.esg: ESGAgent(SectionName.esg, ltm),
        SectionName.other: BaseSectionAgent(SectionName.other, ltm),
    }

    def run(state: WorkflowState) -> WorkflowState:
        if not state.chunks:
            state.chunks = load_parsed_document_chunks()
        # Runtime selection with override via env vars
        force_fallback = os.environ.get("ANNUAL_FORCE_FALLBACK") == "1"
        force_agno = os.environ.get("ANNUAL_FORCE_AGNO") == "1"
        if not force_fallback and (force_agno or is_agno_available()):
            return run_with_agno(state)
        # Fallback to built-in deterministic agents
        while state.cursor < len(state.chunks):
            chunk = state.chunks[state.cursor]
            section = supervisor.route(chunk)
            state.routed_chunks.setdefault(section, []).append(chunk.chunk_id)
            section_agents[section].handle(chunk, state)
            state.cursor += 1
        supervisor.aggregate_global(state)
        state.done = True
        return state

    return run


def run_workflow() -> WorkflowState:
    app = build_workflow()
    state = init_state()
    return app(state)


