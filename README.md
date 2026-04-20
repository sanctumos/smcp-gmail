# smcp-gmail

**Gmail API plugin for [SMCP](https://github.com/sanctumos/smcp)** (Model Context Protocol). Exposes Gmail as MCP tools so AI clients can list messages, read, send, and manage labels—without writing Gmail API code.

**For headless / agent-only deployments**, use the sibling plugin **`smcp-gmail-imap/`** (IMAP + SMTP, XOAUTH2 from **pre-provisioned** token JSON, optional app password, optional Workspace service-account delegation — **no OAuth or browser flows in the plugin**). See [`docs/IMAP_AGENT_PLUGIN_PLAN.md`](docs/IMAP_AGENT_PLUGIN_PLAN.md) and `smcp-gmail-imap/README.md`. The original REST + desktop-OAuth plugin remains for interactive / API workflows.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPLv3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

---

## Table of contents

- [Features](#features)
- [Quick start](#quick-start)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [As an SMCP plugin](#as-an-smcp-plugin)
  - [Standalone CLI](#standalone-cli)
- [Commands reference](#commands-reference)
- [Testing](#testing)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **List messages** – Search and paginate with Gmail query syntax (`is:unread`, `from:user@example.com`, etc.).
- **Get message** – Fetch a single message by ID (metadata or full body, including plain/html parts).
- **Send message** – Send plain-text email with optional CC/BCC.
- **List labels** – List all Gmail labels (INBOX, SENT, custom labels).
- **SMCP-native** – Exposes `--describe` for tool discovery; tools appear as `smcp-gmail__list-messages`, etc.
- **OAuth2** – Uses Google’s desktop OAuth flow; credentials stored in `token.json` after first sign-in.

---

## Quick start

```bash
# 1. Clone and install
git clone https://github.com/sanctumos/smcp-gmail.git
cd smcp-gmail
pip install -r requirements.txt

# 2. Add credentials
#    Download OAuth client secrets from Google Cloud Console → APIs & Services → Credentials
#    Save as credentials.json in this directory.

# 3. First run (opens browser to sign in)
python cli.py list-labels

# 4. Use as SMCP plugin: copy into your SMCP plugins directory
cp -r . /path/to/smcp/plugins/smcp-gmail
```

---

## Requirements

- **Python** 3.8 or higher  
- **Google Cloud project** with Gmail API enabled  
- **OAuth 2.0 Client ID** (Desktop application) – client secrets downloaded as `credentials.json`

---

## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

Optional: use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Enable Gmail API and create credentials

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Enable the **Gmail API**: [Enable Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com).
4. Configure the **OAuth consent screen** (e.g. External or Internal, add scopes if needed).
5. Create **Credentials** → **OAuth 2.0 Client ID** → Application type: **Desktop app**.
6. Download the JSON and save it as **`credentials.json`** in the smcp-gmail directory (or set `GMAIL_CREDENTIALS_FILE` to its path).

### 3. First authorization

Run any command that uses Gmail (e.g. `python cli.py list-labels`). The first time, a browser window opens for you to sign in and grant access. Tokens are stored in **`token.json`** (or the path in `GMAIL_TOKEN_FILE`).

See [docs/installation.md](docs/installation.md) for step-by-step and screenshots-style guidance.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GMAIL_CREDENTIALS_FILE` | `credentials.json` (in plugin dir) | Path to OAuth client secrets JSON. |
| `GMAIL_TOKEN_FILE`     | `token.json` (in plugin dir)       | Path to store/load the OAuth token. |

All paths are relative to the current working directory unless absolute. See [docs/configuration.md](docs/configuration.md) for details.

---

## Usage

### As an SMCP plugin

1. Copy or symlink this directory into SMCP’s plugins directory:

   ```bash
   cp -r /path/to/smcp-gmail /path/to/smcp/plugins/
   chmod +x /path/to/smcp/plugins/smcp-gmail/cli.py
   ```

   Or set **`MCP_PLUGINS_DIR`** to a directory that contains a folder named `smcp-gmail` (with `cli.py` inside).

2. Start SMCP. The plugin is discovered automatically; tools are registered with the `smcp-gmail__` prefix.

3. **MCP tool names** (used by AI clients):

   | Tool name | Description |
   |-----------|-------------|
   | `smcp-gmail__list-messages` | List message IDs (optional query, max results, page token). |
   | `smcp-gmail__get-message`   | Get one message by ID (metadata or full body). |
   | `smcp-gmail__send-message`  | Send an email (to, subject, body; optional cc/bcc). |
   | `smcp-gmail__list-labels`   | List Gmail labels. |

### Standalone CLI

```bash
# Plugin spec (JSON) for SMCP discovery
python cli.py --describe

# List labels
python cli.py list-labels

# List messages with Gmail search
python cli.py list-messages --query "is:unread" --max-results 10

# Get a message (metadata only)
python cli.py get-message --message-id "<message-id>"

# Get full body (plain + HTML parts)
python cli.py get-message --message-id "<id>" --format full

# Send email
python cli.py send-message --to "user@example.com" --subject "Hello" --body "Hi from smcp-gmail"
```

All commands print a single JSON object to stdout (or an error object with an `"error"` key). Exit code is 0 on success, 1 on failure.

---

## Commands reference

| Command | Required arguments | Optional arguments | Description |
|---------|--------------------|--------------------|-------------|
| `list-messages` | — | `--user-id`, `--query`, `--max-results`, `--page-token` | List messages; supports Gmail search syntax. |
| `get-message`   | `--message-id` | `--user-id`, `--format` (minimal \| full \| metadata \| raw) | Fetch one message. |
| `send-message`  | `--to`, `--subject`, `--body` | `--user-id`, `--cc`, `--bcc` | Send plain-text email. |
| `list-labels`  | — | `--user-id` | List all labels. |

Example Gmail queries for `--query`: `is:unread`, `from:alice@example.com`, `subject:meeting`, `after:2024/01/01`, `has:attachment`.

Full details: [docs/usage.md](docs/usage.md).

---

## Testing

```bash
pip install -r requirements-testing.txt
python run_tests.py
```

- **Unit tests** – `tests/unit/` (CLI and Gmail client with mocks).
- **Integration tests** – `tests/integration/` (CLI subprocess, `--describe`, error contract).
- **E2E tests** – `tests/e2e/`; run only when credentials are configured:  
  `GMAIL_E2E=1 pytest -m e2e`.

Coverage target: **80%** (enforced by `run_tests.py` when Gmail API deps are installed). Without Gmail deps, some unit tests are skipped; integration and describe tests still run.

See [docs/development.md](docs/development.md) for more.

---

## Documentation

| Document | Contents |
|----------|----------|
| [docs/README.md](docs/README.md) | Index of all documentation. |
| [docs/installation.md](docs/installation.md) | Step-by-step installation and Google Cloud setup. |
| [docs/usage.md](docs/usage.md) | CLI and MCP usage, all commands and parameters. |
| [docs/configuration.md](docs/configuration.md) | Environment variables, credentials, and token paths. |
| [docs/development.md](docs/development.md) | Testing, coverage, and contributing. |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common errors and fixes. |

---

## Troubleshooting

- **"Credentials file not found"** – Ensure `credentials.json` exists (or `GMAIL_CREDENTIALS_FILE` is set) in the plugin directory or current working directory.
- **"Access blocked" / consent screen** – Configure the OAuth consent screen and add the Gmail scopes your app uses.
- **Token expired** – Delete `token.json` and run again to re-authorize.
- **403 / Permission denied** – Check that the Gmail API is enabled for your Google Cloud project.

More: [docs/troubleshooting.md](docs/troubleshooting.md).

---

## License

This project uses dual licensing:

- **Code** (Python source, scripts, config used to run the program): **[GNU Affero General Public License v3.0 (AGPL-3.0)](https://www.gnu.org/licenses/agpl-3.0)** — see [LICENSE](LICENSE). You may use, modify, and distribute the code under the terms of the AGPLv3; if you run a modified version as a network server, you must offer the corresponding source to users.
- **Documentation and other non-code material** (README, docs/, and any other prose or media that is not executable source): **[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/)** — see [LICENSE-DOCS](LICENSE-DOCS). You may share and adapt under attribution and share-alike terms.
