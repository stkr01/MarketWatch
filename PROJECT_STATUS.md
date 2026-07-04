# Krantz Pre-Market AI Dashboard - Project Status

**Last Updated:** 2026-07-05
**Status:** **LIVE on skzdev02** ✅ — Fas 0–4 complete + Session-2 feature wave (charts, AI trade tools, market movers, news analyser, world clocks)
**Branch:** `main` (deployed) · GitHub: `stkr01/MarketWatch`

---

## 🌐 Live deployment (read this first)

**Dashboard:** http://skzdev02:3000 (Tailscale) — nginx on :3000 serves the built
frontend and reverse-proxies `/api` to the backend on `127.0.0.1:8000`.

- **Server:** skzdev02 (Ubuntu 24.04 Azure VM, Tailscale). SSH: `ssh -i C:\dev\keys\skzdev02_key adminskz@100.94.139.84`.
- **Code:** `/opt/premarket` (git clone). Backend systemd unit `premarket-backend` (uvicorn, enabled). DB: `/opt/premarket/data/premarket.db`. Secrets: `/opt/premarket/backend/.env` (`DEBUG=false` → scan every 5 min, 04:00–09:30 ET, Mon–Fri). Telegram alerts configured; Discord empty.
- **Redeploy after pushing to `main`:** SSH in and run `bash /opt/premarket/deploy/deploy.sh` (pull, deps, rebuild frontend, restart backend, reload nginx). Full runbook: `deploy/DEPLOYMENT.md`.

**Local dev:**
```powershell
# backend (window 1)
cd C:\Data\Pre-Market\backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000
# frontend (window 2)
cd C:\Data\Pre-Market\frontend; npm run dev   # http://localhost:5173
```
Notes:
- Set `DEBUG=true` in local `backend/.env` to scan every minute (auto-populates candidates).
- DB migrations run automatically on startup (`ensure_schema()`), patched in place — no data loss.
- New backend dependency this session: **`trafilatura`** (news article extraction).

---

## 📊 Project Overview

**Goal:** Live dashboard for swing trading (1–30 day holds) on US equities, replacing daily email reports.
**Server:** skzdev02 (Azure VM, private Tailscale network) — **deployed & live**
**Architecture:** Python FastAPI backend + React frontend + SQLite database
**Key Feature:** Real-time market scanning + Claude AI (analysis, morning briefing, trade plans, news analysis)

---

## 🆕 Session 2026-07-04/05 — Deploy + feature wave

**Deployed to skzdev02 (Fas 4).** Repo cloned to `/opt/premarket`, Python 3.12 venv,
systemd unit + nginx site on port 3000, prod `.env` (secrets copied from local),
frontend built. Redeploys via `deploy/deploy.sh`. Runbook in `deploy/DEPLOYMENT.md`.

**New features (all built, tested, deployed):**
- **📈 Ticker tape** — scrolling top banner: indices (S&P 500, Nasdaq, Dow, Russell 2000, **DAX `^GDAXI`**, **FTSE 100 `^FTSE`**, VIX), EUR/USD, and the full watchlist with live price + change. Two batched yfinance calls, 60s stale-while-revalidate cache. (`collectors/ticker_tape.py`, `routers/ticker_tape.py`, `components/TickerTape.tsx`)
- **🕐 World clocks banner** — Stockholm / London / New York / Tokyo, live local time + countdown to open / time-since-open, colour-coded by session (**green open / orange pre-market / red closed**). Pure client-side. (`components/MarketClocks.tsx`)
- **📊 Charts** — dependency-free inline-SVG **sparklines** in a new "Trend" column and an **intraday price chart** in the detail view (pre/after-hours shading, prev-close line, H/L/last legend). (`collectors/chart_data.py`, `routers/charts.py`, `components/Sparkline.tsx`, `components/PriceChart.tsx`)
- **🎯 AI trade tools** — in the detail view: **"Varför gappar den?"** (Claude explains the likely catalyst) and **"Trade-plan"** (ATR-based entry/stop/target at 2R + Claude commentary). (`ai/claude_analyzer.py` +`explain_gap`/`generate_trade_plan`, `routers/analyze.py`, `components/TradeTools.tsx`)
- **🔥 Market Movers** — auto-discovers movers beyond the watchlist via Yahoo screeners (day_gainers/losers/most_actives/small_cap_gainers), session-aware change% + RVOL, one-click "+ watchlist". (`collectors/movers.py`, `routers/movers.py`, `components/MarketMovers.tsx`)
- **📰 News Analyser** — paste a URL (or text) → **Swedish AI summary**, overall market impact, and up to 6 **affected assets** each with direction + **1–5 impact score**, cross-referenced against the watchlist. Article extraction via requests+**trafilatura** (browser UA), 422 → paste-text fallback. (`collectors/article.py`, `ai/news_analyzer.py`, `routers/news_analyze.py`, `components/NewsAnalyzerModal.tsx`)
- **UX** — clicking any ticker now opens the **in-app detail** (not Yahoo) and scrolls to it. Top **ActionBar** (Scan Now moved here + News Analyser button; trace light on hover only). Alerts moved from the sidebar to a compact **bell + popover** next to the header clock. Header clock stripped to just time/date. Title → **"Krantz Pre-Market AI Dashboard"**. Sidebar reordered (Screener Performance → Economic Calendar → Movers → Settings → Watchlist).

