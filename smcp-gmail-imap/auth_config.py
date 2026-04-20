"""Load auth mode and paths from environment (agent runtime; no interactive OAuth)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


MAIL_SCOPE = "https://mail.google.com/"

_PLUGIN_DIR = Path(__file__).resolve().parent


class AuthMode(str, Enum):
    OAUTH_REFRESH = "oauth_refresh"
    APP_PASSWORD = "app_password"
    SERVICE_ACCOUNT = "service_account"


@dataclass(frozen=True)
class AuthSettings:
    address: str
    mode: AuthMode
    imap_host: str
    smtp_host: str
    imap_timeout: int
    smtp_timeout: int
    fetch_max_bytes: int
    search_max_uids: int
    # oauth_refresh
    token_file: Optional[Path]
    client_secrets_path: Optional[Path]
    client_id: Optional[str]
    client_secret: Optional[str]
    # app password
    app_password: Optional[str]
    # workspace DWD
    service_account_json: Optional[Path]
    delegated_user: Optional[str]


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def _int(name: str, default: int) -> int:
    v = os.environ.get(name)
    if v is None or v == "":
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _load_client_secrets(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if "installed" in data:
        return data["installed"]
    if "web" in data:
        return data["web"]
    raise ValueError("credentials JSON must contain 'installed' or 'web' client config")


def load_auth_settings() -> AuthSettings:
    imap_host = os.environ.get("GMAIL_IMAP_HOST", "imap.gmail.com").strip()
    smtp_host = os.environ.get("GMAIL_SMTP_HOST", "smtp.gmail.com").strip()
    imap_timeout = _int("GMAIL_IMAP_TIMEOUT", 45)
    smtp_timeout = _int("GMAIL_SMTP_TIMEOUT", 45)
    fetch_max_bytes = _int("GMAIL_FETCH_MAX_BYTES", 512_000)
    search_max_uids = _int("GMAIL_SEARCH_MAX_UIDS", 200)

    if _truthy("GMAIL_USE_SERVICE_ACCOUNT"):
        sa = os.environ.get("GMAIL_SERVICE_ACCOUNT_JSON", "").strip()
        subj = os.environ.get("GMAIL_DELEGATED_USER", "").strip()
        if not sa:
            raise ValueError("GMAIL_SERVICE_ACCOUNT_JSON is required when GMAIL_USE_SERVICE_ACCOUNT=1")
        if not subj:
            raise ValueError("GMAIL_DELEGATED_USER is required when GMAIL_USE_SERVICE_ACCOUNT=1")
        addr = os.environ.get("GMAIL_ADDRESS", "").strip() or subj
        return AuthSettings(
            address=addr,
            mode=AuthMode.SERVICE_ACCOUNT,
            imap_host=imap_host,
            smtp_host=smtp_host,
            imap_timeout=imap_timeout,
            smtp_timeout=smtp_timeout,
            fetch_max_bytes=fetch_max_bytes,
            search_max_uids=search_max_uids,
            token_file=None,
            client_secrets_path=None,
            client_id=None,
            client_secret=None,
            app_password=None,
            service_account_json=Path(sa).expanduser(),
            delegated_user=subj,
        )

    addr = os.environ.get("GMAIL_ADDRESS", "").strip()
    if not addr:
        raise ValueError("GMAIL_ADDRESS is required (full mailbox, e.g. you@gmail.com)")

    app_pw = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if app_pw:
        return AuthSettings(
            address=addr,
            mode=AuthMode.APP_PASSWORD,
            imap_host=imap_host,
            smtp_host=smtp_host,
            imap_timeout=imap_timeout,
            smtp_timeout=smtp_timeout,
            fetch_max_bytes=fetch_max_bytes,
            search_max_uids=search_max_uids,
            token_file=None,
            client_secrets_path=None,
            client_id=None,
            client_secret=None,
            app_password=app_pw,
            service_account_json=None,
            delegated_user=None,
        )

    tf = os.environ.get("GMAIL_IMAP_TOKEN_FILE", "").strip()
    token_path = Path(tf).expanduser() if tf else _PLUGIN_DIR / "gmail_imap_token.json"

    cid = os.environ.get("GMAIL_OAUTH_CLIENT_ID", "").strip() or None
    csec = os.environ.get("GMAIL_OAUTH_CLIENT_SECRET", "").strip() or None
    cpath = os.environ.get("GMAIL_OAUTH_CLIENT_SECRETS", "").strip()
    client_secrets: Optional[Path] = Path(cpath).expanduser() if cpath else None

    if token_path.is_file():
        try:
            with open(token_path, encoding="utf-8") as f:
                tokinfo = json.load(f)
            cid = cid or (tokinfo.get("client_id") or "").strip() or None
            csec = csec or (tokinfo.get("client_secret") or "").strip() or None
        except (OSError, json.JSONDecodeError):
            pass

    if not cid and client_secrets and client_secrets.is_file():
        ins = _load_client_secrets(client_secrets)
        cid = ins.get("client_id") or cid
        csec = ins.get("client_secret") or csec

    if not token_path.is_file():
        raise FileNotFoundError(
            f"OAuth token file not found: {token_path}. "
            "Run: python3 cli.py bootstrap-oauth (on any machine), or set GMAIL_IMAP_TOKEN_FILE."
        )
    if not cid or not csec:
        raise ValueError(
            "OAuth runtime requires client id/secret. Set GMAIL_OAUTH_CLIENT_SECRETS "
            "(path to credentials.json) or GMAIL_OAUTH_CLIENT_ID and GMAIL_OAUTH_CLIENT_SECRET."
        )

    return AuthSettings(
        address=addr,
        mode=AuthMode.OAUTH_REFRESH,
        imap_host=imap_host,
        smtp_host=smtp_host,
        imap_timeout=imap_timeout,
        smtp_timeout=smtp_timeout,
        fetch_max_bytes=fetch_max_bytes,
        search_max_uids=search_max_uids,
        token_file=token_path,
        client_secrets_path=client_secrets,
        client_id=cid,
        client_secret=csec,
        app_password=None,
        service_account_json=None,
        delegated_user=None,
    )
