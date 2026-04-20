"""Integration tests: run CLI as subprocess and assert JSON/exit codes."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CLI = PROJECT_ROOT / "cli.py"


def run_cli(*args, timeout=10):
    cmd = [sys.executable, str(CLI)] + list(args)
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


class TestDescribeIntegration:
    def test_describe_returns_valid_json(self):
        code, out, err = run_cli("--describe")
        assert code == 0, f"stderr: {err}"
        data = json.loads(out)
        assert data["plugin"]["name"] == "smcp-gmail"
        names = {c["name"] for c in data["commands"]}
        assert names == {
            "list-mailboxes",
            "search",
            "fetch-headers",
            "fetch-raw-peek",
            "send-message",
        }


class TestCliContract:
    def test_no_args_exits_nonzero(self):
        code, out, err = run_cli()
        assert code != 0
        assert "usage" in out.lower() or "imap" in out.lower() or "describe" in out.lower()

    def test_list_mailboxes_without_env_returns_json_error(self):
        code, out, err = run_cli("list-mailboxes")
        assert code == 1
        data = json.loads(out)
        assert "error" in data

    def test_fetch_headers_requires_uids(self):
        code, out, err = run_cli("fetch-headers")
        assert code != 0

    def test_send_message_requires_args(self):
        code, out, err = run_cli("send-message")
        assert code != 0
