#!/usr/bin/env python3
"""
smcp-gmail – Gmail API plugin for SMCP (Model Context Protocol).

Exposes Gmail operations as MCP tools: list messages, get message, send, list labels.
"""

import argparse
import json
import sys
from typing import Any, Dict


def _describe_spec() -> Dict[str, Any]:
    return {
        "plugin": {
            "name": "smcp-gmail",
            "version": "1.0.0",
            "description": "Gmail API plugin: list messages, get message, send email, list labels.",
        },
        "commands": [
            {
                "name": "list-messages",
                "description": "List Gmail message IDs matching an optional query (e.g. from:user@example.com is:unread).",
                "parameters": [
                    {"name": "user_id", "type": "string", "description": "Gmail user (default: me)", "required": False, "default": "me"},
                    {"name": "query", "type": "string", "description": "Gmail search query", "required": False, "default": None},
                    {"name": "max_results", "type": "integer", "description": "Max messages to return (default 10)", "required": False, "default": 10},
                    {"name": "page_token", "type": "string", "description": "Page token for pagination", "required": False, "default": None},
                ],
            },
            {
                "name": "get-message",
                "description": "Get a single Gmail message by ID (metadata or full body).",
                "parameters": [
                    {"name": "message_id", "type": "string", "description": "Gmail message ID", "required": True, "default": None},
                    {"name": "user_id", "type": "string", "description": "Gmail user (default: me)", "required": False, "default": "me"},
                    {"name": "format", "type": "string", "description": "minimal, full, metadata, raw (default: metadata)", "required": False, "default": "metadata"},
                ],
            },
            {
                "name": "send-message",
                "description": "Send an email via Gmail.",
                "parameters": [
                    {"name": "to", "type": "string", "description": "To address", "required": True, "default": None},
                    {"name": "subject", "type": "string", "description": "Subject line", "required": True, "default": None},
                    {"name": "body", "type": "string", "description": "Plain-text body", "required": True, "default": None},
                    {"name": "user_id", "type": "string", "description": "Gmail user (default: me)", "required": False, "default": "me"},
                    {"name": "cc", "type": "string", "description": "CC addresses (comma-separated)", "required": False, "default": None},
                    {"name": "bcc", "type": "string", "description": "BCC addresses (comma-separated)", "required": False, "default": None},
                ],
            },
            {
                "name": "list-labels",
                "description": "List Gmail labels for the user.",
                "parameters": [
                    {"name": "user_id", "type": "string", "description": "Gmail user (default: me)", "required": False, "default": "me"},
                ],
            },
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gmail API plugin for SMCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--describe",
        action="store_true",
        help="Output plugin spec as JSON for SMCP discovery",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # list-messages
    p_list = subparsers.add_parser("list-messages", help="List messages")
    p_list.add_argument("--user-id", default="me", help="Gmail user")
    p_list.add_argument("--query", default=None, help="Gmail search query")
    p_list.add_argument("--max-results", type=int, default=10, help="Max results")
    p_list.add_argument("--page-token", default=None, help="Page token")

    # get-message
    p_get = subparsers.add_parser("get-message", help="Get a message")
    p_get.add_argument("--message-id", required=True, help="Message ID")
    p_get.add_argument("--user-id", default="me", help="Gmail user")
    p_get.add_argument("--format", default="metadata", choices=["minimal", "full", "metadata", "raw"], help="Message format")

    # send-message
    p_send = subparsers.add_parser("send-message", help="Send an email")
    p_send.add_argument("--to", required=True, help="To address")
    p_send.add_argument("--subject", required=True, help="Subject")
    p_send.add_argument("--body", required=True, help="Body (plain text)")
    p_send.add_argument("--user-id", default="me", help="Gmail user")
    p_send.add_argument("--cc", default=None, help="CC addresses")
    p_send.add_argument("--bcc", default=None, help="BCC addresses")

    # list-labels
    p_labels = subparsers.add_parser("list-labels", help="List labels")
    p_labels.add_argument("--user-id", default="me", help="Gmail user")

    args = parser.parse_args()

    if args.describe:
        print(json.dumps(_describe_spec()))
        sys.exit(0)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    from gmail_client import (
        get_message,
        list_labels,
        list_messages,
        send_message,
    )

    try:
        if args.command == "list-messages":
            result = list_messages(
                user_id=args.user_id,
                query=args.query,
                max_results=args.max_results,
                page_token=args.page_token,
            )
        elif args.command == "get-message":
            result = get_message(
                message_id=args.message_id,
                user_id=args.user_id,
                format=args.format,
            )
        elif args.command == "send-message":
            result = send_message(
                to=args.to,
                subject=args.subject,
                body=args.body,
                user_id=args.user_id,
                cc=args.cc,
                bcc=args.bcc,
            )
        elif args.command == "list-labels":
            result = list_labels(user_id=args.user_id)
        else:
            result = {"error": f"Unknown command: {args.command}"}

        print(json.dumps(result))
        sys.exit(0 if "error" not in result else 1)
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
