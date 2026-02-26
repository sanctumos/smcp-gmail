#!/usr/bin/env python3
"""Run test suite with coverage. Usage: python run_tests.py [pytest args...]"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=cli",
        "--cov=gmail_client",
        "--cov-report=term-missing",
        "--cov-fail-under=80",
        "-v",
        "--tb=short",
    ] + sys.argv[1:]
    sys.exit(subprocess.run(cmd, cwd=PROJECT_ROOT).returncode)
