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
- Edge HTTP handlers must strictly partition API routes from SPA/static file fallback, ensuring every `/api/...` path returns JSON and never HTML, even on 404/500 errors.
- Workspace agent skills are maintained in `.agents/skills/<name>/SKILL.md` with Antigravity frontmatter and self-contained scripts/references.
- Multi-agent orchestration and automated regression pipelines must be defined as declarative DAGs in `workflows/*.yaml` and validated via `python -m src.cli run-graph workflows/<dag>.yaml --dry-run`.
- All autonomous worker nodes performing file mutations must specify `worktree: true` to enforce branch isolation outside protected branches.
- File upload endpoints in all runtime layers must parse multipart/form-data and base64 payloads into isolated file storage (`uploads/`), returning clean static asset URLs and preserving exact binary integrity.
- Image attachments in comment streams must render as compact thumbnail cards with `object-fit: contain` and visual type badges, triggering non-destructive Lightbox modals with Download actions that preserve the active ticket context upon dismissal.
- End-to-end browser integration tests must be implemented using Playwright (`playwright.sync_api` with `chromium`), ensuring isolated fixture lifecycles, explicit selector verification, and binary file download validation.
- Specialized domain skills for system architecture, tech evaluation, migration, observability, UI frontend engineering, web accessibility (WCAG 2.2), UX research, and product discovery are cataloged in `.agents/skills/` with verified schemas and executable Python toolchains.
