from fastapi import FastAPI


app = FastAPI(title="AI Powered Pull Request Review")

@app.get("/")
def health():
    return {"status": "ok"}

