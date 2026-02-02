# 🚀 Deployment Guide

## Quick Start (Docker - Recommended)

### 1. Prerequisites
- Docker & Docker Compose installed
- GitHub Personal Access Token (for webhook validation + API access)
- (Optional) Ollama running locally for LLM inference

### 2. Configure Environment Variables

Create `.env` files in each service directory with your actual tokens:

**`services/webhook/.env`**:
```bash
# GitHub Token (dual purpose: webhook signature + API auth)
GITHUB_TOKEN=ghp_your_actual_token_here
GITLAB_TOKEN=your_gitlab_token_here

# Infrastructure
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
ORCHESTRATOR_QUEUE=orchestrator_queue
```

**`services/git_worker/.env`**:
```bash
# Git Provider Tokens
GITHUB_TOKEN=ghp_your_actual_token_here
GITLAB_TOKEN=your_gitlab_token_here

# Infrastructure
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
ORCHESTRATOR_QUEUE=orchestrator_queue
LLM_QUEUE=llm_queue
GIT_QUEUE=git_queue
```

**`services/llm_worker/.env`**:
```bash
# Infrastructure
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
ORCHESTRATOR_QUEUE=orchestrator_queue
LLM_QUEUE=llm_queue
GIT_QUEUE=git_queue

# LLM Provider (choose one)
# Option 1: OpenAI
OPENAI_API_KEY=sk-...

# Option 2: Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Option 3: Ollama (Local - Default)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:3b
```

**`services/orchestrator/.env`**:
```bash
# Infrastructure
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
ORCHESTRATOR_QUEUE=orchestrator_queue
LLM_QUEUE=llm_queue
GIT_QUEUE=git_queue
```

### 3. Deploy

```bash
# Build and start all services
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f webhook
docker-compose logs -f orchestrator
```

### 4. Configure GitHub Webhook

1. Go to your repository → Settings → Webhooks → Add webhook
2. **Payload URL**: `http://your-server:8000/webhook/github`
3. **Content type**: `application/json`
4. **Secret**: Use the same value as your `GITHUB_TOKEN`
5. **Events**: Select "Pull requests"
6. Save

### 5. Test

```bash
# Use the simulation script
pdm run python scripts/simulate_webhook.py
```

---

## Local Development (Without Docker)

### 1. Install Dependencies

```bash
# Install PDM
pip install -U pdm

# Install project dependencies
pdm install
```

### 2. Start Infrastructure

```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start RabbitMQ
docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

### 3. Configure Environment

Set environment variables in your shell or create `.env` files (see Docker section above).

### 4. Run Services (4 separate terminals)

**Terminal 1 - Webhook**:
```powershell
$env:GITHUB_TOKEN="ghp_..."; $env:RABBITMQ_URL="amqp://guest:guest@localhost:5672/"; $env:REDIS_URL="redis://localhost:6379/0"; $env:ORCHESTRATOR_QUEUE="orchestrator_queue"; pdm run python -m uvicorn services.webhook.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Orchestrator**:
```powershell
$env:RABBITMQ_URL="amqp://guest:guest@localhost:5672/"; $env:REDIS_URL="redis://localhost:6379/0"; $env:ORCHESTRATOR_QUEUE="orchestrator_queue"; $env:LLM_QUEUE="llm_queue"; $env:GIT_QUEUE="git_queue"; pdm run python -m services.orchestrator.main
```

**Terminal 3 - LLM Worker**:
```powershell
$env:RABBITMQ_URL="amqp://guest:guest@localhost:5672/"; $env:REDIS_URL="redis://localhost:6379/0"; $env:LLM_QUEUE="llm_queue"; $env:GIT_QUEUE="git_queue"; $env:OLLAMA_BASE_URL="http://localhost:11434"; pdm run python -m services.llm_worker.main
```

**Terminal 4 - Git Worker**:
```powershell
$env:GITHUB_TOKEN="ghp_..."; $env:RABBITMQ_URL="amqp://guest:guest@localhost:5672/"; $env:REDIS_URL="redis://localhost:6379/0"; $env:GIT_QUEUE="git_queue"; pdm run python -m services.git_worker.main
```

---

## Architecture Notes

### Token Consolidation
**IMPORTANT**: `GITHUB_TOKEN` serves **dual purpose**:
1. **Webhook Signature Validation**: Used as the HMAC secret to validate incoming webhooks
2. **GitHub API Authentication**: Used to fetch PR data and post comments

This means:
- When configuring GitHub webhook, use your `GITHUB_TOKEN` as the "Secret"
- The same token is used for API calls
- No separate `GITHUB_WEBHOOK_SECRET` needed

### Queue System
- **RabbitMQ** handles message passing between services
- **Redis** stores conversation state and deduplication data
- Management UI: `http://localhost:15672` (guest/guest)

### Service Communication Flow
```
GitHub Webhook → Webhook Service → RabbitMQ (orchestrator_queue)
                                  ↓
                            Orchestrator → RabbitMQ (llm_queue)
                                          ↓
                                    LLM Worker → RabbitMQ (git_queue)
                                                ↓
                                          Git Worker → GitHub API
```

---

## Troubleshooting

### Docker Build Fails
**Issue**: Tree-sitter compilation errors
**Solution**: Dockerfiles include `build-essential` and `python3-dev`. If still failing, check Docker logs:
```bash
docker-compose logs webhook
```

### Webhook Returns 401
**Issue**: Invalid signature
**Solution**: Ensure `GITHUB_TOKEN` in `.env` matches the webhook secret in GitHub settings

### Service Can't Connect to RabbitMQ
**Issue**: Connection refused
**Solution**: 
```bash
# Check RabbitMQ is running
docker-compose ps rabbitmq

# Check logs
docker-compose logs rabbitmq
```

### Import Errors
**Issue**: `ModuleNotFoundError`
**Solution**: Services use relative imports. Run as modules:
```bash
python -m services.webhook.main  # ✅ Correct
python services/webhook/main.py  # ❌ Wrong
```

---

## Security Best Practices

1. **Never commit `.env` files** - They're in `.gitignore`
2. **Rotate tokens regularly** - Especially after any exposure
3. **Use separate tokens** for different environments (dev/staging/prod)
4. **Revoke immediately** if a token is accidentally pushed to git
5. **Limit token scopes** - Only grant necessary permissions

---

## Monitoring

### RabbitMQ Management UI
- URL: `http://localhost:15672`
- Credentials: `guest` / `guest`
- Monitor queue depths, message rates, connections

### Service Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f webhook

# Last 100 lines
docker-compose logs --tail=100 orchestrator
```

### Health Checks
```bash
# Webhook service
curl http://localhost:8000/health

# RabbitMQ
curl http://localhost:15672/api/health/checks/alarms
```
