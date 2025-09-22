from __future__ import annotations

import json
from pathlib import Path

from .workflow import run_workflow


def main() -> None:
    final_state = run_workflow()
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


