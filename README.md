# Annual Report Analysis

Agentic analysis of annual report files by section like Letter to Shareholders, MD&A, Financial Statements, Audit Report, Corporate Governance, SDG, ESG and etc., with the agno which is full-stack agentic framework.

## Quick start
- Put a parsed report (.md or .json) in:
  - `annual_report_analysis/output/your_report.md` (or `.json`)
- Run with Python:
```bash
python -m annual_report_analysis.runner
```
- Or use the CLI (additional options):
```bash
annual-report-analysis --input ./annual_report_analysis/output --max-chars 3000 --force-agno
```
- Output is written to:
```
annual_report_analysis/output/analysis_summary.json
```

## How it works (simple)
1) The app loads your file and splits it into chunks (~3,000 chars).
2) Each chunk is routed to a section (e.g., MD&A, ESG).
3) The section agent summarizes the chunk, detects sentiment and risks, and extracts things from the contect though proper analysis.
4) Agents store results to long‑term memory and send a message to the supervisor.
5) All section summaries are combined into a single global report.

- If Agno is installed:
  - A team of agents with distinct prompts processes the chunks.
- If not:
  - A deterministic supervisor + section agents run locally with the same outputs.

## CLI options
```bash
annual-report-analysis \
  --input ./annual_report_analysis/output \
  --max-chars 3000 \
  --force-agno
```
- `--input`: directory with your `.md` or `.json` report
- `--max-chars`: chunk size (characters)
- `--force-agno`: prefer Agno runtime when available

Environment overrides (optional):
- `ANNUAL_FORCE_AGNO=1` to prefer Agno
- `ANNUAL_FORCE_FALLBACK=1` to force deterministic path

## Installation
This project runs without external deps. To enable Agno/Transformers paths:
```bash
pip install -r requirements.txt
```
(Installs `agno-client`, `phidata`, `transformers`, `torch`.)

Editable install for development:
```bash
pip install -e .
```

## Configuration
- Input directory: files in `annual_report_analysis/output/` are picked up by default
- Chunk size: `tools.load_parsed_document_chunks(max_chunk_chars=...)`
- Prompts: `prompts.SECTION_GUIDANCE` and `prompts.AGNO_SYSTEM_PROMPTS`
- Memory: JSONL under `annual_report_analysis/memory_store/{agent}/{section}.jsonl`

## Project structure
```
annual_report_analysis/
  __init__.py
  agents.py               # Deterministic supervisor + section agents and Agno factories
  agno_support.py         # Agno runtime selection and collaborative run loop
  cli.py                  # CLI entrypoint (argparse)
  config.py               # App defaults (paths, flags)
  document_processing.py  # File-level parsing utilities (reserved/optional)
  memory.py               # Short/Long term memory implementations
  prompts.py              # Guidance and Agno system prompts
  runner.py               # Minimal entry that calls workflow
  state.py                # Dataclasses for state/messages
  tools.py                # Loader, heuristics, fallback analyzers
  transformer_tools.py    # Optional HF pipelines (FinBERT, zero-shot)
  workflow.py             # Orchestrator; prefers Agno then fallback
```

## Development
- Makefile (optional helper): `make install`, `make install-full`, `make run`, `make clean`
- CI: GitHub Action builds, runs a sample, and prints output

## FAQ
- Where do I put my file?
  - `annual_report_analysis/output/your_report.md` (or `.json`).
- How do I force the deterministic path?
  - `ANNUAL_FORCE_FALLBACK=1 python -m annual_report_analysis.runner`
- How do I enable Agno?
  - `pip install -r requirements.txt` then `--force-agno` or `ANNUAL_FORCE_AGNO=1`.
- Where are the results?
  - `annual_report_analysis/output/analysis_summary.json`.

## License
MIT
