from fastapi import FastAPI
from .api import github_api, gitlab_api
from .utils import logger

app = FastAPI(
    title="AI Pull Request Reviewer - Webhook Service",
    description="Service to ingest and validate webhooks from GitHub/GitLab",
    version="0.1.0"
)

# Include Routers
app.include_router(github_api.router, tags=["GitHub Webhooks"])
app.include_router(gitlab_api.router, tags=["GitLab Webhooks"])

@app.on_event("startup")
async def startup_event():
    logger.info("Webhook service is starting up...")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
