#!/usr/bin/env python3
"""
smcp-gmail-imap — Gmail over IMAP + SMTP for SMCP (agent-safe).

This process never starts OAuth, device codes, or browsers. It only reads secrets
and refresh tokens you provision out-of-band (vault, CI, laptop script elsewhere).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _plugin_dir() -> Path:
    return Path(__file__).resolve().parent


def _describe_spec() -> Dict[str, Any]:
    return {
        "plugin": {
            "name": "smcp-gmail-imap",
            "version": "2.0.1",
            "description": "Gmail via IMAP+SMTP for agents: mailboxes, UID search (X-GM-RAW), fetch, send. Runtime only: XOAUTH2 from pre-provisioned token JSON, app password, or Workspace service-account delegation. No OAuth or browser flows in this plugin.",
        },
        "commands": [
            {
                "name": "list-mailboxes",
                "description": "IMAP LIST mailboxes (Gmail labels as folders).",
                "parameters": [],
            },
            {
                "name": "search",
                "description": "UID SEARCH in a folder; optional Gmail raw query (X-GM-RAW) when server supports it.",
                "parameters": [
                    {"name": "folder", "type": "string", "required": False, "default": "INBOX"},
                    {"name": "gmail_raw_query", "type": "string", "required": False, "default": None},
                ],
            },
            {
                "name": "fetch-headers",
                "description": "UID FETCH selected header fields (BODY.PEEK) for one or more UIDs.",
                "parameters": [
                    {"name": "folder", "type": "string", "required": False, "default": "INBOX"},
                    {"name": "uids", "type": "string", "required": True, "default": None},
                ],
            },
            {
                "name": "fetch-raw-peek",
                "description": "UID FETCH BODY.PEEK[] for one UID (base64 RFC822 chunk, size-capped).",
                "parameters": [
                    {"name": "folder", "type": "string", "required": False, "default": "INBOX"},
                    {"name": "uid", "type": "string", "required": True, "default": None},
                ],
            },
            {
                "name": "send-message",
                "description": "Send plain-text email via SMTP submission (XOAUTH2 or app password).",
                "parameters": [
                    {"name": "to", "type": "string", "required": True, "default": None},
                    {"name": "subject", "type": "string", "required": True, "default": None},
                    {"name": "body", "type": "string", "required": True, "default": None},
                    {"name": "cc", "type": "string", "required": False, "default": None},
                    {"name": "bcc", "type": "string", "required": False, "default": None},
                ],
            },
        ],
    }


def _ensure_path() -> None:
    pd = str(_plugin_dir())
    if pd not in sys.path:
        sys.path.insert(0, pd)


def main() -> None:
    _ensure_path()
    parser = argparse.ArgumentParser(
        description="smcp-gmail-imap — Gmail IMAP/SMTP for SMCP (no in-process OAuth)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--describe",
        action="store_true",
        help="Emit SMCP plugin JSON spec",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list-mailboxes", help="List IMAP mailboxes")

    p_s = sub.add_parser("search", help="UID SEARCH")
    p_s.add_argument("--folder", default="INBOX")
    p_s.add_argument("--gmail-raw-query", default=None, dest="gmail_raw_query")

    p_fh = sub.add_parser("fetch-headers", help="Fetch headers for UIDs")
    p_fh.add_argument("--folder", default="INBOX")
    p_fh.add_argument("--uids", required=True, help="Comma-separated IMAP UIDs")

    p_fr = sub.add_parser("fetch-raw-peek", help="Fetch raw message PEEK for one UID")
    p_fr.add_argument("--folder", default="INBOX")
    p_fr.add_argument("--uid", required=True)

    p_send = sub.add_parser("send-message", help="SMTP send")
    p_send.add_argument("--to", required=True)
    p_send.add_argument("--subject", required=True)
    p_send.add_argument("--body", required=True)
    p_send.add_argument("--cc", default=None)
    p_send.add_argument("--bcc", default=None)

    args = parser.parse_args()
    if args.describe:
        print(json.dumps(_describe_spec()))
        return

    if not args.command:
        parser.print_help()
        sys.exit(1)

    from auth_config import load_auth_settings
    from imap_ops import fetch_headers, fetch_raw_peek, list_mailboxes, search_messages
    from smtp_ops import send_message

    try:
        settings = load_auth_settings()
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    try:
        if args.command == "list-mailboxes":
            out = list_mailboxes(settings)
        elif args.command == "search":
            out = search_messages(
                settings,
                folder=args.folder,
                gmail_raw_query=args.gmail_raw_query,
            )
        elif args.command == "fetch-headers":
            uids: List[str] = [x.strip() for x in args.uids.split(",") if x.strip()]
            out = fetch_headers(settings, args.folder, uids)
        elif args.command == "fetch-raw-peek":
            out = fetch_raw_peek(settings, args.folder, args.uid)
        elif args.command == "send-message":
            out = send_message(settings, args.to, args.subject, args.body, cc=args.cc, bcc=args.bcc)
        else:
            print(json.dumps({"error": f"unknown command {args.command}"}))
            sys.exit(1)
        print(json.dumps(out))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
