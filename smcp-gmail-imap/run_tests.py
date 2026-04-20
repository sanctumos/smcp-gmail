#!/usr/bin/env python3
"""Pytest + coverage for smcp-gmail-imap (run: python3 smcp-gmail-imap/run_tests.py)."""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


if __name__ == "__main__":
    cov_mods = [
        "auth_config",
        "xoauth2",
        "token_provider",
        "oauth_refresh",
        "workspace_auth",
        "bootstrap_device",
        "imap_ops",
        "smtp_ops",
        "cli",
    ]
    cov_args: list[str] = []
    for m in cov_mods:
        cov_args.extend(["--cov", m])
    env = os.environ.copy()
    pp = str(HERE)
    if env.get("PYTHONPATH"):
        pp += os.pathsep + env["PYTHONPATH"]
    env["PYTHONPATH"] = pp
    cmd = (
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(HERE / "pytest.ini"),
            str(HERE / "tests"),
        ]
        + cov_args
        + ["--cov-report=term-missing", "--cov-fail-under=55"]
        + sys.argv[1:]
    )
    sys.exit(subprocess.run(cmd, cwd=str(HERE), env=env).returncode)
