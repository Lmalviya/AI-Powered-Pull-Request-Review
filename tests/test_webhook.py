import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from services.webhook.main import app
from services.webhook.config import settings

client = TestClient(app)

def get_signature(body: bytes, secret: str) -> str:
    """Helper to calculate HMAC SHA256 signature."""
    signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def test_github_webhook_opened_success():
    """Test successful github pull_request 'opened' event."""
    payload = {
        "action": "opened",
        "number": 1,
        "pull_request": {
            "title": "Test PR",
            "number": 1,
            "user": {"login": "testuser"},
            "base": {"ref": "main"},
            "head": {"ref": "feature"}
        },
        "repository": {
            "full_name": "owner/repo",
            "owner": {"login": "owner"}
        },
        "sender": {"login": "testuser"}
    }
    
    body = json.dumps(payload).encode("utf-8")
    secret = settings.github_webhook_secret
    signature = get_signature(body, secret)
    
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": "test-delivery-id",
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json"
    }
    
    response = client.post("/webhook/github", content=body, headers=headers)
    
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Event received"}

def test_github_webhook_invalid_signature():
    """Test github webhook with an invalid signature."""
    payload = {"action": "opened", "number": 1}
    body = json.dumps(payload).encode("utf-8")
    
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": "test-delivery-id",
        "X-Hub-Signature-256": "sha256=invalid_signature",
        "Content-Type": "application/json"
    }
    
    response = client.post("/webhook/github", content=body, headers=headers)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid signature"

def test_github_webhook_ignored_action():
    """Test that non-triggering actions are ignored (but still return 200)."""
    payload = {
        "action": "labeled", # Ignored action
        "number": 1,
        "pull_request": {
            "title": "Test PR",
            "number": 1,
            "user": {"login": "testuser"},
            "base": {"ref": "main"},
            "head": {"ref": "feature"}
        },
        "repository": {
            "full_name": "owner/repo",
            "owner": {"login": "owner"}
        },
        "sender": {"login": "testuser"}
    }
    
    body = json.dumps(payload).encode("utf-8")
    signature = get_signature(body, settings.github_webhook_secret)
    
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": "test-delivery-id",
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json"
    }
    
    response = client.post("/webhook/github", content=body, headers=headers)
    
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Event received"}
