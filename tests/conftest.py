"""Test configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def sample_annual_report():
    """Create a sample annual report text for testing."""
    return """
    Letter to Shareholders
    
    Dear Shareholders,
    
    We are pleased to report another successful year...
    
    Management Discussion and Analysis
    
    Financial performance exceeded expectations with revenue growth...
    
    Financial Statements
    
    Balance Sheet
    Assets: $100M
    Liabilities: $40M
    
    Audit Report
    
    We have audited the accompanying financial statements...
    """
