import requests
import json
import hmac
import hashlib
import uuid
import time

# Configuration
WEBHOOK_URL = "http://localhost:8000/webhook/github"
SECRET = "your_github_token_here"  # Must match GITHUB_TOKEN

# Payload for PR #5 in Lmalviya/AI-Powered-Pull-Request-Review
payload = {
    "action": "opened",
    "number": 5,
    "pull_request": {
        "url": "https://api.github.com/repos/Lmalviya/AI-Powered-Pull-Request-Review/pulls/5",
        "id": 123456789,
        "number": 5,
        "state": "open",
        "title": "Feature: Add RabbitMQ Support",
        "user": {
            "login": "Lmalviya",
            "id": 1
        },
        "body": "This PR adds RabbitMQ support for better reliability.",
        "head": {
            "label": "Lmalviya:feature-rabbitmq",
            "ref": "feature-rabbitmq",
            "sha": "e5c6b7d8e9f0a1b2c3d4e5f6g7h8i9j0k1l2m3n4", # Mock SHA
            "repo": {
                "full_name": "Lmalviya/AI-Powered-Pull-Request-Review",
                "name": "AI-Powered-Pull-Request-Review",
                "owner": {
                    "login": "Lmalviya"
                }
            }
        },
        "base": {
            "label": "Lmalviya:main",
            "ref": "main",
            "sha": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0", # Mock SHA
            "repo": {
                "full_name": "Lmalviya/AI-Powered-Pull-Request-Review",
                "name": "AI-Powered-Pull-Request-Review",
                "owner": {
                    "login": "Lmalviya"
                }
            }
        }
    },
    "repository": {
        "id": 987654321,
        "node_id": "R_kgDOH...",
        "name": "AI-Powered-Pull-Request-Review",
        "full_name": "Lmalviya/AI-Powered-Pull-Request-Review",
        "private": False,
        "owner": {
            "login": "Lmalviya",
            "id": 1
        }
    },
    "sender": {
        "login": "Lmalviya"
    }
}

payload_bytes = json.dumps(payload).encode('utf-8')

# Generate Signature
signature = hmac.new(
    key=SECRET.encode('utf-8'),
    msg=payload_bytes,
    digestmod=hashlib.sha256
).hexdigest()

headers = {
    "Content-Type": "application/json",
    "X-GitHub-Event": "pull_request",
    "X-Hub-Signature-256": f"sha256={signature}",
    "X-GitHub-Delivery": str(uuid.uuid4())
}

print(f"Sending Webhook to {WEBHOOK_URL}...")
print(f"Repo: Lmalviya/AI-Powered-Pull-Request-Review")
print(f"PR: #5")

try:
    response = requests.post(WEBHOOK_URL, data=payload_bytes, headers=headers)
    print(f"Response Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Failed to connect: {e}")
