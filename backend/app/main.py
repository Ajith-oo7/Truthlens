from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import get_settings
from app.observability.tracing import configure_observability

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
settings = get_settings()
configure_observability()

app = FastAPI(
    title="TruthLens",
    description="Agentic fact verification system. Not a chatbot.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=(settings.cors_origin_list + ["*"]) if settings.app_env == "local" else settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.middleware("http")
async def no_cache_ui(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/ui"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


ui_dir = Path(__file__).resolve().parents[2] / "apps" / "web"
if ui_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(ui_dir), html=True), name="ui")


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui/")
