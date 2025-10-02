from __future__ import annotations

from typing import Any, Callable, Dict, List

from .memory import LongTermMemory
from .prompts import AGNO_SYSTEM_PROMPTS
from .state import AgentMessage, SectionName, WorkflowState
from .tools import (
    analyze_sentiment_finbert_stub,
    detect_risk_fingpt_stub,
    guess_section,
    extract_good_bad_points,
)
from .transformer_tools import analyze_sentiment_finbert, detect_risk_fingpt


def is_agno_available() -> bool:
    try:
        from agno.agent import Agent  # type: ignore
        from agno.team import Team  # type: ignore
        _ = (Agent, Team)
        return True
    except Exception:
        return False


def _default_tools() -> Dict[str, Callable[..., Any]]:
    return {
        "analyze_sentiment": lambda text: analyze_sentiment_finbert(text)
        or analyze_sentiment_finbert_stub(text),
        "detect_risk": lambda text: detect_risk_fingpt(text)
        or detect_risk_fingpt_stub(text),
        "extract_good_bad": extract_good_bad_points,
        "guess_section": guess_section,
    }


def build_agno_team(ltm: LongTermMemory):
    # Reuse centralized agent definitions in agents.py
    try:
        from .agents import build_agno_team as _build_team  # type: ignore
        return _build_team()
    except Exception:
        return None


def run_with_agno(state: WorkflowState) -> WorkflowState:
    ltm = LongTermMemory()
    build = build_agno_team(ltm)
    if not build:
        return state
    team, supervisor, section_agents = build

    if not state.chunks:
        # Keep loader centralized in workflow to avoid new deps
        return state

    # Simple related-sections map to emulate inter-agent collaboration
    related_sections: Dict[SectionName, List[SectionName]] = {
        SectionName.mdna: [SectionName.financial_statements, SectionName.audit_report],
        SectionName.financial_statements: [SectionName.audit_report, SectionName.mdna],
        SectionName.audit_report: [SectionName.financial_statements, SectionName.corporate_governance],
        SectionName.esg: [SectionName.corporate_governance],
        SectionName.corporate_governance: [SectionName.esg],
        SectionName.letter_to_shareholders: [SectionName.mdna],
        SectionName.sdg_17: [SectionName.esg],
        SectionName.other: [],
    }

    # Message passing: supervisor routes chunks, section agents reply
    for chunk in state.chunks[state.cursor :]:
        primary = chunk.section_hint or guess_section(chunk.content) or SectionName.other
        # Decide collaboration targets
        targets = {primary}
        for sec in related_sections.get(primary, []):
            targets.add(sec)

        for section in targets:
            state.routed_chunks.setdefault(section, []).append(chunk.chunk_id)

            # Load prior context from LTM
            prior_records = ltm.query_all(agent_name=section.value, section=section)
            prior_good: List[str] = []
            prior_bad: List[str] = []
            for r in prior_records[-20:]:
                v = r.get("value", {}) if isinstance(r, dict) else {}
                good_list = v.get("good_points") or []
                bad_list = v.get("bad_points") or []
                if isinstance(good_list, list):
                    prior_good.extend([str(x) for x in good_list][:2])
                if isinstance(bad_list, list):
                    prior_bad.extend([str(x) for x in bad_list][:2])

            context_snippet = "\n".join([f"- GOOD: {g}" for g in prior_good[:3]] + [f"- BAD: {b}" for b in prior_bad[:3]])
            context_header = f"Prior context for {section.value}:\n{context_snippet}\n\n" if context_snippet else ""

            # Prepare context prompt
            prompt = (
                f"Process the following annual report chunk for section {section.value}. "
                f"Return a concise summary, sentiment, risks, good_points and bad_points as JSON fields.\n\n"
                f"{context_header}{chunk.content}"
            )

            try:
                # Send as a message to the chosen agent via team. API may vary; we emulate a call interface.
                agent = section_agents[section]
                _ = agent.run(prompt)  # type: ignore[attr-defined]
            except Exception:
                _ = None

            # Deterministic post-processing and memory write
            guidance = AGNO_SYSTEM_PROMPTS.get(section.value, AGNO_SYSTEM_PROMPTS["other"])  # type: ignore[index]
            summary_body = (chunk.content[:800] + ("..." if len(chunk.content) > 800 else ""))
            summary = f"[{section.value}] {guidance}\n\n{context_header}{summary_body}"

            sentiment = analyze_sentiment_finbert(chunk.content) or analyze_sentiment_finbert_stub(chunk.content)
            risks = detect_risk_fingpt(chunk.content) or detect_risk_fingpt_stub(chunk.content)
            decisions = extract_good_bad_points(chunk.content)

            prev_summary = state.section_summaries.get(section, "")
            combined_summary = (prev_summary + "\n\n" + summary).strip() if prev_summary else summary
            state.section_summaries[section] = combined_summary
            state.section_findings.setdefault(section, {})
            state.section_findings[section].setdefault("sentiment", []).append(sentiment)
            state.section_findings[section].setdefault("risks", []).append(risks)

            ltm.upsert(
                agent_name=section.value,
                section=section,
                key=f"{chunk.chunk_id}:{section.value}",
                value={
                    "summary": summary,
                    "sentiment": sentiment,
                    "risks": risks,
                    "good_points": decisions["good"],
                    "bad_points": decisions["bad"],
                },
            )

            state.mailbox.append(
                AgentMessage(
                    sender=section.value,
                    recipient="supervisor",
                    content=summary,
                    context={
                        "chunk_id": chunk.chunk_id,
                        "sentiment": sentiment,
                        "risks": risks,
                        "good_points": decisions["good"],
                        "bad_points": decisions["bad"],
                    },
                )
            )

        state.cursor += 1

    # Aggregate global report
    parts: List[str] = []
    for name, summary in state.section_summaries.items():
        parts.append(f"## {name.value}\n{summary}")
    state.global_report = "\n\n".join(parts)
    state.done = True
    return state


