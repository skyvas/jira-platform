# Code Style & Conventions

- All REST models must inherit from Pydantic BaseModel.
- Enforce strict typing with Python 3.9+ type hints.
- Tests must execute via pytest with exit code 0.
- Partial updates on PATCH endpoints must use sentinel defaults (_UNSET) and inspect req.model_fields_set for nullable fields.
- Protected API routes must use FastAPI dependency injection (Depends(get_current_user)).
- Administrative endpoints must enforce role checks via require_admin() dependency.
- All web entrypoints (main.py) must support dual-mode execution with a zero-dependency fallback (e.g. standard library http.server) when ASGI servers (uvicorn) are absent in WebAssembly / edge sandboxes.
- Separate production runtime dependencies in requirements.txt from build, test, and C-extension tools in requirements-dev.txt to preserve portability in edge/WASI environments.
- Edge manifests (app.yaml, wasmer.toml, .wasmerignore) must be maintained at the repository root and validated against wasmer package build before committing.

