"""
Gmail API client for smcp-gmail plugin.

Uses google-api-python-client with OAuth2 credentials.
Credentials: credentials.json (client secrets), token.json (stored after first auth).
"""
import base64
import os
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Paths: prefer env, then plugin dir, then cwd
_PLUGIN_DIR = Path(__file__).resolve().parent


def _credentials_path() -> Path:
    path = os.getenv("GMAIL_CREDENTIALS_FILE")
    if path:
        return Path(path)
    return _PLUGIN_DIR / "credentials.json"


def _token_path() -> Path:
    path = os.getenv("GMAIL_TOKEN_FILE")
    if path:
        return Path(path)
    return _PLUGIN_DIR / "token.json"


def get_credentials() -> Credentials:
    """Load or obtain OAuth2 credentials."""
    creds = None
    token_path = _token_path()
    creds_path = _credentials_path()

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(
                    f"Credentials file not found: {creds_path}. "
                    "Download from Google Cloud Console and save as credentials.json, "
                    "or set GMAIL_CREDENTIALS_FILE."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds


def get_service():
    """Build Gmail API service."""
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def list_messages(
    user_id: str = "me",
    query: Optional[str] = None,
    max_results: int = 10,
    page_token: Optional[str] = None,
    label_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """List message IDs and thread IDs matching query."""
    service = get_service()
    params: Dict[str, Any] = {"userId": user_id, "maxResults": max_results}
    if query:
        params["q"] = query
    if page_token:
        params["pageToken"] = page_token
    if label_ids:
        params["labelIds"] = label_ids
    response = service.users().messages().list(**params).execute()
    messages = response.get("messages", [])
    return {
        "messages": [{"id": m["id"], "threadId": m.get("threadId")} for m in messages],
        "nextPageToken": response.get("nextPageToken"),
        "resultSizeEstimate": response.get("resultSizeEstimate", 0),
    }


def get_message(
    message_id: str,
    user_id: str = "me",
    format: str = "metadata",
) -> Dict[str, Any]:
    """Get a single message. format: minimal, full, metadata, raw."""
    service = get_service()
    msg = (
        service.users()
        .messages()
        .get(userId=user_id, id=message_id, format=format)
        .execute()
    )
    # Flatten for JSON: payload headers as dict, body snippet
    result = {
        "id": msg.get("id"),
        "threadId": msg.get("threadId"),
        "labelIds": msg.get("labelIds", []),
        "snippet": msg.get("snippet"),
        "internalDate": msg.get("internalDate"),
        "sizeEstimate": msg.get("sizeEstimate"),
    }
    payload = msg.get("payload") or {}
    result["subject"] = _header(payload, "Subject")
    result["from"] = _header(payload, "From")
    result["to"] = _header(payload, "To")
    result["date"] = _header(payload, "Date")
    if format == "full" and "parts" in payload:
        result["body_plain"] = _first_part_body(payload, "text/plain")
        result["body_html"] = _first_part_body(payload, "text/html")
    elif format == "full" and "body" in payload and payload["body"].get("data"):
        result["body"] = _decode_body(payload["body"])
    return result


def _header(payload: Dict, name: str) -> Optional[str]:
    headers = payload.get("headers") or []
    for h in headers:
        if (h.get("name") or "").lower() == name.lower():
            return h.get("value")
    return None


def _decode_body(body: Dict) -> str:
    data = body.get("data")
    if not data:
        return ""
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")


def _first_part_body(payload: Dict, mime_type: str) -> Optional[str]:
    for part in payload.get("parts") or []:
        if (part.get("mimeType") or "").lower() == mime_type:
            if part.get("body", {}).get("data"):
                return _decode_body(part["body"])
    return None


def send_message(
    to: str,
    subject: str,
    body: str,
    user_id: str = "me",
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
) -> Dict[str, Any]:
    """Send an email. body is plain text."""
    service = get_service()
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    if cc:
        message["cc"] = cc
    if bcc:
        message["bcc"] = bcc
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    body_obj = {"raw": raw}
    sent = (
        service.users()
        .messages()
        .send(userId=user_id, body=body_obj)
        .execute()
    )
    return {"id": sent.get("id"), "threadId": sent.get("threadId"), "labelIds": sent.get("labelIds", [])}


def list_labels(user_id: str = "me") -> Dict[str, Any]:
    """List Gmail labels."""
    service = get_service()
    response = service.users().labels().list(userId=user_id).execute()
    labels = response.get("labels", [])
    return {"labels": [{"id": l["id"], "name": l["name"], "type": l.get("type")} for l in labels]}
