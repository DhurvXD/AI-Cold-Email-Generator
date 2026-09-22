"""
AI Cold Email Generator - Main Entry Point
Allows easy deployment to Streamlit Community Cloud, Hugging Face Spaces, Render, or local execution.
"""
import runpy
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

# Execute Gen_ai/main.py
target_script = root_dir / "Gen_ai" / "main.py"
runpy.run_path(str(target_script), run_name="__main__")

