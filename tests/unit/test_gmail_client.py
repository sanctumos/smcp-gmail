"""Unit tests for gmail_client."""
import base64
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Skip entire module if Gmail API deps not installed (e.g. in CI without deps)
pytest.importorskip("google.auth")
# Import after path is set by conftest
import gmail_client as gc


class TestPathHelpers:
    """Test _credentials_path and _token_path."""

    def test_credentials_path_default(self):
        with patch.dict(os.environ, {}, clear=False):
            # Remove env if set
            os.environ.pop("GMAIL_CREDENTIALS_FILE", None)
            p = gc._credentials_path()
        assert p == gc._PLUGIN_DIR / "credentials.json"

    def test_credentials_path_env(self):
        with patch.dict(os.environ, {"GMAIL_CREDENTIALS_FILE": "/tmp/creds.json"}):
            p = gc._credentials_path()
        assert p == Path("/tmp/creds.json")

    def test_token_path_default(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GMAIL_TOKEN_FILE", None)
            p = gc._token_path()
        assert p == gc._PLUGIN_DIR / "token.json"

    def test_token_path_env(self):
        with patch.dict(os.environ, {"GMAIL_TOKEN_FILE": "/tmp/token.json"}):
            p = gc._token_path()
        assert p == Path("/tmp/token.json")


class TestHeader:
    """Test _header extraction from payload."""

    def test_finds_subject(self):
        payload = {"headers": [{"name": "Subject", "value": "Hello"}]}
        assert gc._header(payload, "Subject") == "Hello"

    def test_case_insensitive(self):
        payload = {"headers": [{"name": "FROM", "value": "a@b.com"}]}
        assert gc._header(payload, "from") == "a@b.com"

    def test_missing_returns_none(self):
        payload = {"headers": [{"name": "Other", "value": "x"}]}
        assert gc._header(payload, "Subject") is None

    def test_empty_headers(self):
        assert gc._header({}, "Subject") is None
        assert gc._header({"headers": []}, "Subject") is None


class TestDecodeBody:
    """Test _decode_body."""

    def test_decodes_base64(self):
        text = "Hello world"
        encoded = base64.urlsafe_b64encode(text.encode("utf-8")).decode("utf-8")
        assert gc._decode_body({"data": encoded}) == text

    def test_empty_data(self):
        assert gc._decode_body({}) == ""
        assert gc._decode_body({"data": None}) == ""


class TestFirstPartBody:
    """Test _first_part_body."""

    def test_finds_text_plain(self):
        encoded = base64.urlsafe_b64encode(b"plain").decode("utf-8")
        payload = {"parts": [{"mimeType": "text/plain", "body": {"data": encoded}}]}
        assert gc._first_part_body(payload, "text/plain") == "plain"

    def test_finds_text_html(self):
        encoded = base64.urlsafe_b64encode(b"<p>hi</p>").decode("utf-8")
        payload = {"parts": [{"mimeType": "text/html", "body": {"data": encoded}}]}
        assert gc._first_part_body(payload, "text/html") == "<p>hi</p>"

    def test_no_matching_part(self):
        payload = {"parts": [{"mimeType": "application/octet-stream"}]}
        assert gc._first_part_body(payload, "text/plain") is None

    def test_empty_parts(self):
        assert gc._first_part_body({}, "text/plain") is None


class TestGetCredentials:
    """Test get_credentials (mocked)."""

    def test_raises_when_no_creds_file(self):
        with patch.object(gc, "_token_path", return_value=Path("/nonexistent/token.json")), \
             patch.object(gc, "_credentials_path", return_value=Path("/nonexistent/creds.json")), \
             patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError) as exc_info:
                gc.get_credentials()
            assert "Credentials file not found" in str(exc_info.value)


class TestListMessages:
    """Test list_messages with mocked service."""

    def test_returns_messages_and_token(self):
        mock_service = MagicMock()
        mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            "messages": [{"id": "id1", "threadId": "t1"}],
            "nextPageToken": "tok",
            "resultSizeEstimate": 1,
        }
        with patch.object(gc, "get_service", return_value=mock_service):
            out = gc.list_messages(user_id="me", query="is:unread", max_results=5)
        assert out["messages"] == [{"id": "id1", "threadId": "t1"}]
        assert out["nextPageToken"] == "tok"
        assert out["resultSizeEstimate"] == 1
        call_kw = mock_service.users.return_value.messages.return_value.list.call_args[1]
        assert call_kw["userId"] == "me"
        assert call_kw["q"] == "is:unread"
        assert call_kw["maxResults"] == 5

    def test_empty_messages(self):
        mock_service = MagicMock()
        mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            "messages": [],
            "resultSizeEstimate": 0,
        }
        with patch.object(gc, "get_service", return_value=mock_service):
            out = gc.list_messages()
        assert out["messages"] == []
        assert out.get("resultSizeEstimate") == 0


