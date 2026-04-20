import base64

from xoauth2 import xoauth2_inner_bytes, xoauth2_smtp_base64


def test_xoauth2_inner_bytes_format():
    inner = xoauth2_inner_bytes("a@b.com", "tok123")
    assert inner.startswith(b"user=a@b.com")
    assert b"auth=Bearer tok123" in inner
    assert inner.endswith(b"\x01\x01")


def test_xoauth2_smtp_base64_roundtrip():
    b64 = xoauth2_smtp_base64("u@x.com", "atok")
    raw = base64.b64decode(b64.encode("ascii"))
    assert b"user=u@x.com" in raw
    assert b"Bearer atok" in raw
