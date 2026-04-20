"""SMTP submission to Gmail (XOAUTH2 or app password)."""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from auth_config import AuthMode, AuthSettings
from token_provider import access_token_for_xoauth2, xoauth2_user_address
from xoauth2 import xoauth2_smtp_base64


def send_message(
    settings: AuthSettings,
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
) -> Dict[str, str]:
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.address
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    recipients: List[str] = []
    for part in [to, cc or "", bcc or ""]:
        for x in part.split(","):
            x = x.strip()
            if x and x not in recipients:
                recipients.append(x)

    smtp = smtplib.SMTP_SSL(settings.smtp_host, 465, timeout=settings.smtp_timeout)
    try:
        smtp.ehlo()
        if settings.mode == AuthMode.APP_PASSWORD:
            smtp.login(settings.address, settings.app_password or "")
        else:
            tok = access_token_for_xoauth2(settings)
            user = xoauth2_user_address(settings)
            auth_b64 = xoauth2_smtp_base64(user, tok)
            code, resp = smtp.docmd("AUTH", "XOAUTH2 " + auth_b64)
            if code != 235:
                raise RuntimeError(f"SMTP XOAUTH2 failed: {code} {resp!r}")
        smtp.sendmail(settings.address, recipients, msg.as_string())
        return {"status": "sent", "to": to}
    finally:
        try:
            smtp.quit()
        except Exception:
            pass
