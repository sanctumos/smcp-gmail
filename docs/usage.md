# Usage

This document describes how to use smcp-gmail as an SMCP plugin and from the command line.

## As an SMCP plugin

### Installing the plugin into SMCP

1. Copy or symlink the smcp-gmail directory into SMCP’s plugins directory:

   ```bash
   cp -r /path/to/smcp-gmail /path/to/smcp/plugins/smcp-gmail
   chmod +x /path/to/smcp/plugins/smcp-gmail/cli.py
   ```

2. Or set **`MCP_PLUGINS_DIR`** so it points to a directory that contains a folder named `smcp-gmail` (with `cli.py` inside).

3. Start SMCP. The server discovers plugins by scanning the plugins directory; each subdirectory with a `cli.py` is a plugin.

### MCP tool names

SMCP registers one tool per plugin command. Tool names use the pattern **`plugin__command`** (double underscore):

| MCP tool name | Command | Description |
|---------------|---------|-------------|
| `smcp-gmail__list-messages` | `list-messages` | List message IDs with optional search and pagination. |
| `smcp-gmail__get-message`   | `get-message`   | Get a single message by ID. |
| `smcp-gmail__send-message`  | `send-message`  | Send an email. |
| `smcp-gmail__list-labels`   | `list-labels`   | List Gmail labels. |

AI clients call these tools by name and pass the parameters as a JSON object. Parameter names use underscores (e.g. `message_id`, `max_results`); the CLI accepts the same names with dashes (e.g. `--message-id`, `--max-results`).

### Plugin discovery (`--describe`)

SMCP can call `cli.py --describe` to get a JSON spec of the plugin (name, version, commands, and parameters). That spec is used to register tools with the correct schema. You can run it manually:

```bash
python cli.py --describe
```

---

## Standalone CLI

All commands are invoked as:

```bash
python cli.py <command> [options]
```

Output is a single JSON object on stdout. On failure, the object includes an `"error"` key and the process exits with code 1.

---

## Commands

### `list-messages`

List message IDs (and thread IDs) matching an optional Gmail search query.

**Usage:**

```bash
python cli.py list-messages [--user-id USER_ID] [--query QUERY] [--max-results N] [--page-token TOKEN]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--user-id` | string | `me` | Gmail user (use `me` for the authenticated user). |
| `--query` | string | — | Gmail search query (e.g. `is:unread`, `from:user@example.com`). |
| `--max-results` | integer | 10 | Maximum number of messages to return (1–500). |
| `--page-token` | string | — | Page token from a previous response for pagination. |

**Example Gmail queries:**

- `is:unread` – Unread messages  
- `from:alice@example.com` – From a specific sender  
- `to:me` – Sent to you  
- `subject:meeting` – Subject contains “meeting”  
- `has:attachment` – Has attachments  
- `after:2024/01/01` – After a date  
- `label:important` – With label “important”  
- Combined: `is:unread from:boss@company.com`

**Output shape:**

```json
{
  "messages": [{"id": "...", "threadId": "..."}, ...],
  "nextPageToken": "..." | null,
  "resultSizeEstimate": 42
}
```

Use `id` from `messages` with **get-message** to fetch full content.

---

### `get-message`

Fetch a single message by ID.

**Usage:**

```bash
python cli.py get-message --message-id ID [--user-id USER_ID] [--format FORMAT]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--message-id` | string | *(required)* | Gmail message ID. |
| `--user-id` | string | `me` | Gmail user. |
| `--format` | string | `metadata` | `minimal`, `full`, `metadata`, or `raw`. |

**Formats:**

- **`metadata`** – Headers (Subject, From, To, Date), snippet, label IDs, size; no body.
- **`full`** – Same plus body: `body_plain` / `body_html` for multipart, or `body` for single-part.
- **`minimal`** – Minimal fields.
- **`raw`** – Raw RFC 2822; response shape may differ.

**Output shape (metadata/full):**

```json
{
  "id": "...",
  "threadId": "...",
  "labelIds": ["INBOX", "UNREAD"],
  "snippet": "...",
  "subject": "...",
  "from": "...",
  "to": "...",
  "date": "...",
  "body_plain": "..." | null,
  "body_html": "..." | null
}
```

---

### `send-message`

Send a plain-text email.

**Usage:**

```bash
python cli.py send-message --to TO --subject SUBJECT --body BODY [--user-id USER_ID] [--cc CC] [--bcc BCC]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--to` | string | *(required)* | Recipient email address(es). |
| `--subject` | string | *(required)* | Subject line. |
| `--body` | string | *(required)* | Plain-text body. |
| `--user-id` | string | `me` | Gmail user sending the message. |
| `--cc` | string | — | CC addresses (comma-separated). |
| `--bcc` | string | — | BCC addresses (comma-separated). |

**Output shape:**

```json
{
  "id": "...",
  "threadId": "...",
  "labelIds": ["SENT"]
}
```

---

### `list-labels`

List all Gmail labels for the user.

**Usage:**

```bash
python cli.py list-labels [--user-id USER_ID]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--user-id` | string | `me` | Gmail user. |

**Output shape:**

```json
{
  "labels": [
    {"id": "INBOX", "name": "INBOX", "type": "system"},
    {"id": "Label_123", "name": "My Label", "type": "user"}
  ]
}
```

Use label **ids** in search queries (e.g. `label:INBOX`).

---

## Examples

List the 5 most recent unread messages:

```bash
python cli.py list-messages --query "is:unread" --max-results 5
```

Get full body of a message:

```bash
python cli.py get-message --message-id "18abc123def456" --format full
```

Send an email with CC:

```bash
python cli.py send-message --to "alice@example.com" --subject "Notes" --body "See attached." --cc "bob@example.com"
```

List labels (to use in queries):

```bash
python cli.py list-labels
```

---

## Error output

On error, the CLI prints a JSON object with an `"error"` key and exits with code 1:

```json
{"error": "Credentials file not found: ..."}
```

See [Troubleshooting](troubleshooting.md) for common errors and fixes.
