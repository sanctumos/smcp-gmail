"""Unit tests for CLI."""
import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

import cli


class TestDescribeSpec:
    """Test _describe_spec output."""

    def test_has_plugin_and_commands(self):
        spec = cli._describe_spec()
        assert "plugin" in spec
        assert spec["plugin"]["name"] == "smcp-gmail"
        assert "commands" in spec
        assert isinstance(spec["commands"], list)

    def test_commands_have_required_fields(self):
        spec = cli._describe_spec()
        for cmd in spec["commands"]:
            assert "name" in cmd
            assert "description" in cmd
            assert "parameters" in cmd
            assert isinstance(cmd["parameters"], list)

    def test_list_messages_command_present(self):
        spec = cli._describe_spec()
        names = [c["name"] for c in spec["commands"]]
        assert "list-messages" in names
        assert "get-message" in names
        assert "send-message" in names
        assert "list-labels" in names


class TestMain:
    """Test main() with various argv and mocks."""

    def test_describe_prints_json_and_exits_zero(self, capsys):
        with patch.object(sys, "argv", ["cli.py", "--describe"]):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 0
        out, err = capsys.readouterr()
        spec = json.loads(out)
        assert spec["plugin"]["name"] == "smcp-gmail"
        assert len(spec["commands"]) >= 4

    def test_no_command_prints_help_and_exits_one(self, capsys):
        with patch.object(sys, "argv", ["cli.py"]):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 1
        out, err = capsys.readouterr()
        assert "usage" in out.lower() or "Gmail" in out

    def test_list_messages_success(self, capsys):
        pytest.importorskip("google.auth")
        with patch.object(sys, "argv", [
            "cli.py", "list-messages",
            "--user-id", "me", "--query", "is:unread", "--max-results", "3",
        ]), patch("gmail_client.list_messages") as mock_list:
            mock_list.return_value = {"messages": [{"id": "1"}], "nextPageToken": None, "resultSizeEstimate": 1}
            cli.main()
        out, _ = capsys.readouterr()
        data = json.loads(out)
        assert data["messages"] == [{"id": "1"}]
        mock_list.assert_called_once_with(user_id="me", query="is:unread", max_results=3, page_token=None)

    def test_get_message_success(self, capsys):
        pytest.importorskip("google.auth")
        with patch.object(sys, "argv", ["cli.py", "get-message", "--message-id", "msg123", "--format", "full"]), \
             patch("gmail_client.get_message") as mock_get:
            mock_get.return_value = {"id": "msg123", "snippet": "Hi"}
            cli.main()
        out, _ = capsys.readouterr()
        data = json.loads(out)
        assert data["id"] == "msg123"
        mock_get.assert_called_once_with(message_id="msg123", user_id="me", format="full")

    def test_send_message_success(self, capsys):
        pytest.importorskip("google.auth")
        with patch.object(sys, "argv", [
            "cli.py", "send-message",
            "--to", "a@b.com", "--subject", "Subj", "--body", "Body text",
        ]), patch("gmail_client.send_message") as mock_send:
            mock_send.return_value = {"id": "sent1"}
            cli.main()
        out, _ = capsys.readouterr()
        data = json.loads(out)
        assert data["id"] == "sent1"
        mock_send.assert_called_once_with(
            to="a@b.com", subject="Subj", body="Body text",
            user_id="me", cc=None, bcc=None,
        )

    def test_list_labels_success(self, capsys):
        pytest.importorskip("google.auth")
        with patch.object(sys, "argv", ["cli.py", "list-labels"]), \
             patch("gmail_client.list_labels") as mock_labels:
            mock_labels.return_value = {"labels": [{"id": "INBOX", "name": "INBOX"}]}
            cli.main()
        out, _ = capsys.readouterr()
        data = json.loads(out)
        assert data["labels"] == [{"id": "INBOX", "name": "INBOX"}]
        mock_labels.assert_called_once_with(user_id="me")

    def test_file_not_found_prints_json_error_and_exits_one(self, capsys):
        pytest.importorskip("google.auth")
        with patch.object(sys, "argv", ["cli.py", "list-labels"]), \
             patch("gmail_client.list_labels", side_effect=FileNotFoundError("No credentials")):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 1
        out, _ = capsys.readouterr()
        data = json.loads(out)
        assert "error" in data
        assert "credentials" in data["error"].lower() or "No" in data["error"]

    def test_generic_exception_prints_json_error_and_exits_one(self, capsys):
        pytest.importorskip("google.auth")
        with patch.object(sys, "argv", ["cli.py", "list-labels"]), \
             patch("gmail_client.list_labels", side_effect=RuntimeError("API down")):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 1
        out, _ = capsys.readouterr()
        data = json.loads(out)
        assert data["error"] == "API down"
