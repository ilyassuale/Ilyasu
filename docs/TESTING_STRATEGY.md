# Testing Strategy

## 1. Unit Tests

- `pytest` for service logic (parsing, scoring, matching).
- `pytest-asyncio` for async services and database tests.
- Target 80%+ coverage for `app/services` and `app/schemas`.

## 2. Integration Tests

- Test FastAPI + async test client (`httpx.AsyncClient`) for API routes.
- Test database with PostgreSQL in CI.
- Mock external services (OpenAI, Whisper, S3) with `respx` or `unittest.mock`.

## 3. E2E Tests

- Playwright for frontend flows.
- Test resume upload, interview flow, and report generation.

## 4. Security Tests

- OWASP ZAP for API vulnerability scanning.
- Rate limiting tests.
- RBAC permission tests.

## 5. Performance Tests

- Locust for load testing interview APIs.
- Async pool and Celery worker scaling validation.

## 6. Test Commands

```bash
cd backend
pytest -q
pytest --cov=app --cov-report=html
ruff check .
mypy app --ignore-missing-imports
```

## 7. CI/CD

- Run lint, typecheck, and tests on every PR.
- Block merge if coverage drops below 70%.
