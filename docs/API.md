# GitPulse API Reference

Base URL: `http://localhost:8000` (local) or `https://gitpulse-api.up.railway.app` (deployed)

---

## Health Check

### `GET /`

```bash
curl http://localhost:8000/
```

**Response:**
```json
{"status": "ok", "service": "gitpulse", "version": "0.1.0"}
```

---

## Profile Analysis

### `GET /api/analyze/{username}`

Fetch GitHub profile, score it, and save a progress snapshot.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `username` | path | required | GitHub username |
| `role_category` | query | `"other"` | One of: `backend`, `frontend`, `fullstack`, `ml`, `security`, `devops`, `cloud`, `data_engineering`, `mobile`, `other` |

```bash
curl "http://localhost:8000/api/analyze/tarundattagondi?role_category=backend"
```

**Response:**
```json
{
  "username": "tarundattagondi",
  "profile": {
    "login": "tarundattagondi",
    "name": null,
    "bio": null,
    "public_repos": 9,
    "followers": 1,
    "html_url": "https://github.com/tarundattagondi",
    "avatar_url": "..."
  },
  "repos_count": 9,
  "score": {
    "total_score": 61,
    "max_score": 100,
    "breakdown": {
      "skills_match": {"score": 24, "max": 40, "reasoning": "..."},
      "project_relevance": {"score": 16, "max": 25, "reasoning": "..."},
      "readme_quality": {"score": 15, "max": 15, "reasoning": "..."},
      "activity_level": {"score": 2, "max": 10, "reasoning": "..."},
      "profile_completeness": {"score": 2, "max": 10, "reasoning": "..."}
    }
  },
  "snapshot": {
    "timestamp": "2026-04-12T02:28:54.123Z",
    "role_category": "backend",
    "overall_score": 61,
    "category_scores": {...},
    "delta_since_last": null
  }
}
```

---

### `GET /api/score/{username}`

Score a profile, optionally against a specific job description.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `username` | path | required | GitHub username |
| `job_description` | query | `null` | Job description text |
| `role_category` | query | `"other"` | Role category |

```bash
curl "http://localhost:8000/api/score/tarundattagondi?job_description=SWE+Intern+Java+Python"
```

---

## Job Board

### `GET /api/jobs`

Browse SimplifyJobs Summer 2026 internship listings.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `role` | query | `null` | Comma-separated role keywords |
| `location` | query | `null` | Comma-separated location keywords |
| `exclude_closed` | query | `true` | Hide closed positions |

```bash
curl "http://localhost:8000/api/jobs?role=software,engineer&location=NYC,SF"
```

**Response:**
```json
{
  "total": 42,
  "jobs": [
    {
      "company": "The New York Times",
      "role": "Full Stack Engineer Intern",
      "location": "NYC",
      "link": "https://...",
      "posted_date": "2026-04-11",
      "is_closed": false,
      "sponsors_visa": true
    }
  ]
}
```

---

### `POST /api/scan-jobs`

Start an async job scan with profile matching.

**Request body:**
```json
{
  "username": "tarundattagondi",
  "role_filters": ["software", "engineer"],
  "location_filters": ["NYC"],
  "max_jobs": 10
}
```

```bash
curl -X POST http://localhost:8000/api/scan-jobs \
  -H "Content-Type: application/json" \
  -d '{"username":"tarundattagondi","role_filters":["software"],"max_jobs":5}'
```

**Response:**
```json
{"scan_id": "a1b2c3d4", "status": "running"}
```

---

### `GET /api/scan-jobs/status/{scan_id}`

Poll scan progress. Returns results when `status` is `"completed"`.

```bash
curl http://localhost:8000/api/scan-jobs/status/a1b2c3d4
```

**Response (completed):**
```json
{
  "scan_id": "a1b2c3d4",
  "status": "completed",
  "total_jobs_scanned": 5,
  "matched_jobs": 5,
  "results": [
    {
      "company": "Acme",
      "role": "SWE Intern",
      "match_score": 72,
      "match_details": {...}
    }
  ]
}
```

---

## PR Agent

### `POST /api/pr/preview`

Preview a README improvement without any GitHub writes.

**Request body:**
```json
{
  "username": "tarundattagondi",
  "repo_name": "CloudGuard",
  "token": "ghp_..."
}
```

```bash
curl -X POST http://localhost:8000/api/pr/preview \
  -H "Content-Type: application/json" \
  -d '{"username":"tarundattagondi","repo_name":"CloudGuard","token":"ghp_..."}'
```

**Response:**
```json
{
  "current_readme": "# CloudGuard\n...",
  "suggested_readme": "# CloudGuard\n\n[![Build](...)...",
  "diff_summary": "--- README.md (current)\n+++ README.md (suggested)\n...",
  "stats": {"additions": 85, "deletions": 3}
}
```

---

### `POST /api/pr/open`

Open a PR with an improved README. Safety enforced: only README.md, only repos you own, always feature branch.

**Request body:**
```json
{
  "username": "tarundattagondi",
  "repo_name": "CloudGuard",
  "new_readme_content": "# CloudGuard\n\n...",
  "token": "ghp_..."
}
```

**Response:**
```json
{
  "pr_url": "https://github.com/tarundattagondi/CloudGuard/pull/1",
  "pr_number": 1,
  "branch_name": "gitpulse/readme-improvement-20260412-143022"
}
```

---

## Progress Tracking

### `GET /api/progress/{username}`

