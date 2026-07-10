# API Documentation

Base URL: `https://api.interview-ai.example.com/api/v1`

## Authentication

### POST /auth/register
Register a new candidate.

**Request**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "Jane Doe"
}
```

**Response**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { ... }
}
```

### POST /auth/login
Login with email/password.

**Request**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

### POST /auth/google
Login with Google ID token.

**Request**
```json
{
  "token": "<google_id_token>"
}
```

### POST /auth/password-reset/request
Request password reset email.

### POST /auth/password-reset/confirm
Reset password with token.

## Resumes

### POST /resumes/upload
Upload PDF/DOCX/TXT resume.

- `Content-Type: multipart/form-data`
- Field: `file`

### POST /resumes/{id}/parse
Parse resume and generate intelligence.

### GET /resumes/{id}
Get parsed resume with intelligence.

### POST /resumes/{id}/match
Get top 10 matching jobs.

## Jobs

### GET /jobs
List active jobs.

### POST /jobs
Create a new job (recruiter/admin).

## Interviews

### POST /interviews
Create an interview session.

**Request**
```json
{
  "resume_id": "uuid",
  "job_id": "uuid",
  "title": "Backend Engineer Mock",
  "difficulty": "medium",
  "question_categories": ["hr", "technical", "behavioral"]
}
```

### POST /interviews/{id}/start
Start session and generate questions.

### GET /interviews/{id}
Get current session state.

### POST /interviews/{id}/answer
Submit an answer.

**Request**
```json
{
  "question_id": "uuid",
  "transcript": "My answer...",
  "audio_base64": "<optional>",
  "duration_seconds": 45
}
```

### POST /interviews/{id}/complete
Complete session and generate report.

### GET /interviews/{id}/report
Get final report.

## Recruiter

### GET /recruiter/candidates
Search candidates.

### GET /recruiter/reports
List all candidate reports.

### GET /recruiter/analytics
Recruiter dashboard metrics.

## Admin

### GET /admin/users
List users.

### PUT /admin/users/{id}/toggle
Activate/deactivate user.

### GET /admin/analytics
Admin analytics.

## Analytics

### GET /analytics/dashboard
Candidate dashboard.

### GET /analytics/skill-trends
Missing skills aggregation.
