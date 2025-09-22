from __future__ import annotations

from typing import Dict  # noqa: F401

from .memory import LongTermMemory, ShortTermMemory
from .prompts import SECTION_GUIDANCE, AGNO_SYSTEM_PROMPTS
from .state import AgentMessage, DocumentChunk, SectionName, WorkflowState
from .tools import (
    analyze_sentiment_finbert_stub,
    detect_risk_fingpt_stub,
    guess_section,
    extract_good_bad_points,
)
from .transformer_tools import analyze_sentiment_finbert, detect_risk_fingpt


class BaseSectionAgent:
    def __init__(self, name: SectionName, ltm: LongTermMemory) -> None:
        self.name = name
        self.ltm = ltm
        self.stm = ShortTermMemory(capacity=20)

    def handle(self, chunk: DocumentChunk, state: WorkflowState) -> None:
        guidance = SECTION_GUIDANCE.get(self.name.value, SECTION_GUIDANCE["other"])  # type: ignore[index]
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

        # Decompose current chunk
        text = chunk.content.strip()
        decisions = extract_good_bad_points(text)
        good_points = decisions["good"]
        bad_points = decisions["bad"]
        context_header = ""
        if prior_good or prior_bad:
            context_header = "Previous decisions context:\n- GOOD: " + "; ".join(prior_good[:5]) + "\n- BAD: " + "; ".join(prior_bad[:5]) + "\n\n"
        summary_body = (text[:800] + ("..." if len(text) > 800 else ""))
        summary = f"[{self.name.value}] {guidance}\n\n{context_header}{summary_body}"

        sentiment = analyze_sentiment_finbert(chunk.content) or analyze_sentiment_finbert_stub(chunk.content)
        risks = detect_risk_fingpt(chunk.content) or detect_risk_fingpt_stub(chunk.content)

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

