"""CLI entry point for agentset-gradio-demo"""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the Gradio app"""
    app_path = Path(__file__).parent / "app.py"
    subprocess.run([sys.executable, str(app_path)])


if __name__ == "__main__":
    main()
