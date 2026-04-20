"""XOAUTH2 SASL inner string for Gmail IMAP/SMTP (imaplib encodes to base64 itself)."""

from __future__ import annotations


def xoauth2_inner_bytes(user: str, access_token: str) -> bytes:
    """
    Return the *unencoded* SASL XOAUTH2 payload.
    imaplib.IMAP4.authenticate() base64-encodes the returned bytes.
    For SMTP, base64-encode this value and send as AUTH XOAUTH2 <b64>.
    """
    return f"user={user}\x01auth=Bearer {access_token}\x01\x01".encode("utf-8")


def xoauth2_smtp_base64(user: str, access_token: str) -> str:
    """SMTP AUTH XOAUTH2 expects one base64 blob (no newlines)."""
    import base64

    raw = xoauth2_inner_bytes(user, access_token)
    return base64.b64encode(raw).decode("ascii")