---

## 🆕 Session 2026-07-03 — What we added

- **Live pre-market gap pricing** — gap% now measured against the latest *real* intraday trade (incl. pre/post-market, 1-min bars, `prepost=True`) vs. the prior regular-session close, instead of yesterday's daily open. Addresses the top backlog item + main known limitation. `market_data.py`: `_get_intraday_snapshot()`, `_classify_session()`, `_previous_regular_close()`; new `previous_close` / `pre_market_price` / `price_source` fields (DB auto-migrated). Frontend shows PRE/POST/LIVE/EOD badges + "vs $X close". Toggle with `USE_PREMARKET_DATA` (default true).
- **Push alerts** — notify on *strong* candidates (a screened candidate that also clears tighter thresholds: `ALERT_GAP_THRESHOLD_PERCENT` default 4%, `ALERT_RVOL_THRESHOLD` default 2.0). Channels: **Telegram** (bot token + chat id) and **Discord** (webhook URL). Deduped one-per-symbol-per-ET-day so the every-few-minutes scheduler doesn't spam. New `alerts_sent` table, `alerts.py` service, `/api/alerts` (config + recent) + `/api/alerts/test`. Sidebar "🔔 Alerts" panel with live status + Test button. No-ops safely when no channel is configured. Verified: strong/weak filtering, dispatch, dedup, DB recording (mocked channel) all pass.

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
- **Enhancements (07-01/02)** — indicators, watchlist, outcome tracking, economic calendar, AI briefing, redesign ✅
- **Live pre-market gap + alerts (07-03)** — real intraday gap, Telegram/Discord alerts ✅
- **Fas 4** Deploy to skzdev02 — **DONE (07-04)** ✅ live at http://skzdev02:3000
- **Session-2 feature wave (07-04/05)** — ticker tape, world clocks, charts/sparklines, AI trade tools, market movers, news analyser, click-to-detail, action bar, alerts bell ✅

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
| GET  | `/api/alerts` · POST `/api/alerts/test` | Alert config + recent sent alerts; send test notification |
| GET/PATCH | `/api/settings` | Runtime-adjustable thresholds (screening & alert gap %), live-editable from UI |
| GET  | `/api/ticker-tape` | Indices + FX + watchlist quotes for the scrolling banner — **07-04** |
| GET  | `/api/sparklines` | Downsampled intraday series per watchlist symbol (table sparklines) — **07-04** |
| GET  | `/api/stock/{ticker}/history` | Intraday 1-min series (incl. pre/post) for the detail chart — **07-04** |
| POST | `/api/stock/{ticker}/why` | Claude explains the likely gap catalyst — **07-04** |
| POST | `/api/stock/{ticker}/trade-plan` | ATR-based entry/stop/target (2R) + Claude plan — **07-04** |
| GET  | `/api/movers` | Auto-discovered movers (Yahoo screeners), watchlist-flagged — **07-04** |
| POST | `/api/news/analyze` | URL/text → Swedish summary + affected assets + 1–5 impact score — **07-04** |

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
alerts_sent†(id, symbol, scan_id, gap_pct, rvol, price, price_source,
             channels, message, status, sent_at)
