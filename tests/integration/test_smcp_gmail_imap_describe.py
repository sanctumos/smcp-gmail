"""Smoke: smcp-gmail-imap --describe via subprocess (avoids sys.path clash with root cli)."""

import json
import subprocess
import sys
from pathlib import Path

IMAP_CLI = Path(__file__).resolve().parents[2] / "smcp-gmail-imap" / "cli.py"


def test_smcp_gmail_imap_describe():
    r = subprocess.run(
        [sys.executable, str(IMAP_CLI), "--describe"],
        cwd=str(IMAP_CLI.parent),
        capture_output=True,
        text=True,
        check=True,
    )
    spec = json.loads(r.stdout)
    assert spec["plugin"]["name"] == "smcp-gmail-imap"
