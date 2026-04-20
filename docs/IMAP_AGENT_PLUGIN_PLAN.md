# SMCP Gmail IMAP Agent Plugin — Architecture & Execution Plan

This document is the canonical plan for **agent-safe Gmail access** over **IMAP + SMTP**, replacing the assumption that an MCP/SMCP tool process can run **interactive Desktop OAuth** (`run_local_server`). It covers **personal Gmail (@gmail.com / consumer Google Account)** first, then **Google Workspace (“Google for business”)**.

**Repository deliverable:** the **`smcp-gmail`** repo root (`cli.py` + IMAP/SMTP modules). **This codebase only implements the runtime lane** — it **never** runs OAuth authorization, device codes, loopback redirects, or any flow that implies a browser or interactive consent. **All token minting happens outside this repo** (your laptop script, secret manager, CI job, admin tooling — not shipped here). The legacy Gmail **REST** + desktop-OAuth implementation was **removed in v3.0.0**.

---

## 1. Goals & non-goals

### Goals

- **Headless / agentic:** SMCP tool invocations must **never** open a browser, print a verification URL for this process, start a local HTTP OAuth callback, or run RFC 8628 device authorization **inside this plugin**.
- **Personal Gmail first:** OAuth2 **refresh token** (and client id/secret) exist as **pre-provisioned artifacts**; runtime uses **XOAUTH2** on IMAP (993) and SMTP submission (465/587) with `google.auth` token refresh only.
- **Workspace second:** Support **domain-wide delegated service accounts** impersonating a user mailbox (admin-provisioned), with the same IMAP/SMTP surface where Google allows it.
- **Optional simplicity path:** **App password** (16-char) for IMAP/SMTP **only** where Google account policy still permits it — documented, not the strategic default.
- **Gmail-native search on IMAP:** Use **`X-GM-RAW`** when `X-GM-EXT-1` is advertised (Gmail search syntax in `UID SEARCH`).
- **Safe defaults for agents:** Prefer **`BODY.PEEK[]`** and explicit **mark-read** tools/commands so bulk fetch does not silently flip `\Seen`.

### Non-goals (initial releases)

- **Gmail REST API** parity (drafts, watch/Pub/Sub, granular metadata-only REST) — out of scope for this plugin; link to legacy REST plugin if needed.
- **Full calendar / Drive** — not this plugin.
- **Any OAuth consent, device, or browser UX inside this repository** — explicitly rejected (including no `bootstrap-oauth` subcommand).

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

## 3. Security model: provisioning (out of band) vs runtime (this plugin)

### Provisioning lane — **not implemented in this repo**

- Operators obtain **Google authorized-user JSON** (`Credentials.to_json()` shape: `refresh_token`, `token_uri`, `client_id`, `client_secret`, scopes) using **their own** one-off tooling, or they use **app passwords**, or Workspace admins configure **service account + DWD**.
- That work may involve browsers, phones, or admin consoles — **elsewhere**. None of it is a subcommand of this repo’s `cli.py`.

### Runtime lane — **this plugin only**

- Loads **token file** and/or **client metadata** from env paths.
- **Refreshes access token** with `google.auth.transport.requests.Request` when expired (no human).
- Builds **XOAUTH2** for IMAP/SMTP.
- **No** `input()`, no `webbrowser`, no `InstalledAppFlow`, no device code endpoint calls.

### Secrets on disk

- **gitignore:** `gmail_imap_token.json`, `token.json`, `credentials.json` at repo root as needed.
- **chmod:** document `600` for token files on Unix.

---

## 4. Personal Gmail (Phase A — ship first)

### Authentication modes

1. **`oauth_refresh` (default)**  
   - Env: `GMAIL_ADDRESS`, `GMAIL_IMAP_TOKEN_FILE` (authorized-user JSON), optional `GMAIL_OAUTH_CLIENT_SECRETS` / `GMAIL_OAUTH_CLIENT_ID` + `GMAIL_OAUTH_CLIENT_SECRET` if not embedded in the token file.  
   - Runtime refreshes access token; IMAP/SMTP use XOAUTH2.

2. **`app_password` (optional)**  
   - Env: `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`.  
   - IMAP/SMTP: `LOGIN` / plain auth as supported by `imaplib`/`smtplib`.  
   - Document: requires 2SV + app passwords enabled; blocked for Advanced Protection, etc.

### SMCP tool / CLI command surface (MVP)

