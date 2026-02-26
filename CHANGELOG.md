# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_Nothing yet._

## [1.0.0] - 2026-02-26

### Added

- **Gmail SMCP plugin** – CLI and MCP tools for Gmail API.
  - `list-messages` – list message IDs with optional query, pagination (`--query`, `--max-results`, `--page-token`).
  - `get-message` – fetch a single message by ID (metadata or full body, `--format` minimal/full/metadata/raw).
  - `send-message` – send plain-text email (`--to`, `--subject`, `--body`; optional `--cc`, `--bcc`).
  - `list-labels` – list Gmail labels.
- **SMCP integration** – `--describe` for tool discovery; tools exposed as `smcp-gmail__list-messages`, `smcp-gmail__get-message`, `smcp-gmail__send-message`, `smcp-gmail__list-labels`.
- **Gmail client** (`gmail_client.py`) – OAuth2 (credentials.json + token.json), path config via `GMAIL_CREDENTIALS_FILE` / `GMAIL_TOKEN_FILE`.
- **Test suite** – unit tests (cli, gmail_client with mocks), integration tests (CLI subprocess), e2e tests (optional, `GMAIL_E2E=1`); pytest-cov with 80% target; `run_tests.py`.
- **Documentation** – README (TOC, quick start, setup, usage, commands, testing); `docs/installation.md`, `docs/usage.md`, `docs/configuration.md`, `docs/development.md`, `docs/troubleshooting.md`, `docs/README.md`.
- **Dual license** – AGPLv3 for all code (LICENSE); CC BY-SA 4.0 for documentation and non-code (LICENSE-DOCS). Copyright and license notices in source files.

### Documentation

- Full installation guide (Google Cloud, Gmail API, OAuth consent, credentials).
- Usage guide: SMCP plugin install, MCP tool names, standalone CLI, all commands and parameters, output shapes, examples.
- Configuration: environment variables, credentials and token files, scopes.
- Development: running tests, coverage, unit/integration/e2e, contributing.
- Troubleshooting: common errors (credentials, token, 403, ModuleNotFoundError, SMCP tools, send failures).

### Legal

- Code licensed under GNU Affero General Public License v3.0 (see LICENSE).
- Documentation and other non-code material licensed under Creative Commons Attribution-ShareAlike 4.0 International (see LICENSE-DOCS).

---

[Unreleased]: https://github.com/sanctumos/smcp-gmail/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/sanctumos/smcp-gmail/releases/tag/v1.0.0
