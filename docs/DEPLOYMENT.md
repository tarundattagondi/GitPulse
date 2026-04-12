# GitPulse Deployment Guide

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vercel     │     │   Railway   │     │   Chrome     │
│  (Frontend)  │────▶│  (Backend)  │◀────│  Extension   │
│  React SPA   │     │  FastAPI    │     │  Manifest V3 │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  Supabase   │
                    │  Postgres   │
                    └─────────────┘
```

---

## 1. Backend — Railway

### Steps

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select the `GitPulse` repository
4. Railway will auto-detect the `Procfile` and `railway.json`

### Environment Variables

Set these in the Railway dashboard under **Variables**:

| Variable | Value |
|----------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (`sk-ant-...`) |
| `GITHUB_TOKEN` | GitHub personal access token (`ghp_...`) |
| `CLAUDE_MODEL` | `claude-sonnet-4-5` |
| `SUPABASE_URL` | Your Supabase project URL (`https://xxx.supabase.co`) |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (`eyJ...`) |

### Supabase Setup

1. Create a project at [supabase.com](https://supabase.com)
2. Run the schema SQL in the SQL Editor (creates tables: `analyses`, `snapshots`, `cached_jobs`, `pr_log`, `rate_limits`, `company_benchmarks`)
3. Copy the project URL and service role key to Railway env vars
4. Seed benchmarks: `python -m backend.seed_benchmarks`

### Verify

Once deployed, Railway provides a public URL (e.g. `https://gitpulse-api.up.railway.app`).

Test the health check:
```bash
curl https://gitpulse-api.up.railway.app/
# Expected: {"status":"ok","service":"gitpulse","version":"0.1.0"}
```

### Notes

- The `Procfile` runs: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
- Railway automatically sets `$PORT`
- The `railway.json` configures health check on `/` and auto-restart on failure

---

## 2. Frontend — Vercel

### Steps

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **"Add New Project"** → import the `GitPulse` repository
3. Configure the project:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### Environment Variables

Set in Vercel dashboard under **Settings → Environment Variables**:

| Variable | Value |
|----------|-------|
| `VITE_API_BASE_URL` | Your Railway backend URL (e.g. `https://gitpulse-api.up.railway.app`) |

### SPA Routing

The `frontend/vercel.json` is already configured with rewrites to handle client-side routing:
```json
{"rewrites": [{"source": "/(.*)", "destination": "/index.html"}]}
```

### CORS Update

After deploying, update `backend/app.py` to replace the Vercel wildcard with your actual domain:
```python
allow_origins=[
    "http://localhost:5173",
    "https://your-app.vercel.app",  # ← replace this
]
```

Then redeploy the backend.

---

## 3. Chrome Extension

The extension is not published to the Chrome Web Store. Install it locally:

1. Open `chrome://extensions` in Chrome
2. Enable **Developer mode** (top-right toggle)
3. Click **"Load unpacked"**
4. Select the `extension/` folder from this repo

### Configure Backend URL

Before loading, update `extension/popup.js` line 2:
```javascript
const API_BASE = 'https://gitpulse-api.up.railway.app';  // ← your Railway URL
```

See `docs/EXTENSION_INSTALL.md` for detailed instructions.

---

## Post-Deploy Checklist

- [ ] Backend health check returns 200 at `/`
- [ ] Frontend loads at Vercel URL
- [ ] Frontend can call backend (check browser Network tab for CORS errors)
- [ ] Extension can extract JD from a LinkedIn job page
- [ ] Extension can score a profile against extracted JD
- [ ] CORS origins updated in `backend/app.py` with actual Vercel domain
- [ ] Extension `API_BASE` updated with actual Railway URL

---

## Local Development

To run everything locally:

```bash
# Terminal 1: Backend
uvicorn backend.app:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Extension: load extension/ folder in chrome://extensions
# Update extension/popup.js API_BASE to http://localhost:8000
```

The Vite dev server proxies `/api` requests to `localhost:8000` automatically.
