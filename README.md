# smcp-gmail

Gmail API plugin for [SMCP](https://github.com/sanctumos/smcp) (Model Context Protocol). Exposes Gmail operations as MCP tools so AI clients can list messages, read, send, and list labels.

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Cloud / Gmail API**
   - Create a [Google Cloud project](https://console.cloud.google.com/) and enable the [Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com).
   - Configure the OAuth consent screen and create an **OAuth 2.0 Client ID** (Desktop app).
   - Download the client secrets and save as `credentials.json` in this plugin directory (or set `GMAIL_CREDENTIALS_FILE`).

3. **First run**
   - Run any command (e.g. `python cli.py list-labels`). The first time you’ll be prompted to sign in in the browser; credentials are stored in `token.json` (or path in `GMAIL_TOKEN_FILE`).

## Use as SMCP plugin

Copy or symlink this directory into SMCP’s plugins directory:

```bash
cp -r /path/to/smcp-gmail /path/to/smcp/plugins/
chmod +x /path/to/smcp/plugins/smcp-gmail/cli.py
```

Or set `MCP_PLUGINS_DIR` to a directory that contains `smcp-gmail` (with `cli.py` inside).

Tools are exposed as:

- `smcp-gmail__list-messages` – list message IDs (optional query, max results, page token)
- `smcp-gmail__get-message` – get one message by ID (metadata or full)
- `smcp-gmail__send-message` – send an email (to, subject, body; optional cc/bcc)
- `smcp-gmail__list-labels` – list Gmail labels

## CLI (standalone)

```bash
# Plugin spec for SMCP discovery
python cli.py --describe

# List labels
python cli.py list-labels

# List messages (optional query)
python cli.py list-messages --query "is:unread" --max-results 5

# Get message
python cli.py get-message --message-id "<id>"

# Send email
python cli.py send-message --to "user@example.com" --subject "Hi" --body "Hello"
```

## Testing

Full test suite (unit, integration, coverage ≥80%) requires Gmail API deps installed:

```bash
# Optional: use a virtual environment
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements-testing.txt
python run_tests.py
# Or: pytest tests/unit tests/integration --cov=cli --cov=gmail_client --cov-fail-under=80 --cov-report=term-missing
```

- **Unit tests**: `tests/unit/` (cli, gmail_client with mocks).
- **Integration tests**: `tests/integration/` (CLI subprocess, `--describe`, error contract).
- **E2E tests**: `tests/e2e/` – skipped unless `GMAIL_E2E=1` and `credentials.json` (or `GMAIL_CREDENTIALS_FILE`) exists. Run with: `pytest -m e2e`.

Without `google-api-python-client` installed, unit tests that mock the Gmail client are skipped; integration and describe tests still run.

## Env (optional)

- `GMAIL_CREDENTIALS_FILE` – path to OAuth client secrets JSON (default: `credentials.json` in plugin dir).
- `GMAIL_TOKEN_FILE` – path to store/load token (default: `token.json` in plugin dir).

## License

Same as SMCP / your project.
