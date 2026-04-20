"""
OAuth 2.0 device authorization (RFC 8628) for headless bootstrap.

Writes gmail_imap_token.json compatible with google.oauth2.credentials.Credentials.
Requires a Google Cloud OAuth client (Desktop or TV) with client_id + client_secret.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple

from google.oauth2.credentials import Credentials

from auth_config import MAIL_SCOPE, _load_client_secrets

DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def _post_form(url: str, fields: Dict[str, str]) -> Dict[str, Any]:
    body = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_device_flow(client_id: str, client_secret: str) -> Credentials:
    data = _post_form(
        DEVICE_CODE_URL,
        {
            "client_id": client_id,
            "scope": MAIL_SCOPE,
        },
    )
    if "error" in data:
        raise RuntimeError(f"device/code error: {data}")
    device_code = data["device_code"]
    interval = int(data.get("interval", 5))
    expires_in = int(data.get("expires_in", 1800))
    user_code = data["user_code"]
    vurl = data["verification_url"]
    print(f"\nOpen: {vurl}\nEnter code: {user_code}\n", file=sys.stderr)

    start = time.monotonic()
    while time.monotonic() - start < expires_in:
        time.sleep(interval)
        try:
            tok = _post_form(
                TOKEN_URL,
                {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
            )
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err = json.loads(err_body)
            except json.JSONDecodeError:
                raise RuntimeError(f"token HTTP {e.code}: {err_body}") from e
            err_code = err.get("error")
            if err_code in ("authorization_pending", "slow_down"):
                if err_code == "slow_down":
                    interval += 5
                continue
            raise RuntimeError(f"token error: {err}") from e

        if "error" in tok:
            err = tok["error"]
            if err in ("authorization_pending", "slow_down"):
                if err == "slow_down":
                    interval += 5
                continue
            raise RuntimeError(f"token error: {tok}")

        access = tok.get("access_token")
        refresh = tok.get("refresh_token")
        if not access:
            raise RuntimeError(f"Unexpected token response: {tok}")
        return Credentials(
            token=access,
            refresh_token=refresh,
            token_uri=TOKEN_URL,
            client_id=client_id,
            client_secret=client_secret,
            scopes=[MAIL_SCOPE],
        )

    raise TimeoutError("Device authorization timed out before user completed sign-in.")


def bootstrap_from_client_secrets(
    client_secrets_path: Path,
    out_token_path: Path,
) -> None:
    ins = _load_client_secrets(client_secrets_path)
    cid = ins.get("client_id")
    csec = ins.get("client_secret")
    if not cid or not csec:
        raise ValueError("client_secrets JSON missing client_id or client_secret")
    creds = run_device_flow(str(cid), str(csec))
    out_token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    print(f"Wrote token file: {out_token_path}", file=sys.stderr)
