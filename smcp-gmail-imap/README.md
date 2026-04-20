# smcp-gmail-imap

Gmail over **IMAP + SMTP** for **SMCP** and other MCP hosts, designed for **agents and headless servers**: runtime uses a **refresh token** (or **Workspace service-account delegation**), not an interactive browser inside tool calls.

## Personal Gmail (XOAUTH2)

1. Install deps: `pip install -r requirements.txt` (from this directory).
2. **Bootstrap once** (can run on your laptop; prints URL + code):

   ```bash
   export GMAIL_ADDRESS='you@gmail.com'
   python3 cli.py bootstrap-oauth --client-secrets /path/to/credentials.json
   ```

   Writes `gmail_imap_token.json` here (override with `--out-token`). Google Cloud OAuth client must allow **device authorization** (Desktop client usually works; if not, create a **TV and limited input** client for bootstrap only).

3. **Agent runtime** env:

   - `GMAIL_ADDRESS` — mailbox for `From:` / SASL user (same as bootstrap).
   - `GMAIL_IMAP_TOKEN_FILE` — path to `gmail_imap_token.json` if not in this directory.
   - If the token file lacks `client_id` / `client_secret`, set `GMAIL_OAUTH_CLIENT_SECRETS` or the individual env vars.

4. SMCP: point `MCP_PLUGINS_DIR` at a parent of this folder named `smcp-gmail-imap` (or symlink). Tools are prefixed `smcp-gmail-imap__` per `--describe`.

## App password (optional)

If your account supports it:

```bash
export GMAIL_ADDRESS='you@gmail.com'
export GMAIL_APP_PASSWORD='xxxx xxxx xxxx xxxx'
```

## Google Workspace (service account + DWD)

Admin must enable **domain-wide delegation** for your service account client and authorize scope `https://mail.google.com/`.

```bash
export GMAIL_USE_SERVICE_ACCOUNT=1
export GMAIL_SERVICE_ACCOUNT_JSON=/path/to/sa.json
export GMAIL_DELEGATED_USER=user@yourdomain.com
# GMAIL_ADDRESS optional; defaults to delegated user
```

## Commands

| Command | Role |
|--------|------|
| `list-mailboxes` | IMAP LIST |
| `search` | UID SEARCH; `--gmail-raw-query` uses `X-GM-RAW` when server supports it |
| `fetch-headers` | UID FETCH selective headers (peek) |
| `fetch-raw-peek` | UID FETCH `BODY.PEEK[]` (base64, size-capped) |
| `send-message` | SMTP SSL submission |
| `bootstrap-oauth` | Device OAuth — **not** for automated tool loops |

## Tests

```bash
python3 run_tests.py
```

## Canonical plan

See repository [`docs/IMAP_AGENT_PLUGIN_PLAN.md`](../docs/IMAP_AGENT_PLUGIN_PLAN.md).
