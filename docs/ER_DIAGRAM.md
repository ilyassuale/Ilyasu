# Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  companies  │1       *│  recruiters │*       1│  users      │
├─────────────┤         ├─────────────┤         ├─────────────┤
│ id (PK)     │─────────│ id (PK)     │         │ id (PK)     │
│ name        │         │ user_id(FK) │─────────│ email       │
│ domain      │         │ company_id  │         │ hashed_pw   │
│ logo_url    │         │ role        │         │ is_active   │
│ created_at  │         │ created_at  │         │ role        │
└─────────────┘         └─────────────┘         │ created_at  │
                                                └──────┬──────┘
                                                       │
                              ┌────────────────────────┼────────────────────────┐
                              │                        │                        │
                              ▼                        ▼                        ▼
                        ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
                        │  resumes    │        │interview_   │        │  reports    │
                        ├─────────────┤        │  sessions   │        ├─────────────┤
                        │ id (PK)     │        ├─────────────┤        │ id (PK)     │
                        │ user_id(FK) │        │ id (PK)     │        │ session_id  │
                        │ file_url    │        │ user_id(FK) │        │ scores (json)│
                        │ parsed_json │        │ job_id(FK)  │        │ strengths[] │
                        │ scores(json)│        │ status      │        │ weaknesses[]│
                        │ created_at  │        │ started_at  │        │ roadmap     │
                        └─────────────┘        │ completed_at│        │ created_at  │
                                               └──────┬──────┘        └─────────────┘
                                                      │
                           ┌──────────────────────────┼──────────────────────────┐
                           │                          │                          │
                           ▼                          ▼                          ▼
                     ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
                     │  questions  │         │  answers    │         │ analytics   │
                     ├─────────────┤         ├─────────────┤         ├─────────────┤
                     │ id (PK)     │         │ id (PK)     │         │ id (PK)     │
                     │ session_id  │         │ question_id │         │ session_id  │
                     │ type        │         │ audio_url   │         │ behavior    │
                     │ text        │         │ transcript  │         │ metrics     │
                     │ category    │         │ evaluation  │         │ created_at  │
                     │ difficulty  │         │ created_at  │         └─────────────┘
                     └─────────────┘         └─────────────┘

┌─────────────┐
│  jobs       │
├─────────────┤
│ id (PK)     │
│ company_id  │
│ title       │
│ description │
│ skills[]    │
│ embedding   │
│ created_at  │
└─────────────┘
```