Get score history with delta analysis.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `username` | path | required | GitHub username |
| `role_category` | query | `null` | Filter by role |
| `days` | query | `90` | Time window |

```bash
curl "http://localhost:8000/api/progress/tarundattagondi?days=90"
```

**Response:**
```json
{
  "username": "tarundattagondi",
  "snapshot_count": 3,
  "latest_score": 67,
  "latest_timestamp": "2026-04-12T02:28:54Z",
  "deltas": [
    "Apr 11: 61/100 (→ 0 from 61)",
    "Apr 12: 67/100 (↑ +6 from 61) [Skills Match +4, Activity Level +2]"
  ],
  "snapshots": [...]
}
```

---

## Tri-Source Matching

### `POST /api/tri-match`

Cross-reference GitHub profile, resume, and job description. Accepts **multipart form data**.

| Field | Type | Description |
|-------|------|-------------|
| `github_username` | string | GitHub username |
| `jd_text` | string | Job description text |
| `resume` | file | Resume file (PDF, DOCX, or TXT) |

```bash
curl -X POST http://localhost:8000/api/tri-match \
  -F "github_username=tarundattagondi" \
  -F "jd_text=SWE Intern, Java, Python, SQL required" \
  -F "resume=@resume.pdf"
```

**Response:**
```json
{
  "github_username": "tarundattagondi",
  "resume_skills_found": 27,
  "resume_projects_found": 2,
  "jd_role_category": "backend",
  "match_result": {
    "resume_says_github_doesnt_prove": [...],
    "github_shows_resume_doesnt_mention": [...],
    "both_missing_for_jd": [...],
    "resume_rewrite_suggestions": [...],
    "github_project_suggestions": [...]
  }
}
```

---

## Company Benchmarks

### `GET /api/benchmark/companies`

List available companies for benchmarking.

```bash
curl http://localhost:8000/api/benchmark/companies
```

**Response:**
```json
{
  "companies": ["Amazon", "Berkeley Research Group", "Databricks", "Google", "Meta", "Microsoft", "QTS Data Centers", "Salesforce", "Snowflake", "Stripe"]
}
```

---

### `GET /api/benchmark/{username}/{company}`

Compare a user's profile against a company's intern cohort.

```bash
curl http://localhost:8000/api/benchmark/tarundattagondi/Salesforce
```

**Response:**
```json
{
  "company": "Salesforce",
  "overall_percentile": 43,
  "overall_verdict": "Developing candidate for Salesforce — focus on gaps",
  "dimensions": {
    "repo_count": {"user": 9, "cohort_avg": 12, "percentile": 41, "verdict": "On par with cohort"},
    "star_count": {"user": 1, "cohort_avg": 15, "percentile": 20, "verdict": "Below cohort average"},
    "language_match": {"overlap_pct": 80, "matched": ["java","javascript","python","typescript"], "missing": ["apex"], "percentile": 80},
    "project_relevance": {"coverage_pct": 0, "covered": [], "not_covered": ["CRM integrations","REST APIs"], "percentile": 1},
    "readme_quality": {"user": 15, "cohort_avg": 11, "percentile": 63, "verdict": "On par with cohort"}
  }
}
```

---

## Interview Prep

### `POST /api/interview-prep`

Generate tailored interview preparation material.

**Request body:**
```json
{
  "username": "tarundattagondi",
  "jd_text": "Salesforce SWE Intern. Required: Java, Python, SQL, REST APIs..."
}
```

```bash
curl -X POST http://localhost:8000/api/interview-prep \
  -H "Content-Type: application/json" \
  -d '{"username":"tarundattagondi","jd_text":"SWE Intern, Java, Python, SQL"}'
```

**Response:**
```json
{
  "username": "tarundattagondi",
  "role_category": "backend",
  "overall_match_pct": 62,
  "prep": {
    "technical_questions": [
      {
        "question": "Walk through how you would extend CloudGuard to store scan results in PostgreSQL...",
        "why_asked": "Tests database design thinking...",
        "suggested_answer_framework": "Start with schema design...",
        "skill_tested": "SQL and relational database design"
      }
    ],
    "behavioral_questions": [...],
    "coding_challenges": [
      {
        "problem": "Design a RESTful API endpoint...",
        "difficulty": "medium",
        "topics": ["REST API", "data validation"],
        "hint": "Focus on proper HTTP methods..."
      }
    ],
    "gap_coverage_questions": [
      {
        "question": "You haven't worked with Kubernetes...",
        "gap": "Kubernetes and container orchestration",
        "how_to_prepare": "Complete K8s tutorial...",
        "backup_answer": "While I haven't used K8s directly..."
      }
    ]
  }
}
```

---

## Error Responses

All errors return JSON with consistent structure:

| Status | Body |
|--------|------|
| `400` | `{"error": "bad_request", "message": "..."}` |
| `403` | `{"error": "forbidden", "message": "..."}` |
| `429` | `{"error": "rate_limit_exceeded", "message": "...", "limit": 5, "used": 6}` |
| `500` | `{"error": "internal_server_error", "message": "..."}` |

## Rate Limiting

- **5 requests/day per IP** on analysis endpoints (without API key)
- **Unlimited** with `X-Anthropic-Key` header
- Rate-limited paths: `/api/analyze`, `/api/score`, `/api/scan-jobs`, `/api/tri-match`, `/api/interview-prep`, `/api/pr/preview`, `/api/pr/open`
