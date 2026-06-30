# Pre-Market Dashboard — AI Assistant Context

## Project Overview

Pre-Market Swing Trading Dashboard — a live, real-time monitoring tool for swing trading candidates (1–30 day holds) on US equities. Built for Stefan on skzdev02 (Azure VM, private Tailscale network).

**Goal**: Replace daily email reports with a live dashboard that continuously scans for swing trading catalysts (gap%, volume, EMA100, news).

**MVP Status**: Phase 0 — Core architecture laid out. Fas 1–5 ready to implement.

## Key Architecture Decisions

1. **Backend**: Python + FastAPI (not Node) — yfinance/pandas/feedparser are Python-first
2. **Database**: SQLite — simple, no extra service to maintain
3. **Real-time**: Polling (REST, 30–60s) MVP → WebSockets later if needed
4. **AI**: Claude API (Anthropic), on-demand per ticker (not auto on all candidates)
5. **Scanning**: Every 5 minutes during pre-market (04:00–09:30 EST, weekdays)
6. **Data**: Top 10 tickers for dev (configurable, can scale to 500)
7. **Auth**: None for MVP (Tailscale network is already private)

## Dev/Prod Separation

- **GitHub**: `main` (prod) ← `development` ← feature branches
- **.env files**: Separate for dev/prod, never committed. `.env.example` as template.
- **Database**: Separate SQLite files (`dev.db`, `prod.db`)
- **Systemd**: Dev on port 8001, prod on port 8000 (if both run on skzdev02)
- **API Key**: Anthropic key configured per environment

## Open Questions Resolved with Stefan

1. **Swing trading rules** — Gap% ±2%, Volume 1.5x avg, News required (configurable defaults)
2. **API key** — Stefan will create new Anthropic API key later
3. **Test data** — Top 10 tickers for MVP (can become config later)

## Data Flow

```
Pre-market window (04:00–09:30 EST, weekdays)
    ↓
APScheduler triggers every 5 minutes
    ↓
collectors/
  • market_data.py — yfinance: gap%, volume, EMA100
  • news_feed.py — feedparser: recent news per ticker
  • universe.py — Top 10 tickers
    ↓
screeners/swing_rules.py — filter by rules
    ↓
Database (scan_results, news_items)
    ↓
Frontend polls every 30–60s
    ↓
User clicks "Analyze" → ai/claude_analyzer.py → Claude API
    ↓
Response cached in ai_analyses table
```

## Key Files & Paths

### Backend
- `backend/app/main.py` — FastAPI entry point
- `backend/app/config.py` — Environment-based configuration
- `backend/app/models.py` — SQLAlchemy ORM (Ticker, Scan, ScanResult, NewsItem, AIAnalysis)
- `backend/app/routers/` — REST endpoints (candidates, stock, analyze, scan, news)
- `backend/app/collectors/` — Data fetching (market_data, news_feed, universe)
- `backend/app/screeners/swing_rules.py` — Rule-based filtering
- `backend/app/ai/claude_analyzer.py` — Claude integration
- `backend/app/scheduler.py` — APScheduler job setup

### Frontend
- `frontend/src/pages/Dashboard.tsx` — Main page
- `frontend/src/components/` — CandidateTable, StockDetail, AIAnalysisPanel, ScanStatusBar
- `frontend/src/api/client.ts` — Axios API client
- `frontend/vite.config.ts` — Dev proxy to localhost:8000

### Deploy
- `deploy/skzdev02/premarket-backend.service` — systemd unit
- `deploy/skzdev02/nginx.conf.snippet` — reverse proxy config
- `deploy/deploy.sh` — automated deploy script

## Swing Trading Rules (Initial Defaults)

These are configurable in `.env`:

- **Gap%**: ±2% (can be ±2 to ±5%)
- **Volume**: 1.5x of 20-day average
- **EMA100**: Trend indicator (above = uptrend, below = downtrend), NOT a hard filter
- **News**: Must have >= 1 recent news item (last 48h) — **catalyst requirement**

These need Stefan's actual backtested thresholds before Fas 1 finalizes swing_rules.py.

