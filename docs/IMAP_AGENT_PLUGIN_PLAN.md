# SMCP Gmail IMAP Agent Plugin — Architecture & Execution Plan

This document is the canonical plan for **agent-safe Gmail access** over **IMAP + SMTP**, replacing the assumption that an MCP/SMCP tool process can run **interactive Desktop OAuth** (`run_local_server`). It covers **personal Gmail (@gmail.com / consumer Google Account)** first, then **Google Workspace (“Google for business”)**.

**Repository deliverable:** `smcp-gmail-imap/` — a second SMCP plugin directory (sibling layout to any existing `smcp-gmail` REST plugin) with its own `cli.py`, tests, and docs. Agents use **runtime secrets only**; humans use **bootstrap** once per identity.

---

## 1. Goals & non-goals

### Goals

- **Headless / agentic:** SMCP tool invocations must **never** open a browser or bind a loopback OAuth server.
- **Personal Gmail first:** OAuth2 **refresh token** minted **out-of-band** (bootstrap CLI), then **XOAUTH2** on IMAP (993) and SMTP submission (465/587).
- **Workspace second:** Support **domain-wide delegated service accounts** impersonating a user mailbox (admin-provisioned), with the same IMAP/SMTP surface where Google allows it.
- **Optional simplicity path:** **App password** (16-char) for IMAP/SMTP **only** where Google account policy still permits it — documented, not the strategic default.
- **Gmail-native search on IMAP:** Use **`X-GM-RAW`** when `X-GM-EXT-1` is advertised (Gmail search syntax in `UID SEARCH`).
- **Safe defaults for agents:** Prefer **`BODY.PEEK[]`** and explicit **mark-read** tools/commands so bulk fetch does not silently flip `\Seen`.

### Non-goals (initial releases)

- **Gmail REST API** parity (drafts, watch/Pub/Sub, granular metadata-only REST) — out of scope for this plugin; link to legacy REST plugin if needed.
- **Full calendar / Drive** — not this plugin.
- **GUI or browser-in-tool** — explicitly rejected.

---

## 2. Protocol & Google facts (frozen assumptions)

| Topic | Decision |
|--------|-----------|
| IMAP | `imap.gmail.com:993`, implicit TLS |
| SMTP | `smtp.gmail.com`, `465` (SSL) preferred; `587` + STARTTLS acceptable |
| Consumer OAuth scope for mail protocols | `https://mail.google.com/` (covers IMAP + SMTP via XOAUTH2 per Google) |
| Gmail extensions | Require `CAPABILITY` check for `X-GM-EXT-1`; use `X-GM-RAW`, `X-GM-THRID`, `X-GM-MSGID`, `X-GM-LABELS` when present |
| Folders vs labels | Treat IMAP mailboxes as labels; document `[Gmail]/All Mail`, `[Gmail]/Sent Mail`, etc. |
| Session | Expect **short access token lifetime** and **IMAP server idle limits**; **connect per batch** or short-lived pool — no “one socket forever” |

---

## 3. Security model: bootstrap vs runtime

### Bootstrap lane (human or CI secret generation)

- **Command:** `python cli.py bootstrap-oauth` (device authorization grant, RFC 8628) **or** future: paste authorization code.
- **Output:** Writes **`gmail_imap_token.json`** (or path from `GMAIL_IMAP_TOKEN_FILE`) containing refresh token and client metadata in **Google `Credentials.to_json()`**-compatible shape.
- **May** print URL and user code; **may** require human on a phone or laptop **once**.
- **Never** imported by default when SMCP runs `list-mailboxes` etc.

### Runtime lane (agents / SMCP)

- Loads **token file** + **client secret JSON path** (or inline client id/secret envs).
- **Refreshes access token** with `google.auth.transport.requests.Request` when expired/near expiry.
- Builds **XOAUTH2** initial client response (Base64 of `user=…\x01auth=Bearer …\x01\x01`).
- **No** `input()` except in explicit bootstrap subcommand.

### Secrets on disk

- **gitignore:** `**/gmail_imap_token.json`, `**/token.json` under plugin dir, `credentials.json` (client secrets) — already partially covered at repo root; extend for `smcp-gmail-imap/`.
- **chmod:** document `600` for token files on Unix.

---

## 4. Personal Gmail (Phase A — ship first)

### Authentication modes

1. **`oauth_refresh` (default)**  
   - Env: `GMAIL_ADDRESS`, `GMAIL_IMAP_TOKEN_FILE` (refresh token JSON), `GMAIL_OAUTH_CLIENT_SECRETS` (path to Desktop client `credentials.json`) **or** `GMAIL_OAUTH_CLIENT_ID` + `GMAIL_OAUTH_CLIENT_SECRET`.  
   - Runtime refreshes access token; IMAP/SMTP use XOAUTH2.

2. **`app_password` (optional)**  
   - Env: `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`.  
   - IMAP/SMTP: plain `LOGIN` / `AUTH PLAIN` as supported by `imaplib`/`smtplib`.  
   - Document: requires 2SV + app passwords enabled; blocked for Advanced Protection, etc.

### SMCP tool / CLI command surface (MVP)