```
`*` = added in the 07-01/02 session (auto-migrated via `ensure_schema()`).
`†` = added 07-03 (new table, created by `create_all`). `scan_results` also gained
`previous_close` / `pre_market_price` / `price_source` (auto-migrated).

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
- `alerts.py` — **strong-candidate alerts (Telegram/Discord webhooks, per-day dedup)**
- `runtime_config.py` — **live-editable thresholds (DB-backed overrides of env defaults)**
- `collectors/` — `universe.py` (DB watchlist + seed), `market_data.py` (yfinance + RSI/ATR/RVOL), `news_feed.py` (Yahoo per-ticker RSS), `economic_calendar.py`, **`ticker_tape.py`** (banner quotes), **`chart_data.py`** (intraday history + sparklines), **`movers.py`** (Yahoo screeners), **`article.py`** (URL → article text via trafilatura)
- `screeners/swing_rules.py` — gap/volume/news filtering
- `ai/` — `claude_analyzer.py` (per-ticker analysis + **`explain_gap`** + **`generate_trade_plan`**), `briefing.py` (morning briefing), **`news_analyzer.py`** (news → summary/assets/score)
- `routers/` — candidates, stock, analyze, scan, news, economic, watchlist, outcomes, briefing, alerts, settings, **ticker_tape**, **charts**, **movers**, **news_analyze**

### Frontend (`frontend/src/`)
- `pages/Dashboard.tsx` — layout (header+clock+**AlertsBell**, **TickerTape**, **MarketClocks**, **ActionBar**, briefing, stat bar, 2-col grid, detail, **NewsAnalyzerModal**); shared `selectTicker` opens the in-app detail
- `components/` — CandidateTable (+ Sparkline column), StockDetail (+ PriceChart + TradeTools), ScanStatusBar, AIAnalysisPanel, MarketClock, EconomicCalendar, Watchlist, ScreenerPerformance, BriefingCard, **TickerTape**, **MarketClocks**, **Sparkline**, **PriceChart**, **TradeTools**, **MarketMovers**, **ActionBar**, **NewsAnalyzerModal**, **AlertsBell** _(AlertsPanel retired to the bell)_
- `api/client.ts` — axios client (`/api` proxied to :8000)
- `utils.ts` — `yahooUrl()`, `marketSession()`, `rsiZone()`, `priceSourceBadge()`
- `index.css` — dark/glassmorphism theme (+ tape, clocks, charts, movers, modal, bell styles)

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
- ~~**Gap is not live pre-market**~~ ✅ fixed (07-03) — now uses yfinance 1-min bars with `prepost=True` (last real trade vs prior regular close). Note: yfinance pre-market intraday can be delayed/sparse for thin names; a paid feed (Finnhub/Polygon/Alpaca) would be more robust.
- Outcome returns are approximate (daily-close based, trading-day offsets).
- `/api/scan/status` `is_running` is hardcoded `false`.
- CORS `allow_origins=["*"]` + `allow_credentials=True` is technically invalid (harmless now, no cookies).
- Deprecations: `datetime.utcnow()`, Pydantic `from_orm()` — still work, emit warnings.
- Dev DEBUG mode scans every minute → yfinance rate-limit risk + manual scan can overlap scheduler.

**Feature backlog**
- ~~Push/Telegram/Discord alerts on strong candidates~~ ✅ done (07-03)
- ~~Real pre-market gap data~~ ✅ done (07-03)
- ~~Structured AI output (entry/stop/target as fields)~~ ✅ done (07-04, trade-plan)
- ~~Sparklines / intraday charts~~ ✅ done (07-04)
- ~~Broad auto-discovery of movers beyond the watchlist~~ ✅ done (07-04, Market Movers)
- ~~News analysis (summary + affected assets + impact)~~ ✅ done (07-04, News Analyser)
- **News Analyser history** — persist analyses (URL, summary, assets, scores, date/time) + history view _(agreed "step two")_
- Auto-analyze all candidates (not just on-demand)
- Earnings-date proximity flag; more news sources; sector heatmap
- Futures (`ES=F`/`NQ=F`) in the tape; paper-trading / position log
- Scan history view + real scan status; WebSockets instead of polling
- JWT auth for off-Tailscale access

---

## 🚀 Next Steps

App is deployed and live.

**⭐ Agreed for next session (2026-07-06):**
1. **News Analyser history** ("step two") — a `news_analyses` table (URL, title, summary, assets JSON, scores, **created_at date/time**) + a history view to browse past analyses.
2. **Futures in the tape** (`ES=F`/`NQ=F`) — quick win, shows pre-market direction.

Then, from the backlog:
- **Paper-trade / position log** tied to the outcome tracking.
- Sorting/filtering in the candidate table.

**Deploy note:** `deploy/deploy.sh` needs `+x` on the server (git didn't preserve the
exec bit); it's currently `chmod +x`'d there. Run it as `bash deploy/deploy.sh` if in doubt.

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
