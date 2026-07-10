# Deployment Guide

## Local Development

```bash
cd interview-ai/backend
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Start PostgreSQL and Redis (e.g., via Docker)
docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15

cd ..
docker-compose up --build
```

## AWS Production Deployment

### 1. Infrastructure

- **EKS** or **ECS** for container orchestration.
- **RDS PostgreSQL** for relational data.
- **ElastiCache Redis** for caching and Celery broker.
- **S3** for file storage.
- **Pinecone** for vector search.
- **Route 53** + **ACM** for DNS and TLS certificates.
- **ALB** or **NGINX Ingress Controller** for load balancing.

### 2. Secrets

Store in AWS Secrets Manager or SSM Parameter Store:
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `OPENAI_API_KEY`
- `S3_ACCESS_KEY` / `S3_SECRET_KEY`
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
- `PINECONE_API_KEY`

### 3. CI/CD

The GitHub Actions workflow:
1. Lints and type-checks code.
2. Runs tests against a PostgreSQL service.
3. Builds and pushes Docker image.
4. Deploys to EKS/ECS via kubectl or AWS CLI.

### 4. Kubernetes

```bash
kubectl apply -f infra/k8s-config.yaml
kubectl apply -f infra/k8s-deployment.yaml
```

### 5. Migrations

Run Alembic migrations before deploying:

```bash
kubectl exec -it deploy/interview-ai-api -- alembic upgrade head
```

### 6. Monitoring

- Prometheus/Grafana for metrics.
- AWS CloudWatch for logs.
- Sentry for error tracking.

## Security Checklist

- [ ] HTTPS/TLS enabled.
- [ ] JWT secrets rotated.
- [ ] Rate limiting configured.
- [ ] RBAC enforced.
- [ ] File uploads scanned and size-limited.
- [ ] Database credentials in secrets manager.
- [ ] Audit logging enabled.
- [ ] CORS restricted to frontend domain.
