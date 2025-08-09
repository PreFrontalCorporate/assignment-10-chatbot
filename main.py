from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, httpx

GOOGLE_API_KEY = os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("Missing GOOGLE_GENERATIVE_AI_API_KEY env var")

# Allow your Pages domain + (optionally) Codespaces preview URL for dev
ALLOWED_ORIGINS = [
    # PROD: replace with your Pages origin:
    # e.g. "https://<username>.github.io"
    os.environ.get("ALLOW_ORIGIN_PAGES", "").strip(),
    # DEV: Codespaces origin (optional). You can set this at deploy time.
    os.environ.get("ALLOW_ORIGIN_CODESPACES", "").strip(),
]
ALLOWED_ORIGINS = [o for o in ALLOWED_ORIGINS if o]

app = FastAPI(title="Gemini Proxy (Cloud Run)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],   # tighten in prod!
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,
)

class GeneratePayload(BaseModel):
    model: str = "gemini-2.5-pro"
    contents: list
    generationConfig: dict | None = None
    safetySettings: list | None = None

@app.get("/healthz")
def health():
    return {"ok": True}

@app.post("/generate")
async def generate(body: GeneratePayload, request: Request):
    # Optional: basic origin check in addition to CORS (defense in depth)
    origin = request.headers.get("origin", "")
    if ALLOWED_ORIGINS and origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="Origin not allowed")

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{body.model}:generateContent?key={GOOGLE_API_KEY}"
    )
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            r = await client.post(endpoint, json=body.dict())
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Upstream error: {e!s}")

    if r.status_code >= 400:
        # Pass through Google error text to help debugging
        raise HTTPException(status_code=r.status_code, detail=r.text)

    return r.json()
