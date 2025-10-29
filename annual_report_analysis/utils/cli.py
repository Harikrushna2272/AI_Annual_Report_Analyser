from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from annual_report_analysis.core.config import AppConfig
from annual_report_analysis.graph.workflow import run_workflow


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Annual Report Analysis - LangGraph-powered multi-agent system"
    )

    # Input options
    parser.add_argument(
        "--input", type=str, help="Input PDF file or directory with .md/.json files"
    )
    parser.add_argument("--pdf", type=str, help="Direct path to PDF file to analyze")

    # Processing options
    parser.add_argument(
        "--max-chars",
        type=int,
        default=3000,
        help="Max characters per chunk (default: 3000)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./annual_report_analysis/output",
        help="Output directory for results",
    )

    # Runtime options
    parser.add_argument(
        "--force-agno", action="store_true", help="Force Agno runtime if available"
    )
    parser.add_argument(
        "--force-fallback",
        action="store_true",
        help="Force fallback runtime (disable LangGraph)",
    )

    # Feature toggles
    parser.add_argument(
        "--enable-web-search",
        action="store_true",
        help="Enable web search for external intelligence",
    )
    parser.add_argument(
        "--enable-finance-data",
        action="store_true",
        help="Enable financial data lookup",
    )
    parser.add_argument(
        "--enable-news", action="store_true", help="Enable news gathering"
    )

    # Debug options
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Configure based on arguments
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = AppConfig(
        output_dir=output_dir,
        max_chunk_chars=args.max_chars,
        force_agno=args.force_agno,
    )

    # Set environment variables based on flags
    if args.force_agno:
        os.environ["ANNUAL_FORCE_AGNO"] = "1"
    if args.force_fallback:
        os.environ["ANNUAL_FORCE_FALLBACK"] = "1"

    # Enable features via environment
    if args.enable_web_search:
        os.environ["ENABLE_WEB_SEARCH"] = "1"
    if args.enable_finance_data:
        os.environ["ENABLE_FINANCE_DATA"] = "1"
    if args.enable_news:
        os.environ["ENABLE_NEWS"] = "1"

    if args.verbose:
        os.environ["VERBOSE"] = "1"
    if args.debug:
        os.environ["DEBUG"] = "1"

    # Determine input document
    document_path = None

    if args.pdf:
        # Direct PDF path provided
        document_path = Path(args.pdf)
        if not document_path.exists():
            print(f"Error: PDF file not found: {document_path}")
            sys.exit(1)
        if document_path.suffix.lower() != ".pdf":
            print(f"Error: File is not a PDF: {document_path}")
            sys.exit(1)
        print(f"Processing PDF: {document_path}")

    elif args.input:
        # Check if input is a PDF file or directory
        input_path = Path(args.input)
        if input_path.is_file() and input_path.suffix.lower() == ".pdf":
            document_path = input_path
            print(f"Processing PDF: {document_path}")
        elif input_path.is_dir():
            # Look for PDF in directory
            pdf_files = list(input_path.glob("*.pdf"))
            if pdf_files:
                document_path = pdf_files[0]
                print(f"Found PDF in directory: {document_path}")
            else:
                # Use directory as output dir for pre-processed files
                config.output_dir = input_path
                print(f"Using pre-processed files from: {input_path}")
        else:
            print(f"Error: Invalid input path: {input_path}")
            sys.exit(1)

    else:
        # Use default output directory
        print(f"Using default output directory: {config.output_dir}")

        # Check for PDFs in output directory
        pdf_files = list(config.output_dir.glob("*.pdf"))
        if pdf_files:
            document_path = pdf_files[0]
            print(f"Found PDF in output directory: {document_path}")

    # Run the workflow
    try:
        print("\n" + "=" * 60)
        print("Starting Annual Report Analysis")
        print("=" * 60 + "\n")

        if args.force_fallback:
            print("Using fallback (deterministic) runtime")
            # Import and use old workflow if forced
            from annual_report_analysis.core.workflow import (
                run_workflow as run_old_workflow,
            )
            from annual_report_analysis.core.state import init_state
            from annual_report_analysis.tools.tools import load_parsed_document_chunks

            state = init_state()
            state.chunks = load_parsed_document_chunks(
                output_dir=str(config.output_dir),
                max_chunk_chars=config.max_chunk_chars,
            )
            final_state = run_old_workflow(state)

            # Format output similar to new workflow
            result = {
                "section_summaries": {
                    k.value: v for k, v in final_state.section_summaries.items()
                },
                "section_findings": {
                    k.value: v for k, v in final_state.section_findings.items()
                },
                "global_report": final_state.global_report,
            }
        else:
            print("Using LangGraph workflow with task decomposition")
            result = run_workflow(document_path, config)

        # Save results
        output_file = config.output_dir / "analysis_summary.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)

        print("\n" + "=" * 60)
        print("Analysis Complete!")
        print("=" * 60)
        print(f"\nResults saved to: {output_file}")

        # Print summary if verbose
        if args.verbose:
            print("\n--- Executive Summary ---")
            if "executive_summary" in result:
                print(result["executive_summary"])
            elif "global_report" in result:
                print(
                    result["global_report"][:500] + "..."
                    if len(result["global_report"]) > 500
                    else result["global_report"]
                )

            print("\n--- Key Metrics ---")
            if "key_metrics" in result:
                for metric in result["key_metrics"][:5]:
                    print(
                        f"  • {metric.get('type', 'Unknown')}: {metric.get('value', 'N/A')}"
                    )

            print("\n--- Risk Assessment ---")
            if "risk_assessment" in result:
                risk_summary = result["risk_assessment"].get(
                    "risk_summary", "No risks identified"
                )
                print(f"  {risk_summary}")

            print("\n--- Recommendations ---")
            if "recommendations" in result:
                for rec in result["recommendations"][:5]:
                    print(f"  • {rec}")

    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