## Database Schema (SQLite)

```sql
tickers(id, symbol, name, exchange, market_cap, last_updated)
scans(id, timestamp, status, candidate_count)
scan_results(id, scan_id, ticker_id, gap_pct, volume, ema_100, above_ema_100, has_news, timestamp)
news_items(id, ticker_id, title, source, url, published_at, fetched_at)
ai_analyses(id, ticker_id, requested_at, prompt_version, response, usage_tokens, timestamp)
```

## Claude API Integration

- **Model**: `claude-opus-4-1` (on-demand, can switch to sonnet for cost savings)
- **Prompt**: Contextual — combines gap%, volume, EMA100, recent news, asks for 2–3 sentence swing trade assessment
- **Cost**: Per-token usage. Stefan should monitor via Anthropic console.
- **Cache**: Results stored in `ai_analyses` table. Re-run on demand.

## Frontend React Patterns

- **State Management**: React Query (tanstack) for server state, useState for UI state
- **Polling**: `refetchInterval` in useQuery hooks (30–60s for candidates, 10s for scan status)
- **API**: axios client at `src/api/client.ts`
- **Build**: Vite + TypeScript

## Testing Strategy

- **Backend**: pytest for screeners (rule logic), mocked yfinance/feedparser
- **Frontend**: Component smoke tests (optional, can skip MVP)
- **Integration**: Manual smoke test — trigger scan, verify data in SQLite, check dashboard
- **Pre-deploy**: Run in dev env against real pre-market data 1 day before prod push

## Deployment Flow (skzdev02)

1. **Dev Setup**:
   - Separate venv, .env, data/dev.db
   - Backend on port 8001, frontend on 5174 (don't conflict with prod)
   - `npm run dev` + `uvicorn app.main:app --reload --port 8001`

2. **Prod Setup**:
   - Backend: systemd unit (premarket-backend.service), venv at `/opt/premarket/venv`
   - Frontend: built dist/ served via nginx static
   - nginx reverse proxy: `/api/` → uvicorn 8000, `/` → dist/
   - Tailscale access: `premarket.tailscale:3000`

3. **Deploy Script**:
   - `deploy/deploy.sh` — git pull, pip install, npm build, systemctl restart
   - Run on skzdev02 as unprivileged user (create `premarket` user + group)

## Next Steps for Implementation

**Fas 0** (Setup) — ✓ Complete
**Fas 1** (Data Pipeline) — Start here
  - Confirm exact swing trading thresholds with Stefan
  - Implement collectors (universe, market_data, news_feed)
  - Implement screeners/swing_rules.py
  - Write basic tests

**Fas 2** (Backend API + Scheduler)
  - Implement all routers (candidates, stock, analyze, scan, news)
  - APScheduler integration in scheduler.py
  - Database write logic

**Fas 3** (Frontend Dashboard)
  - Complete React components
  - Polling + polling interval tuning
  - Error states + loading states

**Fas 4** (Deploy)
  - Set up systemd, nginx on skzdev02
  - Configure deploy script
  - Separate dev/prod instances

**Fas 5** (Polish)
  - GitHub Actions CI
  - Error handling for rate limits, API failures
  - README + deploy docs

## Important Notes

- **Tailscale**: App is private by design (no public internet). SKzdev02 is Tailscale-joined.
- **No Auth MVP**: Because Tailscale network is already private. Add JWT later if needed.
- **Hermes Separation**: This app is intentionally decoupled from Hermes Agents (which is experimental).
- **Cost**: Monitor Anthropic API usage (token-based billing). Consider Sonnet for cheaper on-demand analysis.
- **Rate Limiting**: yfinance has request limits. Top 10 tickers should be safe. Monitor if scaling to 500.

## Stefan's Preferences (from conversation)

- Keeps dev/prod separate via GitHub branches
- Prefers clean, working code over premature abstractions
- Will configure swing trading rules once seeing the system live
- Wants settings to be configurable later (e.g., TOP_N_TICKERS can move to UI settings)
- Interested in eventually extending to other strategies (currently swing trading only)
