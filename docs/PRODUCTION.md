# Production Readiness Checklist

## Scalability

- Stateless API workers with horizontal pod autoscaling.
- Async AI/ML tasks via Celery workers.
- Redis caching layer.
- Connection pooling and database read replicas.
- S3/MinIO for durable object storage.
- Pinecone for vector search at scale.

## Security

- JWT access/refresh tokens.
- HTTPS/TLS with NGINX.
- Rate limiting per IP and per user.
- RBAC (candidate, recruiter, admin).
- Input validation with Pydantic.
- File upload validation and virus scanning.
- Audit logs for sensitive actions.
- Secrets in AWS Secrets Manager / Kubernetes Secrets.

## Explainability

- AI scores include reasoning, evidence, and confidence.
- Resume parsing returns extracted evidence.
- Job matching returns matched and missing skills.
- Interview reports include per-criterion breakdowns.

## Fairness

- No demographic inference in scoring.
- Model drift monitoring.
- Bias audits on resume scoring and job matching.
- Candidate consent and data retention controls.

## Observability

- Structured JSON logging.
- Prometheus metrics.
- Health check endpoint.
- Distributed tracing with OpenTelemetry.
- Sentry error tracking.

## Disaster Recovery

- Daily PostgreSQL backups.
- S3 cross-region replication.
- Kubernetes node redundancy.
- Documented runbook for rollback.
