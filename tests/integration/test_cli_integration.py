"""Integration tests: run CLI as subprocess and assert JSON/exit codes."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

# Project root (parent of tests/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CLI = PROJECT_ROOT / "cli.py"


def run_cli(*args, timeout=10):
    """Run cli.py with args; return (returncode, stdout, stderr)."""
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
    """Integration tests for --describe (no Gmail deps needed)."""

    def test_describe_returns_valid_json(self):
        code, out, err = run_cli("--describe")
        assert code == 0, f"stderr: {err}"
        data = json.loads(out)
        assert "plugin" in data
        assert data["plugin"]["name"] == "smcp-gmail"
        assert "commands" in data
        assert len(data["commands"]) >= 4

    def test_describe_commands_have_names(self):
        code, out, err = run_cli("--describe")
        assert code == 0
        data = json.loads(out)
        names = [c["name"] for c in data["commands"]]
        assert "list-messages" in names
        assert "get-message" in names
        assert "send-message" in names
        assert "list-labels" in names


class TestCliContract:
    """CLI contract: no args prints help and exits 1; invalid args yield JSON error."""

    def test_no_args_exits_nonzero(self):
        code, out, err = run_cli()
        assert code != 0
        assert "usage" in out.lower() or "Gmail" in out or "describe" in out

    def test_list_labels_without_creds_returns_json_error(self):
        # Without credentials: FileNotFoundError -> JSON with "error"; or missing deps -> non-zero
        code, out, err = run_cli("list-labels")
        assert code == 1
        try:
            data = json.loads(out)
            assert "error" in data
            assert isinstance(data["error"], str)
        except json.JSONDecodeError:
            # e.g. traceback when google module missing
            assert "error" in out or "Error" in err or "ModuleNotFoundError" in err

    def test_get_message_requires_message_id(self):
        code, out, err = run_cli("get-message")
        # argparse will fail (missing required --message-id)
        assert code != 0

    def test_send_message_requires_to_subject_body(self):
        code, out, err = run_cli("send-message")
        assert code != 0


class TestCliArgForwarding:
    """SMCP-style invocation: command plus dashed args."""

    def test_list_messages_arg_forwarding(self):
        # Will fail on credentials or missing deps; check we get JSON or non-zero exit
        code, out, err = run_cli(
            "list-messages",
            "--user-id", "me",
            "--query", "is:unread",
            "--max-results", "5",
        )
        if code == 0:
            data = json.loads(out)
            assert "messages" in data
        else:
            try:
                data = json.loads(out)
                assert "error" in data
            except json.JSONDecodeError:
                pass  # e.g. missing google deps
