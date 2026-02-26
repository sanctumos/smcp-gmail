"""End-to-end tests against real Gmail API. Skip unless GMAIL_E2E=1 and credentials exist."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CLI = PROJECT_ROOT / "cli.py"

# Skip all e2e unless explicitly requested and credentials might exist
E2E_ENABLED = os.environ.get("GMAIL_E2E", "").lower() in ("1", "true", "yes")
CREDENTIALS_FILE = os.environ.get("GMAIL_CREDENTIALS_FILE", str(PROJECT_ROOT / "credentials.json"))
TOKEN_FILE = os.environ.get("GMAIL_TOKEN_FILE", str(PROJECT_ROOT / "token.json"))
HAS_CREDENTIALS = Path(CREDENTIALS_FILE).expanduser().exists()
HAS_TOKEN = Path(TOKEN_FILE).expanduser().exists()

skip_e2e = pytest.mark.skipif(
    not E2E_ENABLED or not HAS_CREDENTIALS,
    reason="E2E disabled (set GMAIL_E2E=1 and have credentials.json) or no credentials",
)


@skip_e2e
def test_e2e_list_labels_returns_json():
    """Call list-labels against real Gmail; expect JSON with labels or error."""
    result = subprocess.run(
        [sys.executable, str(CLI), "list-labels"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    import json
    data = json.loads(result.stdout)
    assert "labels" in data
    assert isinstance(data["labels"], list)


@skip_e2e
def test_e2e_list_messages_returns_json():
    """Call list-messages with small max_results; expect JSON."""
    result = subprocess.run(
        [sys.executable, str(CLI), "list-messages", "--max-results", "1"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    import json
    data = json.loads(result.stdout)
    assert "messages" in data
    assert isinstance(data["messages"], list)
