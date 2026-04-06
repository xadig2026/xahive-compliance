from __future__ import annotations

from pathlib import Path

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.modules.loader import ModuleLoader
from app.narratives import generate_readiness_narratives
from app.schemas import ModuleOut, ReadinessRequestIn
from app.scoring.readiness import build_readiness

APP_ROOT = Path(__file__).resolve().parent
REPO_ROOT = APP_ROOT.parent
MODULES_ROOT = REPO_ROOT / "modules"

# Local dev: create backend/.env (see .env.example). Optional: coding/.env for repo-root tooling.
# .env is gitignored; Azure/production should use app settings / Key Vault, not this file.
load_dotenv(REPO_ROOT / ".env")
load_dotenv(APP_ROOT / ".env", override=True)

module_loader = ModuleLoader(MODULES_ROOT)

app = FastAPI(title="xahive Cybersecurity Compliance Checklist API", version="0.1.0")

_cors = os.environ.get("CORS_ORIGINS", "").strip()
if _cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _cors.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.mount("/static", StaticFiles(directory=str(APP_ROOT / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (APP_ROOT / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/api/modules", response_model=list[ModuleOut])
def list_modules() -> list[ModuleOut]:
    return [ModuleOut(id=m.id, name=m.name, version=m.version) for m in module_loader.list_modules()]


@app.get("/api/modules/{module_id}")
def get_module(module_id: str) -> dict:
    try:
        return module_loader.get_module_meta(module_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Module not found")


@app.get("/api/modules/{module_id}/items")
def get_module_items(module_id: str) -> list[dict]:
    try:
        return module_loader.get_items(module_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Module not found")


@app.post("/api/modules/{module_id}/readiness")
def post_readiness(module_id: str, body: ReadinessRequestIn) -> dict:
    """
    Score saved answers (0–5 per applicable question) and return readiness
    rollups overall and by CSF Function. N/A items are excluded from averages.
    """
    try:
        items = module_loader.get_items(module_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Module not found")
    return build_readiness(module_id, items, body.responses)


@app.post("/api/modules/{module_id}/readiness/narratives")
def post_readiness_narratives(module_id: str, body: ReadinessRequestIn) -> dict:
    """
    Deterministic commentary: strengths, weaknesses, and improvement priorities per CSF function
    and overall. Uses OpenAI with temperature 0 + JSON schema when OPENAI_API_KEY is set;
    otherwise template text derived only from scored controls. Bullets are validated against
    control IDs present in the assessment.
    """
    try:
        items = module_loader.get_items(module_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Module not found")
    return generate_readiness_narratives(module_id, items, body.responses)
