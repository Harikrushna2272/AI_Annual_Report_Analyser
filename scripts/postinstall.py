#!/usr/bin/env python
"""
Download and install spaCy model after package installation.
This script should be run after pip install.
"""

import subprocess
import sys

def install_spacy_model():
    """Install the required spaCy model."""
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("Successfully installed spaCy model 'en_core_web_sm'")
    except subprocess.CalledProcessError as e:
        print(f"Error installing spaCy model: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    install_spacy_model()
