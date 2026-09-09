# Code Style & Conventions

- All REST models must inherit from Pydantic BaseModel.
- Enforce strict typing with Python 3.9+ type hints.
- Tests must execute via pytest with exit code 0.
- Partial updates on PATCH endpoints must use sentinel defaults (_UNSET) and inspect req.model_fields_set for nullable fields.
- Protected API routes must use FastAPI dependency injection (Depends(get_current_user)).
- Administrative endpoints must enforce role checks via require_admin() dependency.

