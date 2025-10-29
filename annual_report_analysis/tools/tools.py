from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from ..core.state import DocumentChunk, SectionName


def load_parsed_document_chunks(
    output_dir: str | Path = "./annual_report_analysis/output",
    max_chunk_chars: int = 3000,
) -> List[DocumentChunk]:
    out_path = Path(output_dir)
    if not out_path.exists():
        return []

    md_files = list(out_path.glob("*.md"))
    txt_content = ""
    src = None
    if md_files:
        src = md_files[0]
        txt_content = src.read_text()
    else:
        json_files = list(out_path.glob("*.json"))
        if json_files:
            src = json_files[0]
            try:
                data = json.loads(src.read_text())
                txt_content = json.dumps(data)
            except Exception:
                txt_content = ""

    if not txt_content:
        return []

    chunks: List[DocumentChunk] = []
    current: List[str] = []
    current_len = 0
    chunk_index = 0
    for line in txt_content.splitlines():
        line_len = len(line) + 1
        if current_len + line_len > max_chunk_chars and current:
            chunk_text = "\n".join(current)
            chunks.append(
                DocumentChunk(
                    chunk_id=f"chunk_{chunk_index}",
                    section_hint=guess_section(chunk_text),
                    content=chunk_text,
                    meta={"source": str(src) if src else "unknown"},
                )
            )
            chunk_index += 1
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len

    if current:
        chunk_text = "\n".join(current)
        chunks.append(
            DocumentChunk(
                chunk_id=f"chunk_{chunk_index}",
                section_hint=guess_section(chunk_text),
                content=chunk_text,
                meta={"source": str(src) if src else "unknown"},
            )
        )

    return chunks


def guess_section(text: str) -> Optional[SectionName]:
    lower = text.lower()
    if "letter to shareholders" in lower or "letter from the ceo" in lower:
        return SectionName.letter_to_shareholders
    if "management's discussion" in lower or "md&a" in lower or "mdna" in lower:
        return SectionName.mdna
    if (
        "financial statements" in lower
        or "balance sheet" in lower
        or "income statement" in lower
    ):
        return SectionName.financial_statements
    if "audit report" in lower or "auditors' report" in lower:
        return SectionName.audit_report
    if "corporate governance" in lower:
        return SectionName.corporate_governance
    if "sdg 17" in lower or "partnerships for the goals" in lower:
        return SectionName.sdg_17
    if "esg" in lower or "sustainability" in lower:
        return SectionName.esg
    return None


def analyze_sentiment_finbert_stub(text: str) -> Dict[str, float]:
    return {"positive": 0.0, "neutral": 1.0, "negative": 0.0, "label": "neutral"}


def detect_risk_fingpt_stub(text: str) -> Dict[str, float]:
    return {"compliance": 0.0, "market": 0.0, "operational": 0.0}


# -------- Content decomposition helpers --------

_GOOD_KEYWORDS = [
    "growth",
    "increase",
    "improved",
    "record",
    "strong",
    "profitable",
    "resilient",
    "positive",
    "expansion",
    "innovation",
    "opportunity",
    "beat",
    "exceeded",
    "surpassed",
]

_BAD_KEYWORDS = [
    "decline",
    "decrease",
    "loss",
    "risk",
    "fraud",
    "weakness",
    "material weakness",
    "litigation",
    "probe",
    "investigation",
    "non-compliance",
    "violation",
    "breach",
    "impairment",
    "downgrade",
]


def split_sentences(text: str) -> List[str]:
    # Very simple splitter; avoids external deps
    parts = []
    buf = []
    for ch in text:
        buf.append(ch)
        if ch in ".!?\n":
            s = "".join(buf).strip()
            if s:
                parts.append(s)
            buf = []
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def extract_good_bad_points(text: str) -> Dict[str, List[str]]:
    sentences = split_sentences(text)
    goods: List[str] = []
    bads: List[str] = []
    for s in sentences:
        ls = s.lower()
        good_hit = any(k in ls for k in _GOOD_KEYWORDS)
        bad_hit = any(k in ls for k in _BAD_KEYWORDS)
        if good_hit and not bad_hit:
            goods.append(s.strip())
        elif bad_hit and not good_hit:
            bads.append(s.strip())
        elif good_hit and bad_hit:
            # If both, consider as risk-tinged achievement; classify as bad to be conservative
            bads.append(s.strip())
    return {"good": goods[:20], "bad": bads[:20]}
