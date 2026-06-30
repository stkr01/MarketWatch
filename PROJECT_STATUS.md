# Pre-Market Swing Trading Dashboard - Project Status

**Last Updated:** 2026-06-30  
**Status:** Fas 0-3 COMPLETE ✅ - Ready for Fas 4 Deployment

---

## 📊 Project Overview

**Goal:** Live dashboard for swing trading (1-30 day holds) on US equities, replacing daily email reports.

**Target Server:** skzdev02 (Azure VM, private Tailscale network)  
**Architecture:** Python FastAPI backend + React frontend + SQLite database  
**Key Feature:** Real-time market scanning + Claude AI on-demand analysis

---

## ✅ Completed Work

### Fas 0: Project Setup (DONE)
- ✅ GitHub repo initialized (`C:\Data\Pre-Market`)
- ✅ Backend structure: FastAPI + SQLAlchemy + SQLite
- ✅ Frontend structure: React + Vite + TypeScript
- ✅ Database schema (5 tables: tickers, scans, scan_results, news_items, ai_analyses)
- ✅ Environment configuration (dev/prod separation via .env)
- ✅ Initial commits to git

### Fas 1: Data Pipeline (DONE)
- ✅ `collectors/universe.py` - Top 10 NASDAQ/NYSE tickers
- ✅ `collectors/market_data.py` - yfinance gap%, volume, EMA100 (FIXED pandas Series issue)
- ✅ `collectors/news_feed.py` - feedparser RSS feeds (CNBC, MarketWatch, Yahoo)
- ✅ `screeners/swing_rules.py` - Gap%, volume, EMA100, news catalyst filtering
- ✅ `pipeline.py` - End-to-end scan orchestration
- ✅ `scheduler.py` - APScheduler (every minute in dev, 5-min pre-market in prod)
- ✅ `test_pipeline_local.py` - All 7 tests PASSING

### Fas 2: Backend API (DONE)
- ✅ FastAPI app with CORS middleware
- ✅ 5 REST endpoints fully implemented:
  - `GET /api/candidates` - Current scan candidates
  - `GET /api/stock/{ticker}` - Stock metadata
  - `GET /api/news/{ticker}` - Recent news
  - `POST /api/stock/{ticker}/analyze` - Claude on-demand analysis
  - `POST /api/scan` - Manual scan trigger (background thread)
  - `GET /api/scan/status` - Scan status + next run countdown
- ✅ Database integration (SQLite write operations)
- ✅ Claude API integration (Anthropic SDK)
- ✅ Scheduler startup/shutdown hooks in main.py
- ✅ Error handling & logging throughout

### Fas 3: React Frontend (DONE)
- ✅ Professional dark-themed dashboard
- ✅ Real-time candidate table (30s polling)
  - Color-coded gap% (🟢 up, 🔴 down)
  - Volume metrics with 💚 highlighting
  - EMA100 position (Above/Below) with indicator
  - News presence indicator 📰
- ✅ Stock detail view with news feed
- ✅ Claude AI analysis panel with caching & refresh
- ✅ Scan status bar with countdown timer
- ✅ Manual scan trigger with visual feedback
- ✅ React Query for server state management
- ✅ Axios API client with error handling
- ✅ Responsive design (mobile-friendly)

---

## 🔧 Tech Stack (Final)

### Backend
- **Language:** Python 3.10+
- **Framework:** FastAPI 0.104+
- **Server:** Uvicorn
- **Database:** SQLite (via SQLAlchemy ORM)
- **Migrations:** Alembic
- **Data Fetching:**
  - yfinance 0.2.32 (market data)
  - feedparser 6.0.10 (RSS news)
  - pandas 3.0+ (data manipulation)
- **Scheduling:** APScheduler 3.11
- **AI:** Anthropic Python SDK 0.114+ (Claude API)
- **Testing:** pytest

### Frontend
- **Framework:** React 18
- **Build:** Vite 5
- **Language:** TypeScript
- **HTTP:** Axios
- **State:** React Query (TanStack Query v5)
- **Routing:** React Router DOM v6
- **Styling:** Custom CSS (dark theme)

### Infrastructure
- **Deployment:** systemd (Linux units on skzdev02)
- **Reverse Proxy:** nginx
- **Network:** Private Tailscale network
- **Git:** GitHub (dev/main branch strategy)

---

## 🚀 How to Run Locally

### Backend Setup
```bash
cd C:\Data\Pre-Market\backend

# Create venv (first time only)
python -m venv venv
.\venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Create .env with API key
cp .env.example .env
# Add: ANTHROPIC_API_KEY=sk-ant-api03-...

# Start server
uvicorn app.main:app --reload --port 8000
```