| Command | Purpose |
|---------|---------|
| `list-mailboxes` | `LIST` + RFC6154 special-use; return name + flags |
| `search` | `SELECT` folder (default `INBOX`), `UID SEARCH` + optional `X-GM-RAW` query, cap max UIDs |
| `fetch-headers` | `UID FETCH` selective headers (`BODY.PEEK`) |
| `fetch-raw-peek` | `UID FETCH` `BODY.PEEK[]`, size-capped, base64 in JSON |
| `send-message` | SMTP submit plain text (attachments = later) |

### Limits & safety knobs (env)

- `GMAIL_IMAP_TIMEOUT` (seconds)
- `GMAIL_FETCH_MAX_BYTES` (per message body)
- `GMAIL_SEARCH_MAX_UIDS` (max IDs returned)
- `GMAIL_SMTP_TIMEOUT`

---

## 5. Google Workspace / “Google for business” (Phase B)

Two distinct deployments — document both; implement **B1** before **B2** unless customer only needs B1.

### B1 — Per-user OAuth (same as consumer)

- Each Workspace user has a **refresh token** stored in JSON **provisioned outside this plugin** for that mailbox.  
- **Admin policies** may restrict IMAP; **XOAUTH2** is the supported approach.  
- **No code fork** beyond docs (“Workspace: ensure IMAP enabled for users”).

### B2 — Service account + domain-wide delegation (DWD)

- **When:** shared automation, delegated access without per-user refresh tokens, admin owns trust boundary.  
- **Requires:** Workspace admin configures DWD for the service client id with scope **`https://mail.google.com/`** (follow admin doc).  
- **Runtime:** `google.oauth2.service_account.Credentials.from_service_account_file(...).with_subject(user@domain.com)` → access token → **same XOAUTH2** string for IMAP/SMTP as that user.  
- **Env:** `GMAIL_USE_SERVICE_ACCOUNT=1`, `GMAIL_SERVICE_ACCOUNT_JSON`, `GMAIL_DELEGATED_USER` (email to impersonate).  
- **Caveats:** DWD is powerful; rotation, audit, and least-scope are admin responsibilities. Some accounts may still block IMAP at the org level.

### B3 — (Future) `gmail.imap_admin` and similar

- Reserved for **rare admin tooling** — not required for normal “read my mailbox as me” agents.  
- Only if a customer explicitly needs behavior outside normal user IMAP visibility.

---

## 6. Implementation map (files)

```
smcp-gmail/   (repo root)
  cli.py
  auth_config.py
  oauth_refresh.py
  xoauth2.py
  token_provider.py
  imap_ops.py
  smtp_ops.py
  workspace_auth.py
  requirements.txt
tests/…
```

**Docs**

- `docs/IMAP_AGENT_PLUGIN_PLAN.md` (this file)
- `.gitignore` includes `gmail_imap_token.json`, `credentials.json`, etc.

---

## 7. Testing strategy

- **Unit:** XOAUTH2 string format; auth config resolution; IMAP command assembly with **mocked** `imaplib.IMAP4_SSL` (future).
- **Integration:** `cli.py --describe` subprocess (no secrets).
- **Live / optional:** `GMAIL_IMAP_LIVE=1` pytest marker — skipped in CI; requires real token file on developer machine.

---

## 8. Rollout & deprecation narrative

- **v3.0.0:** REST + `gmail_client.py` + desktop OAuth **removed** from this repository. Operators use **this** `smcp-gmail` tree only (IMAP/SMTP). Tool names in `--describe` are **`smcp-gmail__list-mailboxes`**, etc. (same prefix, different commands than v1 REST).

---

## 9. Execution checklist (Otto)

- [x] Author this plan (`docs/IMAP_AGENT_PLUGIN_PLAN.md`).
- [x] IMAP implementation at repo root (auth, imap, smtp, cli) — **no in-repo OAuth / device / browser flows**.
- [x] Workspace service-account path (`workspace_auth.py` + `GMAIL_USE_SERVICE_ACCOUNT`).
- [x] Unit + integration tests; root `run_tests.py`.
- [x] README + CHANGELOG; gitignore; push `sanctumos/smcp-gmail`.
- [x] **v3.0.0:** Removed REST `gmail_client.py` and `smcp-gmail-imap/` subdirectory; single plugin tree.

---

## 10. Open questions (answer as you deploy)

- **Where to mint refresh tokens:** Your choice entirely outside this repo (custom script, internal admin app, etc.). This plugin only documents the **JSON shape** and env vars.
- **Verification:** `https://mail.google.com/` may trigger **OAuth verification** for public apps — internal / testing users mitigate for personal use.

---

*Last updated: 2026-04-20 — plan revised: zero OAuth flows in-plugin.*
