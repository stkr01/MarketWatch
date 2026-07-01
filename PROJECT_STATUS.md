# Pre-Market Swing Trading Dashboard - Project Status

**Last Updated:** 2026-07-02
**Status:** Fas 0-3 + Dashboard Enhancements COMPLETE ✅ — Fas 4 (deploy) still pending
**Active branch:** `feature/dashboard-enhancements` (commit `5cc95e3`, not yet merged to `main`/`master`)

---

## ⚡ Resume Tomorrow (read this first)

**Start backend** (PowerShell window 1):
```powershell
cd C:\Data\Pre-Market\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Start frontend** (PowerShell window 2):
```powershell
cd C:\Data\Pre-Market\frontend
npm run dev
```

Open **http://localhost:5173** (Vite jumps to 5174 if 5173 is busy).

Notes:
- `backend/.env` has `DEBUG=true` → scheduler scans **every minute** (auto-populates candidates; no need to click "Scan Now"). Set `DEBUG=false` for the prod-style schedule (every 5 min, 04:00–09:30 ET, Mon–Fri).
- DB migrations run automatically on startup (`ensure_schema()`), so the existing `data/premarket.db` is patched in place — no data loss.
- All local testing passed: `python test_pipeline_local.py` → 7/7; `npm run build` → clean.

**Git:** work is committed on `feature/dashboard-enhancements`. Not pushed, not merged. To continue: `git checkout feature/dashboard-enhancements`.

---

## 📊 Project Overview

**Goal:** Live dashboard for swing trading (1–30 day holds) on US equities, replacing daily email reports.
**Target Server:** skzdev02 (Azure VM, private Tailscale network)
**Architecture:** Python FastAPI backend + React frontend + SQLite database
**Key Feature:** Real-time market scanning + Claude AI on-demand analysis + AI morning briefing

---

## 🆕 Session 2026-07-01/02 — What we added

### Backend correctness fixes
1. **Screened candidates now persist & filter correctly** — added `ScanResult.is_candidate`; pipeline flags it; `/api/candidates` filters on it. (Previously the endpoint returned *all* scanned tickers, not just those passing the rules.)
2. **News feed rewritten** — now uses Yahoo Finance **per-ticker RSS** (`.../rss/2.0/headline?s=SYMBOL`) instead of fragile substring matching in generic feeds. Reliable catalyst detection (~20 items/ticker vs ~0 before).
3. **EMA100 data window** widened `3mo → 1y` (100-day EMA needs >100 trading days).
4. **Claude model** updated `claude-opus-4-1 → claude-opus-4-8`.
5. **Lightweight migrations** — `db.ensure_schema()` adds new columns to the SQLite dev DB idempotently on startup.

### New features (all 4 requested, built + verified)
- **A · Technical indicators** — RSI(14, Wilder), ATR(14) + ATR%, RVOL computed in `market_data.py`, stored on `scan_results`, surfaced in the candidate table (RSI column, RVOL bar) and a new metric strip in the detail view.
- **B · Watchlist** — DB-backed scan universe (`Ticker.is_active`). Seeded with the default 10. Add/remove via `/api/watchlist` (yfinance-validated on add). Sidebar UI with chips.
- **C · Candidate outcome tracking** — `candidate_outcomes` table records each flagged candidate; lazy+throttled evaluation computes **+1 day / +1 week** returns (trading-day based). `/api/outcomes` returns win rate + avg return. "Screener Performance" sidebar panel.
- **D · AI Morning Briefing** — `ai/briefing.py` has Claude summarize candidates + economic calendar into a morning game plan. Cached one-per-day in `briefings`. `/api/briefing` (GET cached) + `/api/briefing/generate` (POST). Card at top of dashboard.

### Also new
- **US Economic Calendar** — `collectors/economic_calendar.py` pulls the free faireconomy/ForexFactory weekly JSON, filters USD + today (US/Eastern), 15-min cache. `/api/economic-calendar`. Sidebar panel with impact color-coding + time.
- **Frontend redesign** — glassmorphism dark theme, live ET market clock + session pill (Pre-Market/Open/After Hours/Closed), stat tiles, richer table, **Yahoo Finance links** on every ticker (`finance.yahoo.com/quote/SYMBOL`), spinners/animations.

---

## ✅ Completed Work (cumulative)

- **Fas 0** Project setup — FastAPI + SQLAlchemy + SQLite, React + Vite + TS ✅
- **Fas 1** Data pipeline — collectors, screeners, `pipeline.py`, `scheduler.py` ✅
- **Fas 2** Backend API — all REST endpoints, DB writes, Claude integration ✅
- **Fas 3** React frontend — dashboard, polling, components ✅
- **Enhancements (this session)** — indicators, watchlist, outcome tracking, economic calendar, AI briefing, redesign ✅
- **Fas 4** Deploy to skzdev02 — **NOT STARTED** (files scaffolded in `deploy/`)

---

## 🔌 API Endpoints (current)

| Method | Path | Purpose |
|---|---|---|
| GET  | `/health` | Health check |
| GET  | `/api/candidates` | Screened candidates from latest scan (filtered by `is_candidate`) |
| GET  | `/api/stock/{ticker}` | Ticker metadata |
| GET  | `/api/stock/{ticker}/scan` | Latest scan metrics (gap, RVOL, RSI, ATR, EMA) — **new** |
| GET  | `/api/news/{ticker}` | Recent news |
| POST | `/api/stock/{ticker}/analyze` | Claude on-demand analysis |
| POST | `/api/scan` | Manual scan trigger (background thread) |
| GET  | `/api/scan/status` | Scan status + next run |
| GET  | `/api/economic-calendar` | Today's USD economic events — **new** |
| GET/POST/DELETE | `/api/watchlist` (+`/{symbol}`) | Manage scan universe — **new** |
| GET  | `/api/outcomes` | Screener performance (win rate, returns) — **new** |
| GET  | `/api/briefing` · POST `/api/briefing/generate` | AI morning briefing — **new** |

---

## 💾 Database Schema (SQLite)

```sql
tickers(id, symbol, name, exchange, market_cap, is_active*, last_updated)
scans(id, timestamp, status, candidate_count)
scan_results(id, scan_id, ticker_id, gap_pct, volume, volume_avg_20, rvol*,
             price, ema_100, above_ema_100, rsi_14*, atr_14*, atr_pct*,
             has_news, is_candidate*, timestamp)
