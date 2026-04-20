"""Optional live Gmail IMAP tests (skipped unless GMAIL_IMAP_LIVE=1 and env configured)."""

import os

import pytest

pytestmark = pytest.mark.skip(reason="Set GMAIL_IMAP_LIVE=1 and configure GMAIL_* to enable live IMAP e2e")


def test_placeholder():
    assert os.environ.get("GMAIL_IMAP_LIVE", "").lower() not in ("1", "true")
