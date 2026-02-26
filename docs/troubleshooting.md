# Troubleshooting

Common issues and how to fix them.

---

## “Credentials file not found”

**Symptom:** CLI or SMCP tool fails with a JSON error like:

```json
{"error": "Credentials file not found: .../credentials.json. Download from Google Cloud Console..."}
```

**Causes and fixes:**

1. **File not in the expected place**  
   By default the plugin looks for `credentials.json` in the **plugin directory** (the folder containing `cli.py`). Put the file there, or set an absolute path:

   ```bash
   export GMAIL_CREDENTIALS_FILE=/path/to/credentials.json
   ```

2. **Wrong working directory**  
   If SMCP (or another process) runs the plugin from a different directory, relative paths may point to the wrong place. Use **absolute paths** for both `GMAIL_CREDENTIALS_FILE` and `GMAIL_TOKEN_FILE` in that environment.

3. **File not downloaded**  
   You must create an OAuth 2.0 Client ID (Desktop app) in Google Cloud Console and download the client secrets JSON. See [Installation](installation.md).

---

## “Access blocked” / “This app isn’t verified”

**Symptom:** During browser sign-in, Google shows “Access blocked” or “This app isn’t verified.”

**Cause:** Your OAuth consent screen is in **Testing** mode and the app is not verified by Google.

**Fixes:**

- For **personal or internal use:** On the warning screen, use **Advanced** → **Go to &lt;your app name&gt; (unsafe)** to continue. Only do this for an app you trust (your own).
- For **production or external users:** Submit the app for verification in Google Cloud Console (OAuth consent screen), or restrict to **Internal** if you use Google Workspace.

---

## Token expired / Invalid credentials

**Symptom:** Commands that used to work start failing with auth or token errors.

**Fixes:**

1. **Delete the token and sign in again:**

   ```bash
   rm token.json
   # or, if you set GMAIL_TOKEN_FILE:
   rm "$GMAIL_TOKEN_FILE"
   ```

   Then run any Gmail command; the browser will open for a new sign-in.

2. **Revoked access**  
   If you or the user revoked access in their Google account (Security → Third-party apps), delete the token file and re-authorize as above.

---

## 403 Forbidden / Gmail API has not been used

**Symptom:** API calls return 403 or a message that the Gmail API has not been used in the project.

**Fixes:**

1. In [Google Cloud Console](https://console.cloud.google.com/), select the correct project.
2. Open **APIs & Services** → **Library**.
3. Search for **Gmail API** and ensure it is **Enabled** for that project.

---

## ModuleNotFoundError: No module named 'google'

**Symptom:** Running `python cli.py list-labels` (or any Gmail command) fails with:

```
ModuleNotFoundError: No module named 'google'
```

**Cause:** The Gmail API dependencies are not installed (or are installed for a different Python).

**Fix:**

```bash
pip install -r requirements.txt
```

If you use a virtual environment, activate it first, then run the command with the same Python that has the packages:

```bash
source venv/bin/activate
pip install -r requirements.txt
python cli.py list-labels
```

---

## SMCP does not list smcp-gmail tools

**Symptom:** After adding the plugin, SMCP’s tool list does not show `smcp-gmail__list-messages`, etc.

**Checks:**

1. **Plugin directory**  
   SMCP must be configured to look in a directory that **contains** a folder named **`smcp-gmail`**, and that folder must contain **`cli.py`**. Check `MCP_PLUGINS_DIR` or the default `plugins/` next to the SMCP server.

2. **Execute permission**  
   Some setups require the CLI to be executable:

   ```bash
   chmod +x /path/to/smcp-gmail/cli.py
   ```

3. **Python path**  
   SMCP runs the plugin with `python cli.py ...` (or `sys.executable`). Ensure that Python can find the `gmail_client` module (same directory as `cli.py`). Running from the plugin directory or having it on `PYTHONPATH` is usually enough.

4. **Describe**  
   From the plugin directory, run:

   ```bash
   python cli.py --describe
   ```

   If this fails, fix the environment (deps, credentials path) first; SMCP discovery uses the same command.

---

## Tests fail with “ModuleNotFoundError: No module named 'google'”

**Symptom:** `pytest tests/unit tests/integration` fails when collecting or running tests that use `gmail_client`.

**Behavior:** Unit tests that depend on the Gmail client use `pytest.importorskip("google.auth")`, so they are **skipped** when the Google packages are not installed. Integration tests run the CLI in a subprocess; without deps the subprocess may exit with an error, which the integration tests accept.

**To run the full suite with coverage (and hit the 80% target):**

```bash
pip install -r requirements-testing.txt
python run_tests.py
```

---

## Send fails / “Recipient address rejected”

**Symptom:** `send-message` returns an error about the recipient or address.

**Checks:**

- **Format:** Use a valid email address for `--to` (and `--cc` / `--bcc` if set).
- **Quotes:** In the shell, quote arguments so that `@` and other characters are not interpreted.
- **Gmail limits:** Respect Gmail sending limits (e.g. 500/day for personal accounts). Large volumes may require a different sending path (e.g. SMTP relay).

---

## Getting more detail

- **CLI:** All errors are printed as JSON with an `"error"` key. The message is intended to be enough to identify the problem (e.g. missing file, API error).
- **SMCP:** Check SMCP’s logs; the server often logs stderr from plugin runs. That may include Python tracebacks if the plugin crashes before printing JSON.
- **Gmail API:** For API-level errors (e.g. 403, 404), see [Gmail API HTTP error codes](https://developers.google.com/gmail/api/reference/responses#standard_error_responses) and your Cloud project’s quotas and enabled APIs.
