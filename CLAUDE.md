# Pre-Market Dashboard — AI Assistant Context

## Project Overview

**Krantz Pre-Market AI Dashboard** — a live, real-time monitoring tool for swing trading candidates (1–30 day holds) on US equities. Built for Stefan on skzdev02 (Azure VM, private Tailscale network). **Deployed & live at http://skzdev02:3000.** GitHub: `stkr01/MarketWatch`.

**Goal**: Replace daily email reports with a live dashboard that continuously scans for swing trading catalysts (gap%, volume, EMA100, news) and layers Claude AI on top.

**Status**: **Fas 0–4 complete (live on skzdev02)** + a Session-2 feature wave. See `PROJECT_STATUS.md` for the detailed state and `deploy/DEPLOYMENT.md` for the runbook.

**Implemented feature set** (beyond the original MVP):
- Technical indicators: RSI(14), ATR(14)/ATR%, RVOL (`market_data.py`, stored on `scan_results`)
- DB-backed **watchlist** (`Ticker.is_active`) — scan universe user-managed via `/api/watchlist`
- **Candidate outcome tracking** — +1d/+1w returns, win rate (`candidate_outcomes`, `outcomes.py`)
- **US economic calendar** — faireconomy/ForexFactory feed, today's USD events (`collectors/economic_calendar.py`)
- **AI Morning Briefing** — Claude summary of candidates + calendar, cached daily (`ai/briefing.py`)
- **Live pre-market gap** (intraday `prepost` quotes) + **Telegram/Discord alerts** on strong candidates
- **Ticker tape** (indices incl. DAX/FTSE + FX + watchlist) and **world-clock banner** (Sto/London/NY/Tokyo, session-coloured)
- **Charts** — inline-SVG sparklines in the table + intraday price chart in the detail view
- **AI trade tools** — "why is it gapping?" + ATR-based trade-plan (entry/stop/target at 2R)
- **Market Movers** — auto-discovery via Yahoo screeners, one-click add-to-watchlist
- **News Analyser** — URL/text → Swedish summary + affected assets + 1–5 impact score (trafilatura + Claude)
- UX: click any ticker → in-app detail (not Yahoo); top ActionBar; alerts as a header bell widget

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
  • market_data.py — yfinance: gap%, volume, EMA100, RSI(14), ATR(14), RVOL
  • news_feed.py — Yahoo per-ticker RSS: recent news per ticker
  • universe.py — DB watchlist (Ticker.is_active), seeded with 10 defaults
    ↓
screeners/swing_rules.py — filter by rules (gap/volume/news)
    ↓
Database (scan_results incl. is_candidate, news_items, candidate_outcomes)
    ↓
Frontend polls every 30–60s
    ↓
