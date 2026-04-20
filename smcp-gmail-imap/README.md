# smcp-gmail-imap

Gmail over **IMAP + SMTP** for **SMCP** and other MCP hosts. **This plugin never runs OAuth, device codes, loopback servers, or any browser flow.** It only consumes credentials you place on disk or in the environment.

## How you get credentials (not this repo)

Pick one path **outside** this plugin, then deploy the resulting secrets to the agent host:

| Mode | You provision |
|------|----------------|
| **XOAUTH2** | A Google **authorized user** JSON (contains `refresh_token`, `client_id`, `client_secret`, `token_uri`, scope `https://mail.google.com/`) — e.g. from a one-off script on your laptop, `gcloud auth application-default login` + export pattern, or your secret manager’s generator. |
| **App password** | `GMAIL_APP_PASSWORD` (where Google still allows it for the account). |
| **Workspace DWD** | Service account JSON + admin domain-wide delegation + `GMAIL_DELEGATED_USER`. |

This repository intentionally does **not** ship a token-minting CLI.

## Runtime environment

**XOAUTH2 (personal Gmail typical):**

- `GMAIL_ADDRESS` — mailbox (SASL `user=` and SMTP From).
- `GMAIL_IMAP_TOKEN_FILE` — path to authorized-user JSON (default: `./gmail_imap_token.json` next to `cli.py`).
- If the JSON lacks `client_id` / `client_secret`, set `GMAIL_OAUTH_CLIENT_SECRETS` or `GMAIL_OAUTH_CLIENT_ID` + `GMAIL_OAUTH_CLIENT_SECRET`.

**App password:**

```bash
export GMAIL_ADDRESS='you@gmail.com'
export GMAIL_APP_PASSWORD='xxxx xxxx xxxx xxxx'
```

**Workspace (service account + delegation):**

```bash
export GMAIL_USE_SERVICE_ACCOUNT=1
export GMAIL_SERVICE_ACCOUNT_JSON=/path/to/sa.json
export GMAIL_DELEGATED_USER=user@yourdomain.com
```

## SMCP

Point `MCP_PLUGINS_DIR` at a parent of the folder **`smcp-gmail-imap`** (with `cli.py` inside). Tools are named per `--describe` (prefix `smcp-gmail-imap__…`).

## Commands

`list-mailboxes`, `search`, `fetch-headers`, `fetch-raw-peek`, `send-message` — see `--describe` JSON.

## Tests

```bash
python3 run_tests.py
```

## Plan

[`docs/IMAP_AGENT_PLUGIN_PLAN.md`](../docs/IMAP_AGENT_PLUGIN_PLAN.md)
