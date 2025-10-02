#!/usr/bin/env python
"""
Pre-commit hook to run linting and tests before commit.
"""

import subprocess
import sys
from typing import List

def run_command(cmd: List[str]) -> bool:
    """Run a command and return True if it succeeds."""
    try:
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Run pre-commit checks."""
    print("Running pre-commit checks...")
    
    # Format code
    print("\nRunning black...")
    if not run_command(["black", "."]):
        print("Black formatting failed!")
        sys.exit(1)
    
    print("\nRunning isort...")
    if not run_command(["isort", "."]):
        print("Import sorting failed!")
        sys.exit(1)
    
    # Run type checking
    print("\nRunning mypy...")
    if not run_command(["mypy", "."]):
        print("Type checking failed!")
        sys.exit(1)
    
    # Run linting
    print("\nRunning pylint...")
    if not run_command(["pylint", "annual_report_analysis", "tests"]):
        print("Linting failed!")
        sys.exit(1)
    
    # Run tests
    print("\nRunning tests...")
    if not run_command(["pytest", "tests/"]):
        print("Tests failed!")
        sys.exit(1)
    
    print("\nAll checks passed!")
    sys.exit(0)

if __name__ == "__main__":
    main()