User clicks "Analyze" → ai/claude_analyzer.py → Claude API → ai_analyses
Morning briefing → ai/briefing.py (candidates + economic_calendar) → briefings
Outcome tracking → outcomes.py evaluates +1d/+1w returns of past candidates
```

## Key Files & Paths

### Backend
- `backend/app/main.py` — FastAPI entry point (create_all + `ensure_schema()` + `seed_default_watchlist()` on startup)
- `backend/app/config.py` — Environment-based configuration
- `backend/app/db.py` — engine/session + `ensure_schema()` idempotent SQLite column migrations
- `backend/app/models.py` — ORM (Ticker, Scan, ScanResult, NewsItem, AIAnalysis, CandidateOutcome, Briefing)
- `backend/app/routers/` — REST endpoints: candidates, stock, analyze, scan, news, economic, watchlist, outcomes, briefing, alerts, settings, **ticker_tape**, **charts**, **movers**, **news_analyze**
- `backend/app/collectors/` — market_data (indicators), news_feed (Yahoo RSS), universe (DB watchlist), economic_calendar, **ticker_tape** (banner quotes), **chart_data** (intraday + sparklines), **movers** (Yahoo screeners), **article** (URL → text via trafilatura)
- `backend/app/screeners/swing_rules.py` — Rule-based filtering
- `backend/app/outcomes.py` — candidate outcome recording + return evaluation
- `backend/app/alerts.py` — strong-candidate alerts (Telegram/Discord, per-day dedup)
- `backend/app/ai/claude_analyzer.py` — per-ticker analysis + `explain_gap` + `generate_trade_plan`
- `backend/app/ai/briefing.py` — Claude morning briefing generator
- `backend/app/ai/news_analyzer.py` — news article → summary + affected assets + score
- `backend/app/scheduler.py` — APScheduler job setup

### Frontend
- `frontend/src/pages/Dashboard.tsx` — Main page (header+clock+AlertsBell, TickerTape, MarketClocks, ActionBar, briefing, stat bar, 2-col grid, NewsAnalyzerModal); shared `selectTicker` opens the in-app detail
- `frontend/src/components/` — CandidateTable(+Sparkline), StockDetail(+PriceChart+TradeTools), AIAnalysisPanel, ScanStatusBar, MarketClock, EconomicCalendar, Watchlist, ScreenerPerformance, BriefingCard, **TickerTape**, **MarketClocks**, **Sparkline**, **PriceChart**, **TradeTools**, **MarketMovers**, **ActionBar**, **NewsAnalyzerModal**, **AlertsBell**
- `frontend/src/utils.ts` — `yahooUrl()`, `marketSession()`, `rsiZone()`, `priceSourceBadge()`
- `frontend/src/api/client.ts` — Axios API client
- `frontend/src/index.css` — dark/glassmorphism theme
- `frontend/vite.config.ts` — Dev proxy to localhost:8000

### Deploy (live)
- `deploy/skzdev02/premarket-backend.service` — systemd unit (uvicorn on 127.0.0.1:8000)
- `deploy/skzdev02/premarket.conf` — nginx site, port 3000, `/api` reverse proxy
- `deploy/deploy.sh` — redeploy script (pull, deps, build, restart, reload nginx)
- `deploy/DEPLOYMENT.md` — full one-time setup + redeploy runbook

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

- **Model**: `claude-opus-4-8` across all AI features (per-ticker analysis, morning briefing, gap explanation, trade-plan, news analysis). Could switch to a Sonnet model for cost savings on high-volume features.
- **AI features**: (1) per-ticker analysis, (2) morning briefing, (3) "why is it gapping?", (4) ATR-based trade-plan commentary, (5) News Analyser (Swedish summary + affected assets + 1–5 score). Each on-demand button shows token usage.
- **Cost**: Per-token usage; monitor via the Anthropic console. Every AI action costs tokens.
- **Cache**: Per-ticker analysis cached in `ai_analyses`; briefing cached daily in `briefings`. Trade-plan/why/news are computed on demand (not persisted yet).

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

> Detailed, current state + resume guide live in `PROJECT_STATUS.md`.

**Fas 0–3** (Setup, Pipeline, API+Scheduler, Frontend) — ✓ Complete
**Enhancements** (indicators, watchlist, outcomes, economic calendar, AI briefing, redesign) — ✓ Complete
**Live pre-market gap + alerts** — ✓ Complete (07-03)
**Fas 4** (Deploy to skzdev02) — ✓ **Complete (07-04)**, live at http://skzdev02:3000
**Session-2 feature wave** — ✓ Complete (07-04/05): ticker tape, world clocks, charts, AI trade tools, market movers, news analyser, click-to-detail, action bar, alerts bell

**Next / backlog**
  - News Analyser history (persist analyses with date/time) — agreed "step two"
  - Futures in the tape (`ES=F`/`NQ=F`); paper-trading / position log
  - Auto-analyze all candidates; earnings-date proximity; more news sources
  - GitHub Actions CI; JWT auth for off-Tailscale access

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
