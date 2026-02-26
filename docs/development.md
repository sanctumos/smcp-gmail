# Development

This document covers running the test suite, coverage, and contributing to smcp-gmail.

## Test suite

### Install test dependencies

```bash
pip install -r requirements-testing.txt
```

This pulls in:

- `requirements.txt` (Gmail API and auth)
- `pytest`
- `pytest-cov`
- `pytest-mock`

### Run all tests (unit + integration)

```bash
python run_tests.py
```

Or with pytest directly:

```bash
pytest tests/unit tests/integration -v --tb=short
```

`run_tests.py` also runs coverage and enforces a **minimum 80%** coverage for `cli` and `gmail_client`. If coverage is below 80%, the run fails.

### Run with coverage report

```bash
pytest tests/unit tests/integration --cov=cli --cov=gmail_client --cov-report=term-missing --cov-fail-under=80
```

Or:

```bash
python run_tests.py
```

Coverage is reported in the terminal with “Missing” lines. HTML report:

```bash
pytest tests/unit tests/integration --cov=cli --cov=gmail_client --cov-report=html
# open htmlcov/index.html
```

---

## Test layout

| Directory | Purpose |
|-----------|---------|
| **tests/unit/** | Unit tests with mocks. `test_cli.py` tests the CLI (describe, commands, errors). `test_gmail_client.py` tests the Gmail client (path helpers, header/body parsing, API calls with mocked service). |
| **tests/integration/** | Integration tests: run the CLI as a subprocess and assert on stdout/exit codes and JSON. No Gmail credentials required; `list-labels` is expected to return a JSON error when creds are missing. |
| **tests/e2e/** | End-to-end tests against the real Gmail API. Skipped unless explicitly enabled. |

---

## Unit tests

- **CLI** – `tests/unit/test_cli.py`  
  - `_describe_spec()` structure and content.  
  - `main()`: `--describe`, no command, each command (list-messages, get-message, send-message, list-labels) with patched `gmail_client`, and error handling (FileNotFoundError, generic exception).  
  - Tests that patch `gmail_client` use `pytest.importorskip("google.auth")` so they are skipped when Gmail API deps are not installed.

- **Gmail client** – `tests/unit/test_gmail_client.py`  
  - Path helpers: `_credentials_path()`, `_token_path()` with and without env.  
  - Parsing: `_header()`, `_decode_body()`, `_first_part_body()`.  
  - `get_credentials()`: FileNotFoundError when credentials file is missing.  
  - `list_messages`, `get_message` (metadata and full with parts/body), `send_message`, `list_labels` with **mocked** `get_service()` so no real API calls.

When **google-api-python-client** (and related) are not installed, the entire `test_gmail_client` module is skipped (via `pytest.importorskip("google.auth")` at the top), and the CLI tests that patch `gmail_client` are skipped. Remaining tests (describe, no-command, integration) still run.

---

## Integration tests

- **tests/integration/test_cli_integration.py**  
  - Run `cli.py` via subprocess.  
  - `--describe`: valid JSON, plugin name, command names.  
  - No args: non-zero exit, help-like output.  
  - `list-labels`: exit 1 and JSON with `"error"` (or traceback if deps missing).  
  - Required-arg handling for `get-message` and `send-message`.  
  - `list-messages` with args: either success JSON or error JSON.

No credentials or Gmail access needed; at most the subprocess fails with a clear error.

---

## E2E tests

E2E tests call the real Gmail API. They are **skipped by default**.

**Enable and run:**

```bash
# Ensure credentials.json (or GMAIL_CREDENTIALS_FILE) exists and token is authorized
export GMAIL_E2E=1
pytest -m e2e -v
```

They expect a valid token (run at least one Gmail command in the browser first if needed). Do not enable in CI unless you use a dedicated test account and secure secrets.

---

## Code style and tools

- Prefer Python 3.8+ style; no legacy compatibility layers required.
- The project uses pytest only; no flake8/black/mypy config in-tree. You can add them and wire to CI as needed.

---

## Contributing

1. Fork the repository.
2. Create a branch, make changes, add or update tests.
3. Run the full suite and ensure coverage stays ≥ 80%:  
   `python run_tests.py`
4. Open a pull request with a short description of the change.

If you add new CLI commands or Gmail client behavior, extend the unit and integration tests and update [Usage](usage.md) and [README](../README.md) as needed.
