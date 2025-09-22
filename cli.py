from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .config import AppConfig
from .workflow import run_workflow
from .state import init_state
from .tools import load_parsed_document_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Annual Report Analysis")
    parser.add_argument("--input", type=str, default="./annual_report_analysis/output", help="Input directory with .md or .json")
    parser.add_argument("--max-chars", type=int, default=3000, help="Max characters per chunk")
    parser.add_argument("--force-agno", action="store_true", help="Force Agno runtime if available")
    args = parser.parse_args()

    cfg = AppConfig(output_dir=Path(args.input), max_chunk_chars=args.max_chars, force_agno=args.force_agno)
    if cfg.force_agno:
        os.environ["ANNUAL_FORCE_AGNO"] = "1"

    state = init_state()
    state.chunks = load_parsed_document_chunks(output_dir=str(cfg.output_dir), max_chunk_chars=cfg.max_chunk_chars)
    final_state = run_workflow(state)

    out_dir = Path("./annual_report_analysis/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "analysis_summary.json").write_text(
        json.dumps(
            {
                "section_summaries": {k.value: v for k, v in final_state.section_summaries.items()},
                "section_findings": {k.value: v for k, v in final_state.section_findings.items()},
                "global_report": final_state.global_report,
            },
            indent=2,
        )
    )
    print("Analysis complete. See annual_report_analysis/output/analysis_summary.json")


if __name__ == "__main__":
    main()
