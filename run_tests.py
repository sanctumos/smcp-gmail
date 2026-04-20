#!/usr/bin/env python3
"""Run test suite with coverage. Usage: python run_tests.py [pytest args...]"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    cov_mods = [
        "cli",
        "auth_config",
        "xoauth2",
        "token_provider",
        "oauth_refresh",
        "workspace_auth",
        "imap_ops",
        "smtp_ops",
    ]
    cov_args: list[str] = []
    for m in cov_mods:
        cov_args.extend(["--cov", m])
    cmd = (
        [sys.executable, "-m", "pytest", "tests"]
        + cov_args
        + ["--cov-report=term-missing", "--cov-fail-under=40", "-v", "--tb=short"]
        + sys.argv[1:]
    )
    sys.exit(subprocess.run(cmd, cwd=PROJECT_ROOT).returncode)
