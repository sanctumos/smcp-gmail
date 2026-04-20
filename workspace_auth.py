"""Google Workspace: domain-wide delegated service account → access token for IMAP/SMTP XOAUTH2."""

from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2 import service_account

from auth_config import MAIL_SCOPE


def delegated_access_token(service_account_json: Path, delegated_user: str) -> str:
    """
    Use a service account JSON key with admin-configured domain-wide delegation
    to impersonate `delegated_user` (full email). Scope must include mail.
    """
    base = service_account.Credentials.from_service_account_file(
        str(service_account_json),
        scopes=[MAIL_SCOPE],
    )
    creds = base.with_subject(delegated_user)
    creds.refresh(Request())
    if not creds.token:
        raise RuntimeError("Service account delegation produced no access token.")
    return str(creds.token)
