"""Unit tests for IMAP-based cli."""
import json
import sys
from unittest.mock import patch

import pytest

import cli


class TestDescribeSpec:
    def test_plugin_name_and_commands(self):
        spec = cli._describe_spec()
        assert spec["plugin"]["name"] == "smcp-gmail"
        names = {c["name"] for c in spec["commands"]}
        assert names == {
            "list-mailboxes",
            "search",
            "fetch-headers",
            "fetch-raw-peek",
            "send-message",
        }


class TestMain:
    def test_describe_prints_json(self, capsys):
        with patch.object(sys, "argv", ["cli.py", "--describe"]):
            cli.main()
        out, _ = capsys.readouterr()
        assert json.loads(out)["plugin"]["name"] == "smcp-gmail"

    def test_no_command_prints_help(self, capsys):
        with patch.object(sys, "argv", ["cli.py"]):
            with pytest.raises(SystemExit) as ei:
                cli.main()
            assert ei.value.code == 1

    def test_list_mailboxes_success(self, capsys):
        with patch.object(sys, "argv", ["cli.py", "list-mailboxes"]), patch(
            "auth_config.load_auth_settings", return_value=object()
        ), patch("imap_ops.list_mailboxes") as mock_list:
            mock_list.return_value = {"mailboxes": [{"name": "INBOX"}]}
            cli.main()
        out, _ = capsys.readouterr()
        assert json.loads(out)["mailboxes"][0]["name"] == "INBOX"

    def test_search_success(self, capsys):
        with patch.object(
            sys, "argv", ["cli.py", "search", "--folder", "INBOX", "--gmail-raw-query", "is:unread"]
        ), patch("auth_config.load_auth_settings", return_value=object()), patch(
            "imap_ops.search_messages"
        ) as mock_s:
            mock_s.return_value = {"uids": ["1", "2"], "truncated": False}
            cli.main()
        data = json.loads(capsys.readouterr().out)
        assert data["uids"] == ["1", "2"]
