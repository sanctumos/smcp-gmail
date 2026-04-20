"""Refresh user OAuth access token from stored refresh token (runtime; no browser)."""

from __future__ import annotations

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from auth_config import MAIL_SCOPE


def load_credentials(
    token_path: Path,
    client_id: str,
    client_secret: str,
    *,
    write_back: bool = True,
) -> Credentials:
    """Load authorized-user JSON and refresh if needed."""
    with open(token_path, encoding="utf-8") as f:
        info = json.load(f)
    info.setdefault("client_id", client_id)
    info.setdefault("client_secret", client_secret)
    creds = Credentials.from_authorized_user_info(info, scopes=[MAIL_SCOPE])

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        if write_back:
            with open(token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
    if not creds.token:
        raise RuntimeError("No access token after refresh; re-run bootstrap-oauth.")
    return creds


def access_token_for_runtime(
    token_path: Path,
    client_id: str,
    client_secret: str,
) -> str:
    c = load_credentials(token_path, client_id, client_secret, write_back=True)
    return str(c.token)
