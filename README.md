# 🤖 AI-Powered Pull Request Reviewer

An intelligent, rigorous, and automated code review agent that acts as a senior developer on your team. It integrates directly with GitHub and GitLab, processes code changes using state-of-the-art LLMs (OpenAI, Anthropic, or Local/Ollama), and posts actionable, context-aware inline comments.

## 🌟 Key Features

*   **⚡ Multi-Platform Support**: Seamlessly works with **GitHub Pull Requests** and **GitLab Merge Requests**.
*   **🤖 Universal LLM Support**: Plug-and-play support for **OpenAI (GPT-4)**, **Anthropic (Claude 3)**, and **Ollama (Llama 3 Local)** with automatic provider detection.
*   **🧠 Deep Context Analysis**:
    *   **Semantic Filtering**: Uses AST (Abstract Syntax Tree) parsing to ignore non-meaningful changes (whitespace, simple renames).
    *   **Agentic Tool Use**: The AI can "read" your repository. If a diff references an unknown function, the AI pauses, fetches the function definition from the codebase, and *then* reviews the code.
*   **💬 Stateful Conversations**: Maintains a conversation history for every chunk of code, allowing for multi-step reasoning and context gathering.
*   **🚫 Smart Noise Reduction**:
    *   **Relevancy Filters**: Automatically ignores lockfiles, images, and non-source directories.
    *   **Idempotency**: Guarantees that the same comment is never posted twice, even if the webhook triggers multiple times.

---

## 🏗 System Architecture

The system is built as a distributed microservices architecture using **Python `asyncio`**, **RabbitMQ** (for reliable message passing), and **Redis** (for state persistence).

### 1. Webhook Service (`services/webhook/`)
*   **Role**: The secure Entry Point.
*   **Function**: Ingests hooks, validates SHA256 signatures (GitHub) or Tokens (GitLab), and filters for relevant events (`opened`, `synchronize`).
*   **Output**: Pushes `START_PR_REVIEW` tasks to Redis.

### 2. Orchestrator Service (`services/orchestrator/`)
*   **Role**: The Workflow Manager.
*   **Function**: 
    - Fetches the Diff from the SCM.
    - Runs **Semantic Filtering** (Tree-sitter) to drop noise.
    - **Chunks** large diffs into manageable 10-line pieces.
*   **Output**: Pushes `EVALUATE_CHUNK` tasks to the LLM Queue.

### 3. LLM Worker (`services/llm_worker/`)
*   **Role**: The "Brain".
*   **Function**: 
    - Maintains stateful conversations in Redis.
    - Decides whether to **Comment** or **Call a Tool** (e.g., `read_file`).
*   **Output**: Sends actions (`GIT_COMMENT` or `TOOL_CALL`) to the Git Queue.

### 4. Git Worker (`services/git_worker/`)
*   **Role**: The "Hands".
*   **Function**: 
    - Executes side effects: posting comments to GitHub/GitLab.
    - reads file content for the AI when requested.
    - Closes the feedback loop by sending new context back to the Orchestrator.

---

## 🚀 Getting Started

### Prerequisites
*   **Python**: 3.13+
*   **Redis**: Running locally or via Docker.
*   **RabbitMQ**: Running locally or via Docker (Management Plugin enabled).
*   **PDM**: Python Dependency Manager (`pip install -U pdm`).
*   **Docker** (Optional but recommended).

### 🔧 Installation (Local)

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/ai-pr-reviewer.git
    cd ai-pr-reviewer
    ```

2.  **Install Dependencies**
    ```bash
    pdm install
    ```

3.  **Configure Environment**
    Create `.env` files in each service directory (`services/webhook/`, `services/llm_worker/`, etc.) or export variables globally.

    **Critical Variables:**
    ```bash
    # Redis
    REDIS_URL=redis://localhost:6379/0
    
    # RabbitMQ
    RABBITMQ_URL=amqp://guest:guest@localhost:5672/

    # Git Provider (Choose one or both)
    GITHUB_TOKEN=ghp_...
    GITHUB_WEBHOOK_SECRET=your_secret
    GITLAB_TOKEN=glpat_...

    # LLM Provider (Examples)
    OPENAI_API_KEY=sk-...  # Will auto-select OpenAI
    # OR
    ANTHROPIC_API_KEY=sk-ant-... # Will auto-select Claude
    # OR
    # (Nothing set) -> Defaults to Ollama (http://localhost:11434)
    ```

4.  **Run Services (Separate Terminals)**
    ```bash
    # Terminal 1: Webhook
    pdm run uvicorn services.webhook.main:app --port 8000

    # Terminal 2: Orchestrator
    pdm run python -m services.orchestrator.main

    # Terminal 3: LLM Worker
    pdm run python -m services.llm_worker.main

    # Terminal 4: Git Worker
    pdm run python -m services.git_worker.main
    ```

---

## 🐳 Docker Deployment (Recommended)

The entire system is containerized.

1.  **Build & Run**
    ```bash
    docker-compose up --build -d
    ```

This spins up:
- Redis (Alpine)
- Webhook Service (Port 8000)
- Orchestrator Worker
- LLM Worker
- Git Worker

---

## 🔮 Roadmap

*   **Batch Commenting**: Aggregating comments to reduce API calls.
*   **Token Budgeting**: Smarter context window management for very large files.
*   **Chat Bot Mode**: Allow users to reply to the AI's comments in the PR to trigger a conversation.