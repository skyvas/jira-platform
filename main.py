"""Root application entrypoint for deployment platforms (Wasmer, Render, Railway, Fly.io, etc.)."""
import os
import uvicorn
from backend.api.app import app

# Export app for ASGI servers like uvicorn main:app
__all__ = ["app"]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=False)
