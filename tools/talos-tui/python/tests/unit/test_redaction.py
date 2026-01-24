import pytest
from talos_tui.adapters.redaction import redact_dict

def test_redact_denylist_keys():
    data = {"secret": "my_password", "public": "visible"}
    redacted = redact_dict(data)
    assert redacted["secret"] == "***REDACTED***"
    assert redacted["public"] == "visible"

def test_redact_nested_dict():
    data = {"meta": {"token": "12345"}}
    redacted = redact_dict(data)
    assert redacted["meta"]["token"] == "***REDACTED***"

def test_redact_pem():
    pem = "-----BEGIN PRIVATE KEY-----\nMIIEvgI...\n-----END PRIVATE KEY-----"
    data = {"cert": pem}
    redacted = redact_dict(data)
    assert redacted["cert"] == "***PEM REDACTED***"

def test_truncate_large_string():
    large = "A" * 70000
    data = {"blob": large}
    redacted = redact_dict(data)
    assert "TRUNCATED" in redacted["blob"]
    assert len(redacted["blob"]) < 1000
