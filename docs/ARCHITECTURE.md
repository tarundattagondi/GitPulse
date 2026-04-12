# GitPulse Architecture

## System Diagram

```mermaid
graph TB
    subgraph Client
        FE[React Frontend<br/>Vite + Tailwind]
        EXT[Chrome Extension<br/>Manifest V3]
    end

    subgraph Backend["FastAPI Backend"]
        APP[app.py<br/>Routes + Middleware]

        subgraph Services
            ANA[analyzer.py<br/>Orchestrator]
            GH[github_service.py<br/>Async GitHub Client]
            SCR[scorer.py<br/>5-Category Scorer]
            JDA[jd_analyzer.py<br/>JD Parser]
            MAT[matcher.py<br/>Profile-JD Matcher]
            REC[recommender.py<br/>Action Plans]
            JBS[job_board_scanner.py<br/>SimplifyJobs Parser]
            PRA[pr_agent.py<br/>PR Agent]
            PT[progress_tracker.py<br/>Snapshots]
            RP[resume_parser.py<br/>PDF/DOCX Parser]
            TM[tri_match.py<br/>Tri-Source Matcher]
            CB[company_benchmarks.py<br/>Cohort Benchmarks]
            IG[interview_generator.py<br/>Interview Prep]
        end
    end

    subgraph External
        GHAPI[GitHub REST API<br/>+ GraphQL]
        CLAUDE[Anthropic Claude API]
        SIMPLIFY[SimplifyJobs Repo<br/>README.md]
    end

    subgraph Storage
        SUPA[(Supabase Postgres<br/>analyses, snapshots,<br/>cached_jobs, pr_log,<br/>rate_limits, benchmarks)]
    end

    FE -->|HTTP| APP
    EXT -->|HTTP| APP
    APP --> ANA
    APP --> JBS
    APP --> PRA
    APP --> PT
    APP --> TM
    APP --> CB
    APP --> IG
    ANA --> GH
    ANA --> SCR
    GH -->|httpx async| GHAPI
    SCR -->|anthropic SDK| CLAUDE
    JDA -->|anthropic SDK| CLAUDE
    MAT -->|anthropic SDK| CLAUDE
    REC -->|anthropic SDK| CLAUDE
    TM -->|anthropic SDK| CLAUDE
    IG -->|anthropic SDK| CLAUDE
    RP -->|anthropic SDK| CLAUDE
    JBS -->|httpx| SIMPLIFY
    PRA -->|PyGithub| GHAPI
    JBS --> SUPA
    PT --> SUPA
    PRA --> SUPA
    CB --> SUPA
```

## Data Flow

### Profile Analysis Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as FastAPI
    participant GH as GitHub API
    participant CL as Claude API
    participant FS as JSON Storage

    U->>FE: Enter username
    FE->>API: GET /api/analyze/{username}
    API->>GH: Fetch profile + repos (parallel)
    GH-->>API: Profile, repos, languages
    API->>GH: Fetch READMEs + commits (parallel)
    GH-->>API: README content, commit counts
    API->>CL: Score skills_match (semantic)
    API->>CL: Score project_relevance (semantic)
    CL-->>API: AI scores + reasoning
    API->>API: Score readme_quality (checklist)
    API->>API: Score activity_level (log-scaled)
    API->>API: Score profile_completeness (field checks)
    API->>FS: Save snapshot to progress_history.json
    API-->>FE: Score breakdown + snapshot
    FE-->>U: Render gauge + bars
```

### Job Matching Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant SJ as SimplifyJobs
    participant CL as Claude API
    participant FS as Cache

    U->>API: POST /api/scan-jobs
    API->>FS: Check cached_jobs.json (24hr TTL)
    alt Cache miss
        API->>SJ: Fetch README.md (raw)
        SJ-->>API: HTML table (1300+ rows)
        API->>API: Parse HTML into JobListings
        API->>FS: Write cache
    end
    API->>API: Filter by role/location/closed
    loop Each job (semaphore=5)
        API->>CL: Analyze JD + Match profile
        CL-->>API: Match score + gaps
    end
    API-->>U: Ranked results by match_score
```

### PR Agent Safety Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant PRA as PR Agent
    participant GH as GitHub API

    U->>API: POST /api/pr/open
    API->>PRA: open_readme_pr()
    PRA->>PRA: Log attempt to pr_log.json
    PRA->>GH: Authenticate with token
    PRA->>GH: Verify repo ownership
    alt Not owner
        PRA-->>API: 403 PermissionError
    end
    PRA->>PRA: Assert file == README.md
    PRA->>GH: Get default branch SHA
    PRA->>GH: Create feature branch
    PRA->>GH: Commit README to feature branch
    PRA->>GH: Open PR (feature → default)
    PRA->>PRA: Log success to pr_log.json
    PRA-->>API: {pr_url, pr_number, branch_name}
```

## Component Responsibilities

### Services

| Service | Responsibility | External Deps |
|---------|---------------|---------------|
| `analyzer.py` | Orchestrates fetch → score → snapshot pipeline | github_service, scorer, progress_tracker |
| `github_service.py` | Async GitHub data fetching (REST + GraphQL) | GitHub API via httpx |
| `scorer.py` | 5-category scoring (40+25+15+10+10=100) | Claude API for skills_match + project_relevance |
| `jd_analyzer.py` | Parses JD text into structured JSON | Claude API |
| `matcher.py` | Semantic profile-to-JD matching | Claude API |
| `recommender.py` | Generates projects, README rewrites, 30-day plans | Claude API |
| `job_board_scanner.py` | Fetches/parses/caches SimplifyJobs listings | SimplifyJobs repo via httpx |
| `pr_agent.py` | Generates README improvements, opens PRs | GitHub API via PyGithub, Claude API |
| `progress_tracker.py` | Saves/retrieves score snapshots, computes deltas | JSON file storage |
| `resume_parser.py` | Extracts text from PDF/DOCX, parses with AI | pypdf, python-docx, Claude API |
| `tri_match.py` | Cross-references GitHub + resume + JD | Claude API |
| `company_benchmarks.py` | Compares user vs company cohort averages | Seed JSON data |
| `interview_generator.py` | Generates tailored interview prep material | Claude API |

### Scoring Weights

| Category | Points | Method |
|----------|--------|--------|
| Skills Match | 40 | Claude semantic comparison against market/JD |
| Project Relevance | 25 | Claude semantic analysis of project quality |
| README Quality | 15 | Checklist (headings, code blocks, install, badges, usage) |
| Activity Level | 10 | log₂(commits_90d + 1), capped at 10 |
| Profile Completeness | 10 | 2 pts each: name, bio, location, company/blog, avatar |

### Rate Limiting

| Tier | Limit | Scope |
|------|-------|-------|
| Unauthenticated | 5 requests/day per IP | All `/api/*` analysis endpoints |
| With `X-Anthropic-Key` header | Unlimited | All endpoints |
| GitHub API (with token) | 5,000 requests/hour | GitHub data fetching |
| GitHub API (without token) | 60 requests/hour | GitHub data fetching |
