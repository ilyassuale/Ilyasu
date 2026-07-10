# AI-Powered Virtual Interview System — Architecture

## 1. Overview

A cloud-native, modular platform that simulates real-time virtual job interviews. Candidates upload resumes, get matched to roles, complete AI-generated interviews (voice, video, technical), and receive explainable feedback. Recruiters and admins access dashboards, analytics, and reports.

## 2. High-Level Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                    │
│  React/Next.js SPA  ──  WebRTC (getUserMedia)  ──  WebSocket for realtime   │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │ HTTPS / WSS
┌──────────────────────────────▼──────────────────────────────────────────────┐
│                           Ingress / NGINX                                    │
│  TLS termination, rate limiting, static assets, reverse proxy                │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────────┐
│                          FastAPI Application                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │ Auth Router  │ │ Resume Router│ │ Interview    │ │ Dashboard    │       │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘       │
│  ┌──────▼───────────────▼──────────────────▼────────────────▼─────────┐     │
│  │              Domain Services (orchestration & agents)              │     │
│  │  ResumeParser  JobMatcher  InterviewEngine  Evaluator  Analytics   │     │
│  └──────┬───────────────┬──────────────┬──────────┬───────────────────┘     │
│         │               │              │          │                        │
│         ▼               ▼              ▼          ▼                        │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                    AI / ML Layer (async Celery)                    │     │
│  │  GPT-5.5  Whisper  Sentence Transformers  spaCy  MediaPipe  OpenCV │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└──────┬──────────────┬──────────────┬──────────┬─────────────────────────────┘
       │              │              │          │
       ▼              ▼              ▼          ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│PostgreSQL│  │  Redis   │  │ Pinecone │  │  S3/MinIO│
│  (data)  │  │ (cache/  │  │ (vectors)│  │  (files) │
│          │  │  queue)  │  │          │  │          │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

## 3. Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0, Alembic |
| Async Tasks | Celery, Redis, Flower (optional) |
| Auth | JWT, python-jose, passlib, python-social-auth / Google OAuth2 |
| AI/ML | OpenAI GPT-4o (or configurable), Whisper, SentenceTransformers, spaCy, PyMuPDF, python-docx, MediaPipe, OpenCV |
| Vector DB | Pinecone (or pgvector for self-hosted) |
| Database | PostgreSQL 15+ |
| Cache | Redis |
| Object Storage | AWS S3 or MinIO |
| Web Server | NGINX |
| Deployment | Docker, Docker Compose, Kubernetes (optional), AWS ECS/EKS, GitHub Actions |
| Monitoring | Prometheus, Grafana, structured logging, OpenTelemetry (optional) |

## 4. Module Boundaries

- `app/api/v1` — HTTP route definitions, input validation, dependency injection.
- `app/services` — Business logic orchestration; reusable, framework-agnostic.
- `app/agents` — AI/ML-specific workflows (generation, parsing, evaluation).
- `app/models` — SQLAlchemy ORM models.
- `app/schemas` — Pydantic request/response models.
- `app/core` — Config, security, logging, events.
- `app/db` — Session management and dependency injection.
- `app/utils` — Helpers (file, text, embeddings).
- `app/prompts` — Jinja2 templates for LLM prompts.
- `alembic` — Database migrations.
- `tests` — Unit, integration, and E2E tests.

## 5. Security Model

- JWT access tokens (short TTL) + refresh tokens (long TTL, stored hashed).
- Password hashing with bcrypt (Argon2 optional).
- OAuth2 via Google using `python-social-auth` or manual OAuth flow.
- RBAC: `candidate`, `recruiter`, `admin`.
- Rate limiting per endpoint per user/IP.
- HTTPS/TLS, CORS, HSTS, secure cookie flags.
- Input validation and sanitization via Pydantic.
- File upload scanning (ClamAV placeholder), size limits, allowed MIME types.
- Audit logging for authentication, report access, and admin actions.

## 6. Scalability & Resilience

- Stateless FastAPI workers behind NGINX.
- Celery workers for async AI/ML jobs.
- Redis for caching and Celery broker.
- Pinecone for low-latency vector search.
- S3/MinIO for durable file storage.
- Database connection pooling via SQLAlchemy async engine.
- Health checks and graceful shutdown.

## 7. Explainability & Fairness

- Every AI score returns `reasoning`, `evidence`, and `confidence`.
- Resume parsing returns raw extracted evidence.
- Job matching returns matched skills and missing skills.
- Interview evaluation returns per-criterion breakdowns.
- Audit log stores model versions and prompts.
- No protected-attribute inference in scoring logic.
