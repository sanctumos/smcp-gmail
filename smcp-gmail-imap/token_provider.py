"""Resolve an OAuth access token for XOAUTH2 (user refresh or Workspace SA)."""

from __future__ import annotations

from auth_config import AuthMode, AuthSettings
from oauth_refresh import access_token_for_runtime
from workspace_auth import delegated_access_token


def xoauth2_user_address(settings: AuthSettings) -> str:
    """SASL user= must be the mailbox being accessed (delegated user for DWD)."""
    if settings.mode == AuthMode.SERVICE_ACCOUNT and settings.delegated_user:
        return settings.delegated_user
    return settings.address


def access_token_for_xoauth2(settings: AuthSettings) -> str:
    if settings.mode == AuthMode.APP_PASSWORD:
        raise ValueError("XOAUTH2 requires OAuth or service account; use app_password IMAP login path instead.")
    if settings.mode == AuthMode.SERVICE_ACCOUNT:
        assert settings.service_account_json and settings.delegated_user
        return delegated_access_token(settings.service_account_json, settings.delegated_user)
    assert settings.token_file and settings.client_id and settings.client_secret
    return access_token_for_runtime(settings.token_file, settings.client_id, settings.client_secret)