news_items(id, ticker_id, title, source, url, summary, published_at, fetched_at)
ai_analyses(id, ticker_id, requested_at, prompt_version, response, usage_tokens, timestamp)
candidate_outcomes*(id, ticker_id, scan_id, symbol, flagged_at, entry_price,
             price_1d, return_1d_pct, evaluated_1d,
             price_1w, return_1w_pct, evaluated_1w)
briefings*(id, date, content, generated_at, usage_tokens)
```
`*` = added this session (auto-migrated via `ensure_schema()`).

---

## 📁 Key Files

### Backend (`backend/app/`)
- `main.py` — FastAPI entry; `create_all` + `ensure_schema()` + `seed_default_watchlist()` on startup
- `config.py` — env-based config (thresholds, model, ports)
- `db.py` — engine, session, **`ensure_schema()` migrations**
- `models.py` — ORM (Ticker, Scan, ScanResult, NewsItem, AIAnalysis, **CandidateOutcome**, **Briefing**)
- `schemas.py` — Pydantic response models
- `pipeline.py` — scan orchestration (+ records candidate outcomes)
- `scheduler.py` — APScheduler (every min in DEBUG, 5-min pre-market in prod)
- `outcomes.py` — **candidate outcome record + evaluate service**
- `collectors/` — `universe.py` (DB watchlist + seed), `market_data.py` (yfinance + **RSI/ATR/RVOL**), `news_feed.py` (**Yahoo per-ticker RSS**), **`economic_calendar.py`**
- `screeners/swing_rules.py` — gap/volume/news filtering
- `ai/` — `claude_analyzer.py` (per-ticker), **`briefing.py`** (morning briefing)
- `routers/` — candidates, stock, analyze, scan, news, **economic**, **watchlist**, **outcomes**, **briefing**

### Frontend (`frontend/src/`)
- `pages/Dashboard.tsx` — layout (header+clock, briefing, stat bar, 2-col grid, detail)
- `components/` — CandidateTable, StockDetail, ScanStatusBar, AIAnalysisPanel, **MarketClock**, **EconomicCalendar**, **Watchlist**, **ScreenerPerformance**, **BriefingCard**
- `api/client.ts` — axios client (`/api` proxied to :8000)
- `utils.ts` — **`yahooUrl()`, `marketSession()`, `rsiZone()`**
- `index.css` — redesigned dark/glassmorphism theme

---

## 🎯 Swing Trading Rules (config.py / .env)

- **Gap %:** ±2.0% (`GAP_THRESHOLD_PERCENT`)
- **Volume:** 1.5× 20-day avg (`VOLUME_MULTIPLIER`) — this is effectively the RVOL filter
- **News:** ≥1 recent item, last 48h (`NEWS_LOOKBACK_HOURS`) — **required catalyst**
- **EMA100 / RSI / ATR:** informational (shown, not hard filters)
- **Universe:** DB watchlist (`is_active`), seeded with 10 liquid names

---

## 🐛 Known Limitations / Backlog

**Limitations**
- **Gap is not live pre-market** — it's today's daily open vs yesterday's close (yfinance daily bars). Real pre-market quotes need a source like Finnhub/Polygon/Alpaca.
- Outcome returns are approximate (daily-close based, trading-day offsets).
- `/api/scan/status` `is_running` is hardcoded `false`.
- CORS `allow_origins=["*"]` + `allow_credentials=True` is technically invalid (harmless now, no cookies).
- Deprecations: `datetime.utcnow()`, Pydantic `from_orm()` — still work, emit warnings.
- Dev DEBUG mode scans every minute → yfinance rate-limit risk + manual scan can overlap scheduler.

**Feature backlog (brainstormed, not yet built)**
- Push/Telegram/Discord alerts on strong candidates
- Auto-analyze all candidates (not just on-demand)
- Structured AI output (rating + entry/stop/target as fields)
- News sentiment scoring; earnings-date proximity; more sources
- Sparklines / candlestick charts; sector heatmap
- Scan history view + real scan status; WebSockets instead of polling
- Trade journal; paper-trading (Alpaca); JWT auth for off-Tailscale access

---

## 🚀 Next Steps

**Option 1 — Fas 4 Deploy to skzdev02** (original plan)
- systemd unit + nginx reverse proxy + `deploy/deploy.sh` (scaffolds exist in `deploy/`)
- Set prod `.env` (`DEBUG=false`, real `ANTHROPIC_API_KEY`), data dir `/opt/premarket/data/`
- Est. 1–2 h

**Option 2 — Merge & keep building features**
- Merge `feature/dashboard-enhancements` → `main`/`master`
- Pick from the backlog above (alerts and real pre-market data are highest value)

---

## 🔐 Security Notes
- `.env` is gitignored (verified not tracked); never commit API keys.
- No auth for MVP (Tailscale private network). Add JWT before any public exposure.

---

## 📞 Quick Troubleshooting
- **Port 8000 in use** → a backend is already running (likely your `--reload` server, which auto-picks up code changes). Check `curl http://localhost:8000/health`.
- **Frontend on 5174** → 5173 was busy; both work.
- **No candidates** → check backend logs; try lowering `GAP_THRESHOLD_PERCENT`; ensure a scan ran.
- **Briefing/analysis fails** → verify `ANTHROPIC_API_KEY` in `backend/.env`.
- **New column errors** → `ensure_schema()` runs on startup; if bypassing `main.py`, call it manually (see `test_pipeline_local.py`).
