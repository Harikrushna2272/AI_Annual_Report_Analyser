"""Annual Report Analysis Package

This package provides tools and utilities for analyzing annual reports using AI agents.

Modules:
- core: Core functionality and data models
- agents: Agent implementations and coordination
- tools: Analysis and processing tools
- utils: Utility functions and CLI
"""

from annual_report_analysis.core.state import DocumentChunk, SectionName, WorkflowState
from annual_report_analysis.utils.runner import run_workflow

__version__ = "0.1.0"
__all__ = ["DocumentChunk", "SectionName", "WorkflowState", "run_workflow"]
