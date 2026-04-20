# smcp-gmail

**Gmail over IMAP + SMTP** for **[SMCP](https://github.com/sanctumos/smcp)**. Built for **agents and headless servers**: **no Gmail REST API**, **no OAuth or browser flows in this process** — you provision **refresh-token JSON**, **app passwords**, or **Workspace service-account delegation** outside this repo, then point env vars at them.

**Version 3.x** replaces the old Gmail REST + `run_local_server` plugin entirely.

---

## Requirements

- Python **3.10+** (3.13 tested)
- `pip install -r requirements.txt` → `google-auth`, `requests` (stdlib `imaplib` / `smtplib`)

---

## Authentication (pick one)

### XOAUTH2 (refresh token JSON)

1. Obtain a Google **authorized-user** JSON (`refresh_token`, `client_id`, `client_secret`, `token_uri`, scope `https://mail.google.com/`) using **your own** tooling (not shipped here). Save as e.g. `gmail_imap_token.json`.

2. Env:

   - **`GMAIL_ADDRESS`** — full mailbox (e.g. `you@gmail.com`).
   - **`GMAIL_IMAP_TOKEN_FILE`** — path to that JSON (default: `./gmail_imap_token.json` next to `cli.py`).
   - If the JSON omits client fields: **`GMAIL_OAUTH_CLIENT_SECRETS`** or **`GMAIL_OAUTH_CLIENT_ID`** + **`GMAIL_OAUTH_CLIENT_SECRET`**.

### App password

```bash
export GMAIL_ADDRESS='you@gmail.com'
export GMAIL_APP_PASSWORD='xxxx xxxx xxxx xxxx'
```

### Google Workspace (service account + DWD)

Admin configures domain-wide delegation for scope `https://mail.google.com/`.

```bash
export GMAIL_USE_SERVICE_ACCOUNT=1
export GMAIL_SERVICE_ACCOUNT_JSON=/path/to/sa.json
export GMAIL_DELEGATED_USER=user@yourdomain.com
```

---

## SMCP

Install this repo (or copy) so SMCP’s plugin directory contains **`smcp-gmail`** with **`cli.py`**. Tools are named in `--describe` (prefix **`smcp-gmail__`**).

---

## Commands

| CLI command | Purpose |
|-------------|---------|
| `list-mailboxes` | IMAP LIST |
| `search` | UID SEARCH; `--gmail-raw-query` uses `X-GM-RAW` when supported |
| `fetch-headers` | UID FETCH header fields (peek) |
| `fetch-raw-peek` | UID FETCH `BODY.PEEK[]` (base64, capped) |
| `send-message` | SMTP SSL submission |

```bash
python3 cli.py --describe   # SMCP discovery JSON
python3 cli.py list-mailboxes
```

---

## Testing

```bash
pip install -r requirements-testing.txt
python3 run_tests.py
```

---

## Architecture

See **[docs/IMAP_AGENT_PLUGIN_PLAN.md](docs/IMAP_AGENT_PLUGIN_PLAN.md)**.

## License

AGPL-3.0 (code); docs under LICENSE-DOCS where noted.