**Logs show:** Data collection → screening → candidate matches ✓

### Frontend Setup
```bash
cd C:\Data\Pre-Market\frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**Dashboard at:** http://localhost:5173

### Full Flow Test
1. Open dashboard
2. Click "🔄 Scan Now"
3. Wait 10-20 seconds
4. Candidates appear in table
5. Click "View" → see stock detail + news
6. Click "🤖 Analyze" → Claude AI analysis loads

---

## 📁 Project Structure

```
C:\Data\Pre-Market\
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry
│   │   ├── config.py               # Env-based config
│   │   ├── db.py                   # SQLAlchemy setup
│   │   ├── models.py               # ORM models (5 tables)
│   │   ├── schemas.py              # Pydantic models
│   │   ├── pipeline.py             # Scan orchestration
│   │   ├── scheduler.py            # APScheduler jobs
│   │   ├── routers/                # API endpoints (5 files)
│   │   ├── collectors/             # Data fetching (3 files)
│   │   ├── screeners/              # swing_rules.py
│   │   └── ai/                     # claude_analyzer.py
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── test_pipeline_local.py      # 7/7 tests PASSING
├── frontend/
│   ├── src/
│   │   ├── pages/                  # Dashboard.tsx
│   │   ├── components/             # 4 UI components
│   │   ├── api/                    # Axios client
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css               # Dark theme
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── .env.example
├── deploy/
│   ├── skzdev02/
│   │   ├── premarket-backend.service
│   │   ├── nginx.conf.snippet
│   │   └── DEPLOY.md
│   └── deploy.sh
├── .github/workflows/              # CI/CD (placeholder)
├── .gitignore
├── CLAUDE.md                       # AI context doc
├── README.md                       # Feature overview
├── LOCAL_DEV_GUIDE.md              # Dev setup guide
├── PROJECT_STATUS.md               # THIS FILE
└── .git/                           # Git repo

```

---

## 🎯 Swing Trading Rules (Current)

**Screening Criteria:**
- **Gap %:** ±2.0% (configurable in `config.py`)
- **Volume:** 1.5x of 20-day average (configurable)
- **EMA100:** Trend indicator (above = uptrend, below = downtrend)
- **News:** Must have ≥1 recent news item (last 48 hours) - REQUIRED

**Tickers:** Top 10 NASDAQ/NYSE (dev mode, can scale to 500)

**Scan Frequency:**
- Dev: Every minute (APScheduler)
- Prod: Every 5 minutes, 04:00–09:30 EST, Mon-Fri

---

## 🔄 Data Flow

```
Pre-market window
    ↓
APScheduler triggers (every 1 min dev / 5 min prod)
    ↓
pipeline.py: run_market_scan()
    ├── Collectors: yfinance, feedparser
    ├── Screeners: swing_rules filtering
    ├── Database: save scan_results, news_items
    └── Return candidates list
    ↓
Frontend polls /api/candidates (every 30s)
    ↓
User sees updated dashboard
    ↓
User clicks "Analyze" → POST /api/stock/{ticker}/analyze
    ↓
Claude API → analysis cached in DB
    ↓