| Command | Purpose |
|---------|---------|
| `list-mailboxes` | `LIST` + RFC6154 special-use; return name + `\HasNoChildren` etc. |
| `search` | `SELECT` folder (default `INBOX`), `UID SEARCH` + optional `X-GM-RAW` query, cap max UIDs |
| `fetch` | `UID FETCH` with `BODY.PEEK[]` or `BODY.PEEK[HEADER]`, size cap, optional max bytes |
| `send-message` | SMTP submit plain text (attachments = later) |
| `bootstrap-oauth` | Device flow; writes token file |

### Limits & safety knobs (env)

- `GMAIL_IMAP_TIMEOUT` (seconds)
- `GMAIL_FETCH_MAX_BYTES` (per message body)
- `GMAIL_SEARCH_MAX_UIDS` (max IDs returned)
- `GMAIL_SMTP_TIMEOUT`

---

## 5. Google Workspace / “Google for business” (Phase B)

Two distinct deployments — document both; implement **B1** before **B2** unless customer only needs B1.

### B1 — Per-user OAuth (same as consumer)

- Each Workspace user has a **refresh token** (bootstrap per mailbox).  
- **Admin policies** may restrict IMAP or “less secure” paths; **XOAUTH2** is the supported approach.  
- **No code fork** beyond docs (“Workspace: ensure IMAP enabled for users”).

### B2 — Service account + domain-wide delegation (DWD)

- **When:** shared automation, delegated access without per-user interactive consent, admin owns trust boundary.  
- **Requires:** Workspace admin configures DWD for the service client id with scope **`https://mail.google.com/`** (or narrower if Google allows for IMAP — follow admin doc).  
- **Runtime:** `google.oauth2.service_account.Credentials.from_service_account_file(...).with_subject(user@domain.com)` → access token → **same XOAUTH2** string for IMAP/SMTP as that user.  
- **Env:** `GMAIL_USE_SERVICE_ACCOUNT=1`, `GMAIL_SERVICE_ACCOUNT_JSON`, `GMAIL_DELEGATED_USER` (email to impersonate).  
- **Caveats:** DWD is powerful; rotation, audit, and least-scope are admin responsibilities. Some accounts may still block IMAP at the org level.

### B3 — (Future) `gmail.imap_admin` and similar

- Reserved for **rare admin tooling** — not required for normal “read my mailbox as me” agents.  
- Only if a customer explicitly needs behavior outside normal user IMAP visibility.

---

## 6. Implementation map (files)

```
smcp-gmail-imap/
  __init__.py
  cli.py                 # argparse: --describe, subcommands
  auth_config.py         # resolve env → AuthSettings dataclass
  oauth_refresh.py      # refresh access token from user OAuth token file
  xoauth2.py             # build XOAUTH2 blob (base64)
  imap_ops.py            # list_mailboxes, search, fetch
  smtp_ops.py            # send_message
  bootstrap_device.py    # RFC8628 device authorization against Google
  workspace_auth.py      # service account + with_subject() path
  requirements.txt       # imaplib/stdlib + google-auth + requests
tests/
  unit/
    test_xoauth2.py
    test_auth_config.py
    test_imap_ops_mock.py
    test_bootstrap_device_mock.py
  integration/
    test_cli_describe.py
```

**Root repo changes**

- `docs/IMAP_AGENT_PLUGIN_PLAN.md` (this file)
- `README.md` section: “Use `smcp-gmail-imap` for agents; REST plugin is legacy desktop-OAuth shaped”
- `.gitignore` entries for `smcp-gmail-imap/gmail_imap_token.json`, etc.

---

## 7. Testing strategy

- **Unit:** XOAUTH2 string format; auth config resolution; IMAP command assembly with **mocked** `imaplib.IMAP4_SSL` (patch `imaplib.IMAP4_SSL` in tests).
- **Integration:** `cli.py --describe` subprocess (no secrets).
- **Live / optional:** `GMAIL_IMAP_LIVE=1` pytest marker — skipped in CI; requires real token file on developer machine.

---

## 8. Rollout & deprecation narrative

- **Do not delete** REST `smcp-gmail` in the same release as IMAP MVP; **mark REST plugin** as **legacy** for agent deployments in README.
- **SMCP operators:** add **`smcp-gmail-imap`** as a separate plugin directory in `MCP_PLUGINS_DIR`; tools are prefixed `smcp-gmail-imap__…` from `--describe`.

---

## 9. Execution checklist (Otto)

- [x] Author this plan (`docs/IMAP_AGENT_PLUGIN_PLAN.md`).
- [x] Implement `smcp-gmail-imap` package (Phases A: auth, imap, smtp, bootstrap, cli).
- [x] Implement Phase B2 Workspace service-account path (`workspace_auth.py` + `GMAIL_USE_SERVICE_ACCOUNT`).
- [x] Unit + integration tests; `smcp-gmail-imap/run_tests.py` + root `tests/integration/test_smcp_gmail_imap_describe.py`.
- [x] README + CHANGELOG; gitignore; push `sanctumos/smcp-gmail`.
- [x] Mirror tree under `projects/sanctum/smcp-gmail` (sync copy with sanctumos).

---

## 10. Open questions (answer as you deploy)

- **OAuth client type for device flow:** Google Cloud “Desktop” vs “TV and limited input” — if device code endpoint rejects client, create a **TV** OAuth client for bootstrap only (documented in troubleshooting).
- **Verification:** `https://mail.google.com/` may trigger **OAuth verification** for public apps — internal / testing users mitigate for personal use.

---

*Last updated: 2026-04-20 — Otto execution against this plan.*
