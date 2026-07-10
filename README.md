# AI-Powered Virtual Job Interview Simulation System

A production-grade, cloud-native platform for AI-driven resume analysis, job matching, and virtual interviews.

## Quick Start

```bash
cp backend/.env.example backend/.env
# Edit .env with your OPENAI_API_KEY, Google OAuth credentials, and storage settings
docker-compose up --build
```

The API will be available at `http://localhost:8000` and NGINX at `http://localhost`.

## Project Structure

```
interview-ai/
├── backend/              FastAPI backend
│   ├── app/
│   │   ├── api/v1/       REST API routes
│   │   ├── core/         Config, security, logging
│   │   ├── db/           Database session and migrations
│   │   ├── models/       SQLAlchemy ORM models
│   │   ├── schemas/      Pydantic request/response models
│   │   ├── services/     Business logic (parsing, scoring, matching)
│   │   ├── agents/       LLM/ML clients
│   │   └── prompts/      Jinja2 prompt templates
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/             React/Next.js SPA (placeholder)
├── nginx/                NGINX reverse proxy
├── infra/                Kubernetes manifests
├── docs/                 Architecture, ER diagrams, API docs
├── docker-compose.yml
└── .github/workflows/    CI/CD
```

## Key Features

- **User Auth**: Email, Google OAuth, JWT, password reset.
- **Resume Upload**: PDF, DOCX, TXT extraction with PyMuPDF, python-docx.
- **Resume Intelligence**: ATS, resume score, missing skills, grammar, role recommendations.
- **Job Matching**: Semantic similarity with sentence transformers.
- **AI Interview Generator**: Adaptive questions across HR, technical, behavioral, leadership, coding, SQL, system design.
- **Voice Interview**: Whisper-based speech-to-text.
- **AI Evaluation**: Scoring across 9 dimensions.
- **Behavioral Analytics**: OpenCV/MediaPipe face and pose heuristics.
- **Feedback Generator**: Report with scores, strengths, roadmap, courses.
- **Recruiter & Admin Dashboards**: Candidate search, reports, analytics.

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [ER Diagram](docs/ER_DIAGRAM.md)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Testing Strategy](docs/TESTING_STRATEGY.md)

## Environment Variables

See `backend/.env.example`.

## License

MIT
