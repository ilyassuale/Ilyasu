# PostgreSQL Database Schema

## 1. users

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK, default gen_random_uuid() |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| hashed_password | VARCHAR(255) | NULL for OAuth-only users |
| full_name | VARCHAR(255) | NULL |
| is_active | BOOLEAN | DEFAULT true |
| is_verified | BOOLEAN | DEFAULT false |
| role | VARCHAR(50) | candidate, recruiter, admin |
| auth_provider | VARCHAR(50) | email, google |
| provider_id | VARCHAR(255) | NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

Indexes: `email`, `provider_id`

## 2. password_resets

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK users.id ON DELETE CASCADE |
| token_hash | VARCHAR(255) | UNIQUE, NOT NULL |
| expires_at | TIMESTAMPTZ | NOT NULL |
| used | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMPTZ | DEFAULT now() |

## 3. user_profiles

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK users.id ON DELETE CASCADE |
| phone | VARCHAR(50) | NULL |
| location | VARCHAR(255) | NULL |
| linkedin_url | VARCHAR(255) | NULL |
| portfolio_url | VARCHAR(255) | NULL |
| bio | TEXT | NULL |
| timezone | VARCHAR(50) | DEFAULT 'UTC' |

## 4. companies

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| domain | VARCHAR(255) | UNIQUE |
| logo_url | VARCHAR(500) | NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

## 5. recruiters

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK users.id ON DELETE CASCADE |
| company_id | UUID | FK companies.id ON DELETE SET NULL |
| internal_role | VARCHAR(100) | NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

## 6. resumes

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK users.id ON DELETE CASCADE |
| file_key | VARCHAR(500) | S3/MinIO key |
| file_name | VARCHAR(255) | NOT NULL |
| mime_type | VARCHAR(100) | NOT NULL |
| parsed_text | TEXT | NULL |
| parsed_json | JSONB | NULL |
| ats_score | SMALLINT | NULL |
| resume_score | SMALLINT | NULL |
| job_fit_score | SMALLINT | NULL |
| missing_skills | JSONB | NULL |
| grammar_issues | JSONB | NULL |
| recommended_roles | JSONB | NULL |
| strengths | JSONB | NULL |
| weaknesses | JSONB | NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

Indexes: `user_id`, `GIN(parsed_json)`, `GIN(missing_skills)`, `GIN(recommended_roles)`

## 7. jobs

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| company_id | UUID | FK companies.id ON DELETE SET NULL |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | NOT NULL |
| required_skills | TEXT[] | NULL |
| preferred_skills | TEXT[] | NULL |
| experience_min | SMALLINT | NULL |
| experience_max | SMALLINT | NULL |
| location | VARCHAR(255) | NULL |
| employment_type | VARCHAR(50) | NULL |
| vector_id | VARCHAR(255) | Pinecone vector id |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

Indexes: `GIN(required_skills)`, `GIN(preferred_skills)`, `is_active`

## 8. interview_sessions

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK users.id ON DELETE CASCADE |
| resume_id | UUID | FK resumes.id ON DELETE SET NULL |
| job_id | UUID | FK jobs.id ON DELETE SET NULL |
| title | VARCHAR(255) | NULL |
| status | VARCHAR(50) | pending, active, paused, completed |
| difficulty | VARCHAR(50) | easy, medium, hard |
| started_at | TIMESTAMPTZ | NULL |
| completed_at | TIMESTAMPTZ | NULL |
| config | JSONB | NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

Indexes: `user_id`, `job_id`, `status`

## 9. questions

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| session_id | UUID | FK interview_sessions.id ON DELETE CASCADE |
| category | VARCHAR(50) | hr, technical, behavioral, situational, leadership, problem_solving, coding, sql, system_design |
| question_type | VARCHAR(50) | open, mcq, coding, sql |
| text | TEXT | NOT NULL |
| context | JSONB | NULL |
| expected_keywords | TEXT[] | NULL |
| difficulty | VARCHAR(50) | NULL |
| sequence | SMALLINT | NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

Indexes: `session_id`, `category`, `sequence`

## 10. answers

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| question_id | UUID | FK questions.id ON DELETE CASCADE |
| session_id | UUID | FK interview_sessions.id ON DELETE CASCADE |
| transcript | TEXT | NULL |
| audio_url | VARCHAR(500) | NULL |
| code | TEXT | NULL |
| selected_option | VARCHAR(255) | NULL |
| start_time | TIMESTAMPTZ | NULL |
| end_time | TIMESTAMPTZ | NULL |
| word_count | SMALLINT | NULL |
| wpm | SMALLINT | NULL |
| evaluation | JSONB | NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

Indexes: `question_id`, `session_id`, `GIN(evaluation)`

## 11. reports

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| session_id | UUID | FK interview_sessions.id ON DELETE CASCADE |
| user_id | UUID | FK users.id ON DELETE CASCADE |
| overall_score | SMALLINT | NULL |
| correctness | SMALLINT | NULL |
| communication | SMALLINT | NULL |
| confidence | SMALLINT | NULL |
| relevance | SMALLINT | NULL |
| completeness | SMALLINT | NULL |
| technical_accuracy | SMALLINT | NULL |
| fluency | SMALLINT | NULL |
| vocabulary | SMALLINT | NULL |
| professionalism | SMALLINT | NULL |
| behavioral_score | SMALLINT | NULL |
| technical_score | SMALLINT | NULL |
| section_scores | JSONB | NULL |
| strengths | TEXT[] | NULL |
| weaknesses | TEXT[] | NULL |
| communication_tips | TEXT[] | NULL |
| roadmap | JSONB | NULL |
| recommended_courses | JSONB | NULL |
| reasoning | TEXT | NULL |
| confidence_level | VARCHAR(50) | NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

Indexes: `session_id`, `user_id`, `GIN(section_scores)`

## 12. analytics_events

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| session_id | UUID | FK interview_sessions.id ON DELETE CASCADE |
| user_id | UUID | FK users.id ON DELETE CASCADE |
| event_type | VARCHAR(100) | NOT NULL |
| payload | JSONB | NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

Indexes: `session_id`, `user_id`, `event_type`, `created_at`

## 13. audit_logs

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| actor_id | UUID | FK users.id ON DELETE SET NULL |
| action | VARCHAR(255) | NOT NULL |
| resource_type | VARCHAR(100) | NOT NULL |
| resource_id | UUID | NULL |
| details | JSONB | NULL |
| ip_address | INET | NULL |
| user_agent | TEXT | NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

Indexes: `actor_id`, `resource_type`, `resource_id`, `created_at`
