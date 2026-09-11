"""FastAPI Application entrypoint."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.routes import router
from backend.services.postgres_repository import get_database_url

app = FastAPI(title="Orbit API", version="1.0.0")

try:
    app.state.database_url = get_database_url()
except Exception:
    app.state.database_url = None

import os

cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
if cors_origins_env:
    allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
    allow_credentials = "*" not in allowed_origins
else:
    allowed_origins = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5173",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://testserver",
    ]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok", "app": "orbit"}

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
uploads_dir = frontend_dir / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.api_route("/", methods=["GET", "HEAD"])
    def serve_frontend():
        return FileResponse(str(frontend_dir / "index.html"))