class TestGetMessage:
    """Test get_message with mocked service."""

    def test_metadata_format(self):
        mock_service = MagicMock()
        mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "id": "m1",
            "threadId": "t1",
            "labelIds": ["INBOX"],
            "snippet": "Snippet",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Subj"},
                    {"name": "From", "value": "a@b.com"},
                    {"name": "To", "value": "c@d.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 00:00:00"},
                ]
            },
        }
        with patch.object(gc, "get_service", return_value=mock_service):
            out = gc.get_message("m1", format="metadata")
        assert out["id"] == "m1"
        assert out["subject"] == "Subj"
        assert out["from"] == "a@b.com"
        assert out["to"] == "c@d.com"
        assert out["date"] == "Mon, 1 Jan 2024 00:00:00"

    def test_full_format_with_parts(self):
        mock_service = MagicMock()
        enc = base64.urlsafe_b64encode(b"plain body").decode("utf-8")
        mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "id": "m1",
            "threadId": "t1",
            "labelIds": [],
            "snippet": "",
            "payload": {
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": enc}},
                    {"mimeType": "text/html", "body": {"data": base64.urlsafe_b64encode(b"<p>hi</p>").decode("utf-8")}},
                ]
            },
        }
        with patch.object(gc, "get_service", return_value=mock_service):
            out = gc.get_message("m1", format="full")
        assert out["body_plain"] == "plain body"
        assert out["body_html"] == "<p>hi</p>"

    def test_full_format_single_body(self):
        mock_service = MagicMock()
        enc = base64.urlsafe_b64encode(b"single part").decode("utf-8")
        mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "id": "m1",
            "threadId": "t1",
            "labelIds": [],
            "snippet": "",
            "payload": {"body": {"data": enc}},
        }
        with patch.object(gc, "get_service", return_value=mock_service):
            out = gc.get_message("m1", format="full")
        assert out["body"] == "single part"


class TestSendMessage:
    """Test send_message with mocked service."""

    def test_send_returns_id(self):
        mock_service = MagicMock()
        mock_service.users.return_value.messages.return_value.send.return_value.execute.return_value = {
            "id": "sent1",
            "threadId": "t1",
            "labelIds": ["SENT"],
        }
        with patch.object(gc, "get_service", return_value=mock_service):
            out = gc.send_message(to="a@b.com", subject="Hi", body="Hello")
        assert out["id"] == "sent1"
        assert out["threadId"] == "t1"
        call_kw = mock_service.users.return_value.messages.return_value.send.call_args[1]
        assert call_kw["userId"] == "me"
        assert "raw" in call_kw["body"]

    def test_send_with_cc_bcc(self):
        mock_service = MagicMock()
        mock_service.users.return_value.messages.return_value.send.return_value.execute.return_value = {"id": "1"}
        with patch.object(gc, "get_service", return_value=mock_service):
            gc.send_message(to="a@b.com", subject="S", body="B", cc="c@d.com", bcc="e@f.com")
        # Just ensure no error; MIMEText sets CC/BCC
        call_kw = mock_service.users.return_value.messages.return_value.send.call_args[1]
        raw = base64.urlsafe_b64decode(call_kw["body"]["raw"])
        assert b"c@d.com" in raw
        assert b"e@f.com" in raw


class TestListLabels:
    """Test list_labels with mocked service."""

    def test_returns_labels(self):
        mock_service = MagicMock()
        mock_service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
            "labels": [{"id": "lid1", "name": "INBOX", "type": "system"}],
        }
        with patch.object(gc, "get_service", return_value=mock_service):
            out = gc.list_labels(user_id="me")
        assert out["labels"] == [{"id": "lid1", "name": "INBOX", "type": "system"}]
        call_kw = mock_service.users.return_value.labels.return_value.list.call_args[1]
        assert call_kw["userId"] == "me"