Frontend displays Claude response
```

---

## 🐛 Known Issues / Fixed

### FIXED ✅
1. ~~APScheduler next_run_time attribute error~~ → Added graceful handling
2. ~~Pandas Series scalar extraction error~~ → Robust .item() conversion
3. ~~Scan endpoint not triggering~~ → Background thread implementation
4. ~~Frontend not refetching after scan~~ → Auto-refetch after 15s

### Current Limitations
- No historical tracking of scan performance
- News feeds limited to CNBC, MarketWatch, Yahoo (can expand)
- No backtesting interface (planned for future)
- SQLite only (scales to ~500 stocks, then consider PostgreSQL)

---

## 📝 Swing Trading Rules Customization

To adjust screening rules, edit `backend/app/config.py`:

```python
GAP_THRESHOLD_PERCENT = 2.0        # Change to 1.5 or 3.0
VOLUME_MULTIPLIER = 1.5            # Change to 2.0 for stricter filtering
NEWS_LOOKBACK_HOURS = 48           # Adjust news recency window
```

Or override via `.env`:
```
GAP_THRESHOLD_PERCENT=2.5
VOLUME_MULTIPLIER=1.8
```

---

## 🚀 Next Steps: Fas 4 - Deploy to skzdev02

### What needs to be done:
1. **systemd service unit** - Run backend as daemon
2. **nginx config** - Reverse proxy + static frontend serving
3. **deploy.sh automation** - Git pull → pip install → build → restart
4. **Tailscale access** - Already set up on skzdev02
5. **Environment variables** - Set .env on production server
6. **Database persistence** - SQLite file location `/opt/premarket/data/`

### Files ready:
- `deploy/skzdev02/premarket-backend.service` ✓
- `deploy/skzdev02/nginx.conf.snippet` ✓
- `deploy/deploy.sh` ✓

### Timeline estimate:
- ~30 min to set up systemd unit
- ~20 min to configure nginx
- ~10 min to test end-to-end on server

---

## 📚 Documentation Files

- **CLAUDE.md** - Full AI context (architecture, decisions, open questions)
- **README.md** - Feature overview & quick start
- **LOCAL_DEV_GUIDE.md** - Detailed local development instructions
- **PROJECT_STATUS.md** - THIS FILE (current progress & next steps)
- **.github/workflows/ci.yml** - CI/CD pipeline (placeholder)

---

## 🔐 Security Notes

- **API Keys:** Never commit .env files (in .gitignore)
- **CORS:** Set to "*" for local dev, restrict for production
- **Auth:** No authentication for MVP (Tailscale network is private)
- **HTTPS:** nginx on skzdev02 will handle TLS

---

## 💾 Database

### Current Tables
```sql
tickers(id, symbol, name, exchange, market_cap, last_updated)
scans(id, timestamp, status, candidate_count)
scan_results(id, scan_id, ticker_id, gap_pct, volume, ema_100, above_ema_100, has_news, timestamp)
news_items(id, ticker_id, title, source, url, published_at, fetched_at)
ai_analyses(id, ticker_id, requested_at, prompt_version, response, usage_tokens, timestamp)
```

### View Database
```bash
cd backend
.\venv\Scripts\python -c "
from app.db import SessionLocal
from app.models import Scan
db = SessionLocal()
scans = db.query(Scan).order_by(Scan.id.desc()).limit(5).all()
for s in scans:
    print(f'Scan {s.id}: {s.candidate_count} candidates at {s.timestamp}')
"
```

---

## 🎓 How to Continue Later

1. **Clone repo:**
   ```bash
   cd C:\Data\Pre-Market
   git status  # Check branch
   ```

2. **Read this file** for context

3. **Start backend:**
   ```bash
   cd backend
   .\venv\Scripts\activate
   uvicorn app.main:app --reload --port 8000
   ```

4. **Start frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

5. **Test:**
   - Dashboard: http://localhost:5173
   - Click "🔄 Scan Now"
   - Verify candidates appear

6. **Next:** Deploy to skzdev02 (Fas 4)

---

## 📊 Git Commits (Recent)

```
eb4a185 - Fix: Robust pandas value extraction from yfinance data
4d24cc9 - Fix: Pandas Series scalar extraction in market_data.py
97aa7d8 - Fix: APScheduler next_run_time attribute error
e34aeab - Fix: Improve scan triggering and debug mode
7ef585c - Add Local Development Guide for testing Fas 2-3
c92c940 - Fas 2-3: Complete backend & frontend implementation
526db3e - Fas 1: Complete - all pipeline tests passing (7/7)
86ab06c - Fas 1: Data pipeline implementation - collectors, screeners, API endpoints
35ea481 - Fas 0: Initial project setup - FastAPI backend + React frontend skeleton
```

---

## 🤝 Team Notes

- **Developer:** Stefan Krantz
- **Developed with:** Claude Haiku (AI Assistant)
- **Development Duration:** ~6 hours (Fas 0-3)
- **Next Session Goal:** Deploy Fas 4 to skzdev02 (est. 1-2 hours)

---

## 📞 Quick Troubleshooting

**Backend won't start?**
- Check Python version: `python --version` (need 3.10+)
- Check venv activated: `pip list | findstr fastapi`
- Verify .env exists with ANTHROPIC_API_KEY

**Frontend shows "Cannot POST /api/scan"?**
- Backend not running? Start it first
- Check http://localhost:8000/health returns `{"status": "ok"}`

**No candidates after scan?**
- Check backend logs for data fetching errors
- Market data might not match screening rules
- Try lowering GAP_THRESHOLD_PERCENT in config.py

**Claude analysis fails?**
- Verify ANTHROPIC_API_KEY is valid
- Check API rate limits at console.anthropic.com
- Verify news data exists for the stock

---

**Status:** Ready for Fas 4 deployment. All local testing complete. ✅

