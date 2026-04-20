"""Pytest fixtures and shared config."""
import os
import sys
from pathlib import Path

# Ensure project root is on path for "import cli" and IMAP modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "e2e: end-to-end tests requiring Gmail credentials (run with -m e2e)"
    )
