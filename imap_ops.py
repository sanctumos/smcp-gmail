"""IMAP operations against Gmail (XOAUTH2 or app password)."""

from __future__ import annotations

import email
import imaplib
import re
from typing import Any, Dict, List, Optional, Tuple

from auth_config import AuthMode, AuthSettings
from token_provider import access_token_for_xoauth2, xoauth2_user_address
from xoauth2 import xoauth2_inner_bytes


def _select_mailbox(imap: imaplib.IMAP4_SSL, folder: str) -> Tuple[str, Any]:
    if folder.upper() == "INBOX":
        return imap.select("INBOX")
    escaped = folder.replace("\\", "\\\\").replace('"', '\\"')
    return imap.select(f'"{escaped}"')


def _connect(settings: AuthSettings) -> imaplib.IMAP4_SSL:
    imap = imaplib.IMAP4_SSL(settings.imap_host, 993, timeout=settings.imap_timeout)
    if settings.mode == AuthMode.APP_PASSWORD:
        imap.login(settings.address, settings.app_password or "")
        return imap

    token = access_token_for_xoauth2(settings)
    inner = xoauth2_inner_bytes(xoauth2_user_address(settings), token)

    def authobject(_challenge: bytes) -> bytes:
        return inner

    imap.authenticate("XOAUTH2", authobject)
    return imap


def _has_gmail_extensions(imap: imaplib.IMAP4_SSL) -> bool:
    typ, data = imap.capability()
    if typ != "OK" or not data:
        return False
    caps = data[0].decode("utf-8", errors="replace").upper()
    return "X-GM-EXT-1" in caps


def list_mailboxes(settings: AuthSettings) -> Dict[str, Any]:
    imap = _connect(settings)
    try:
        typ, data = imap.list()
        if typ != "OK":
            return {"error": f"LIST failed: {typ}", "mailboxes": []}
        mailboxes: List[Dict[str, str]] = []
        for row in data or []:
            if not isinstance(row, (bytes, bytearray)):
                continue
            s = row.decode("utf-8", errors="replace")
            # Parse: (\HasChildren \Noselect) "/" "[Gmail]"
            m = re.match(r'^\(([^)]*)\)\s+"([^"]*)"\s+(.+)$', s)
            if m:
                flags, _sep, name = m.group(1), m.group(2), m.group(3)
                mailboxes.append({"flags": flags.strip(), "name": name.strip('"')})
            else:
                mailboxes.append({"flags": "", "name": s})
        return {"mailboxes": mailboxes}
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def search_messages(
    settings: AuthSettings,
    folder: str = "INBOX",
    gmail_raw_query: Optional[str] = None,
    *,
    uid_search_fallback: str = "ALL",
) -> Dict[str, Any]:
    imap = _connect(settings)
    try:
        typ, _ = _select_mailbox(imap, folder)
        if typ != "OK":
            return {"error": f"SELECT {folder} failed: {typ}", "uids": []}
        use_raw = gmail_raw_query and _has_gmail_extensions(imap)
        if use_raw:
            typ, data = imap.uid("SEARCH", "X-GM-RAW", gmail_raw_query)
        else:
            typ, data = imap.uid("SEARCH", uid_search_fallback)
        if typ != "OK" or not data:
            return {"uids": [], "note": None if use_raw else "no X-GM-RAW or empty result"}
        raw = data[0]
        if not isinstance(raw, (bytes, bytearray)):
            return {"uids": []}
        parts = raw.split()
        if not parts:
            return {"uids": []}
        uids = [p.decode("ascii") for p in parts if p.isdigit()]
        cap = settings.search_max_uids
        truncated = len(uids) > cap
        uids = uids[:cap]
        out: Dict[str, Any] = {"uids": uids, "truncated": truncated}
        if use_raw:
            out["query_mode"] = "X-GM-RAW"
        else:
            out["query_mode"] = uid_search_fallback
            if gmail_raw_query and not use_raw:
                out["note"] = "X-GM-EXT-1 not advertised; used fallback UID SEARCH"
        return out
    finally:
        try:
            imap.close()
        except Exception:
            pass
        try:
            imap.logout()
        except Exception:
            pass


def fetch_headers(
    settings: AuthSettings,
    folder: str,
    uids: List[str],
) -> Dict[str, Any]:
    if not uids:
        return {"messages": []}
    imap = _connect(settings)
    try:
        typ, _ = _select_mailbox(imap, folder)
        if typ != "OK":
            return {"error": f"SELECT {folder} failed: {typ}", "messages": []}
        messages: List[Dict[str, Any]] = []
        for uid in uids:
            typ, data = imap.uid(
                "FETCH",
                uid,
                "(UID BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE MESSAGE-ID)])",
            )
            if typ != "OK":
                messages.append({"uid": uid, "error": f"FETCH failed: {typ}"})
                continue
            header_blob = _extract_first_literal_bytes(data)
            if header_blob is None:
                messages.append({"uid": uid, "error": "empty_fetch_response"})
                continue
            if len(header_blob) > settings.fetch_max_bytes:
                messages.append({"uid": uid, "error": "header_block_exceeds_GMAIL_FETCH_MAX_BYTES"})
                continue
            try:
                msg = email.message_from_bytes(header_blob)
                messages.append(
                    {
                        "uid": uid,
                        "from": msg.get("From"),
                        "to": msg.get("To"),
                        "subject": msg.get("Subject"),
                        "date": msg.get("Date"),
                        "message_id": msg.get("Message-ID"),
                    }
                )
            except Exception as e:
                messages.append({"uid": uid, "parse_error": str(e)})
        return {"messages": messages}
    finally:
        try:
            imap.close()
        except Exception:
            pass
        try:
            imap.logout()
        except Exception:
            pass


def _extract_first_literal_bytes(data: Any) -> Optional[bytes]:
    """Pull first literal body bytes from imaplib FETCH response."""
    if not data:
        return None
    for item in data:
        if isinstance(item, tuple):
            for sub in item:
                if isinstance(sub, (bytes, bytearray)) and len(sub) > 0:
                    # Heuristic: skip short status lines
                    if len(sub) > 20 or b"\n" in sub[:200]:
                        return bytes(sub)
        elif isinstance(item, (bytes, bytearray)) and len(item) > 20:
            return bytes(item)
    return None


def fetch_raw_peek(
    settings: AuthSettings,
    folder: str,
    uid: str,
) -> Dict[str, Any]:
    """Fetch full RFC822 with BODY.PEEK[] capped by GMAIL_FETCH_MAX_BYTES (best-effort)."""
    imap = _connect(settings)
    try:
        typ, _ = _select_mailbox(imap, folder)
        if typ != "OK":
            return {"error": f"SELECT {folder} failed: {typ}"}
        typ, data = imap.uid("FETCH", uid, "(UID BODY.PEEK[])")
        if typ != "OK":
            return {"error": f"FETCH failed: {typ}"}
        blob = _extract_first_literal_bytes(data) or b""
        truncated = len(blob) >= settings.fetch_max_bytes
        if len(blob) > settings.fetch_max_bytes:
            blob = blob[: settings.fetch_max_bytes]
            truncated = True
        import base64

        return {
            "uid": uid,
            "truncated": truncated,
            "rfc822_peek_base64": base64.b64encode(blob).decode("ascii"),
        }
    finally:
        try:
            imap.close()
        except Exception:
            pass
        try:
            imap.logout()
        except Exception:
            pass
