# Installation

This guide walks through installing smcp-gmail and configuring Google Cloud credentials.

## Prerequisites

- **Python 3.8+** – Check with `python3 --version`.
- **pip** – Usually included with Python; upgrade with `python3 -m pip install -U pip`.
- **Google account** with Gmail enabled.

---

## Step 1: Get the plugin

Clone or download the repository:

```bash
git clone https://github.com/sanctumos/smcp-gmail.git
cd smcp-gmail
```

Or add it as a submodule inside your SMCP plugins directory:

```bash
mkdir -p /path/to/smcp/plugins
cd /path/to/smcp/plugins
git clone https://github.com/sanctumos/smcp-gmail.git
```

---

## Step 2: Install Python dependencies

From the `smcp-gmail` directory:

```bash
pip install -r requirements.txt
```

Or use a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Installed packages include:

- `google-api-python-client` – Gmail API client
- `google-auth-httplib2` – HTTP transport for auth
- `google-auth-oauthlib` – OAuth2 flow (browser sign-in)

---

## Step 3: Create a Google Cloud project

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one (top bar → project dropdown → **New Project**).
3. Note the project name/ID; you’ll use it for credentials.

---

## Step 4: Enable the Gmail API

1. In the Cloud Console, open **APIs & Services** → **Library** (or go to [API Library](https://console.cloud.google.com/apis/library)).
2. Search for **Gmail API**.
3. Open it and click **Enable**.

---

## Step 5: Configure the OAuth consent screen

1. Go to **APIs & Services** → **OAuth consent screen**.
2. Choose **External** (for any Google account) or **Internal** (Google Workspace only).
3. Fill in:
   - **App name** – e.g. “smcp-gmail”
   - **User support email** – your email
   - **Developer contact** – your email
4. Under **Scopes**, add (if not already present):
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.modify`
5. Save and continue. For **Test users** (External), add the Gmail accounts that will sign in during development.

---

## Step 6: Create OAuth 2.0 credentials

1. Go to **APIs & Services** → **Credentials**.
2. Click **Create credentials** → **OAuth client ID**.
3. **Application type**: choose **Desktop app**.
4. **Name**: e.g. “smcp-gmail desktop”.
5. Click **Create**.
6. In the dialog, click **Download JSON** and save the file.

---

## Step 7: Place credentials in the plugin directory

1. Rename or copy the downloaded file to **`credentials.json`**.
2. Put it in the **smcp-gmail** directory (same folder as `cli.py`).

   ```bash
   mv ~/Downloads/client_secret_*.json /path/to/smcp-gmail/credentials.json
   ```

   Or set the path via environment:

   ```bash
   export GMAIL_CREDENTIALS_FILE=/path/to/your/credentials.json
   ```

**Security:** Do not commit `credentials.json` or `token.json` to version control. They are listed in `.gitignore`.

---

## Step 8: First run and browser sign-in

Run any Gmail command, for example:

```bash
python cli.py list-labels
```

The first time:

1. A browser window opens to Google’s sign-in page.
2. Sign in with the Gmail account you want the plugin to use.
3. Approve the requested scopes (read, send, modify mail).
4. The page may say “The app isn’t verified”; for personal/desktop use you can choose **Advanced** → **Go to smcp-gmail (unsafe)** to continue.
5. After success, the browser can be closed.

The plugin then writes **`token.json`** in the plugin directory (or the path in `GMAIL_TOKEN_FILE`). Later runs reuse this token until it expires or is removed.

---

## Verifying the installation

```bash
# Should print JSON with plugin name and commands
python cli.py --describe

# Should print JSON with a "labels" array
python cli.py list-labels
```

If both succeed, installation is complete. Next: [Usage](usage.md) and [Configuration](configuration.md).
