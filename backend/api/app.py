"""FastAPI Application entrypoint."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.routes import router
from backend.services.postgres_repository import get_database_url

app = FastAPI(title="Orbit API", version="1.0.0")

app.state.database_url = get_database_url()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
uploads_dir = frontend_dir / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(str(frontend_dir / "index.html"))
