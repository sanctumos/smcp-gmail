# Configuration

smcp-gmail is configured via environment variables and two files: **credentials** (OAuth client secrets) and **token** (stored access/refresh token).

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| **GMAIL_CREDENTIALS_FILE** | `credentials.json` in the plugin directory | Path to the OAuth 2.0 client secrets JSON file (downloaded from Google Cloud Console). |
| **GMAIL_TOKEN_FILE** | `token.json` in the plugin directory | Path where the plugin stores and loads the OAuth token after the first sign-in. |

Paths can be absolute or relative to the **current working directory** when the CLI runs. The “plugin directory” is the folder containing `cli.py` and `gmail_client.py`.

### Examples

Use a shared credentials file:

```bash
export GMAIL_CREDENTIALS_FILE=/etc/smcp-gmail/credentials.json
python cli.py list-labels
```

Store the token in a custom location:

```bash
export GMAIL_TOKEN_FILE=~/.config/smcp-gmail/token.json
python cli.py list-labels
```

Both:

```bash
export GMAIL_CREDENTIALS_FILE=/opt/creds/gmail.json
export GMAIL_TOKEN_FILE=/var/lib/smcp-gmail/token.json
python cli.py list-labels
```

---

## Credentials file (`credentials.json`)

- **What it is:** OAuth 2.0 “client secrets” for a **Desktop application** client ID from Google Cloud Console.
- **How to get it:** [Installation](installation.md) describes creating the client ID and downloading the JSON.
- **Format:** JSON with a structure like `{"installed": {"client_id": "...", "client_secret": "...", ...}}` (or `"web"` for web clients; desktop is typically `"installed"`).
- **Security:** Do not commit this file. Restrict read access to the process that runs the plugin (e.g. the SMCP server or your user).

---

## Token file (`token.json`)

- **What it is:** Stored OAuth access and refresh token created after the first successful browser sign-in.
- **When it’s created:** The first time you run a command that calls the Gmail API (e.g. `list-labels`), the plugin opens a browser for sign-in and then writes the token to this file.
- **When it’s used:** On later runs, the plugin loads the token from this file and refreshes it as needed; no browser is opened unless the token is invalid or revoked.
- **Security:** Treat it like a password. Do not commit it. Restrict read/write to the process that runs the plugin.

To force re-authorization (e.g. after changing scopes or switching accounts), delete the token file and run the CLI again.

---

## Scopes

The plugin requests these Gmail scopes:

- `https://www.googleapis.com/auth/gmail.readonly` – Read messages and metadata.
- `https://www.googleapis.com/auth/gmail.send` – Send mail.
- `https://www.googleapis.com/auth/gmail.modify` – Modify labels and state (e.g. mark read).

They are defined in `gmail_client.py` and cannot be overridden via environment variables. If you need different scopes, you would have to change the code and re-authorize (delete `token.json` and sign in again).

---

## Running under SMCP

When SMCP runs the plugin, the **working directory** is usually the SMCP process’s cwd, not necessarily the plugin directory. So:

- If you rely on the default paths, either run SMCP from the plugin directory or use **absolute paths** in `GMAIL_CREDENTIALS_FILE` and `GMAIL_TOKEN_FILE`.
- Alternatively, place `credentials.json` and `token.json` in the plugin directory and set the env vars to those absolute paths so they work regardless of cwd.

Example for a systemd service running SMCP:

```ini
[Service]
Environment="GMAIL_CREDENTIALS_FILE=/opt/smcp-gmail/credentials.json"
Environment="GMAIL_TOKEN_FILE=/var/lib/smcp-gmail/token.json"
```

Then ensure `/opt/smcp-gmail/` (or your plugin path) contains `credentials.json` and that the service has done at least one interactive sign-in so `token.json` exists at the given path (or copy an existing token there with correct permissions).
