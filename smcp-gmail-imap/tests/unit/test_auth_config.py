import json
import os
from pathlib import Path

import pytest

from auth_config import AuthMode, load_auth_settings


def test_load_auth_app_password(tmp_path, monkeypatch):
    monkeypatch.delenv("GMAIL_USE_SERVICE_ACCOUNT", raising=False)
    monkeypatch.setenv("GMAIL_ADDRESS", "me@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "abcdabcdabcdabcd")
    s = load_auth_settings()
    assert s.mode == AuthMode.APP_PASSWORD
    assert s.app_password == "abcdabcdabcdabcd"


def test_load_auth_oauth_reads_client_from_token(tmp_path, monkeypatch):
    monkeypatch.delenv("GMAIL_USE_SERVICE_ACCOUNT", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    tok = tmp_path / "t.json"
    tok.write_text(
        json.dumps(
            {
                "refresh_token": "r",
                "token": "access",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "cid.apps.googleusercontent.com",
                "client_secret": "shh",
                "scopes": ["https://mail.google.com/"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("GMAIL_ADDRESS", "me@gmail.com")
    monkeypatch.setenv("GMAIL_IMAP_TOKEN_FILE", str(tok))
    s = load_auth_settings()
    assert s.mode == AuthMode.OAUTH_REFRESH
    assert s.client_id == "cid.apps.googleusercontent.com"
    assert s.client_secret == "shh"


def test_service_account_defaults_address(monkeypatch):
    monkeypatch.setenv("GMAIL_USE_SERVICE_ACCOUNT", "1")
    monkeypatch.setenv("GMAIL_SERVICE_ACCOUNT_JSON", "/tmp/sa.json")
    monkeypatch.setenv("GMAIL_DELEGATED_USER", "exec@company.com")
    monkeypatch.delenv("GMAIL_ADDRESS", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    s = load_auth_settings()
    assert s.mode == AuthMode.SERVICE_ACCOUNT
    assert s.address == "exec@company.com"
