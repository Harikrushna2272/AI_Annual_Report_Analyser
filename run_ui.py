#!/usr/bin/env python
"""Script to run the Streamlit UI."""

from streamlit.web import cli as stcli
import os
import sys

if __name__ == "__main__":
    # Get the absolute path to the app.py file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "annual_report_analysis", "ui", "app.py")

    sys.argv = ["streamlit", "run", app_path]
    stcli.main()
