# Krantz Pre-Market AI Dashboard

A live dashboard for monitoring pre-market swing trading opportunities on US equities (NASDAQ/NYSE), with Claude AI layered on top.

**Status**: ✅ **Live on skzdev02** — http://skzdev02:3000 (Tailscale). GitHub: `stkr01/MarketWatch`.

## Features

- 📈 **Ticker tape** — indices (S&P 500, Nasdaq, Dow, Russell 2000, DAX, FTSE 100, VIX), EUR/USD, and your watchlist, live
- 🕐 **World clocks** — Stockholm / London / New York / Tokyo, colour-coded by session (open / pre-market / closed)
- 📊 Real-time scanning every 5 min during pre-market; rule-based screening (gap%, volume, EMA100, news)
- 📉 **Charts** — sparklines in the candidate table + intraday price chart (pre/after-hours shaded) in the detail view
- 🤖 **Claude AI** — per-ticker analysis, morning briefing, "why is it gapping?", ATR-based trade-plan
- 🔥 **Market Movers** — auto-discovers movers beyond your watchlist (Yahoo screeners), one-click add
- 📰 **News Analyser** — paste a URL → Swedish AI summary + affected assets + 1–5 impact score
- 🔔 Telegram/Discord **alerts** on strong candidates (compact header bell)
- 📊 Candidate outcome tracking (+1d/+1w returns, win rate) + AI morning briefing
- 🔌 Tailscale private network access on skzdev02

## Tech Stack

- **Backend**: Python + FastAPI + SQLAlchemy + SQLite
- **Frontend**: React 18 + Vite + TypeScript + TanStack Query
- **AI**: Anthropic Claude API (`claude-opus-4-8`)
- **Data**: yfinance, feedparser, trafilatura, pandas
- **Scheduler**: APScheduler (pre-market scans)
- **Deploy**: systemd + nginx on skzdev02 (see `deploy/DEPLOYMENT.md`)

## Quick Start (Development)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Copy and configure env
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run server
python -m uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard runs at `http://localhost:5173`

API calls proxy to `http://localhost:8000`

## Project Structure

```
.
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── routers/     # REST endpoints
│   │   ├── collectors/  # Market data, news collection
│   │   ├── screeners/   # Trading rule screening
│   │   ├── ai/          # Claude analysis
│   │   └── scheduler.py # APScheduler jobs
│   └── requirements.txt
├── frontend/             # React dashboard
│   ├── src/
│   │   ├── pages/       # Dashboard page
│   │   ├── components/  # UI components
│   │   └── api/         # API client
│   └── package.json
└── deploy/              # Deployment configs for skzdev02
```

## Status Checklist

- [x] **Fas 1** — Data pipeline (universe, market_data, news_feed, swing_rules)
- [x] **Fas 2** — Backend API + APScheduler + Claude analysis
- [x] **Fas 3** — Frontend dashboard (table, detail, AI panel, status bar)
- [x] **Enhancements** — indicators, watchlist, outcomes, economic calendar, briefing
- [x] **Live gap + alerts** — intraday pre-market gap, Telegram/Discord alerts
- [x] **Fas 4** — Deploy to skzdev02 (systemd + nginx, live at :3000)
- [x] **Feature wave** — ticker tape, world clocks, charts, AI trade tools, market movers, news analyser
- [ ] News Analyser history (persist with date/time); futures in tape; paper-trading; CI

See `PROJECT_STATUS.md` for the detailed, current state and `deploy/DEPLOYMENT.md` for the deploy runbook.

## Configuration

Key settings in `backend/app/config.py`:

- `TOP_N_TICKERS`: Number of tickers to scan (dev: 10, prod: 500)
- `SCAN_INTERVAL_MINUTES`: Frequency (default: 5 min)
- `GAP_THRESHOLD_PERCENT`: Min gap to trigger (default: 2%)
- `VOLUME_MULTIPLIER`: Volume spike threshold (default: 1.5x)
- `NEWS_LOOKBACK_HOURS`: Recent news window (default: 48h)

Override via `.env` file.

## Deployment

Live on **skzdev02** (Ubuntu, Tailscale): nginx serves the built frontend on port
**3000** and reverse-proxies `/api` to the backend (uvicorn on `127.0.0.1:8000`,
systemd unit `premarket-backend`). Redeploy after pushing to `main`:

```bash
ssh -i C:\dev\keys\skzdev02_key adminskz@100.94.139.84
bash /opt/premarket/deploy/deploy.sh   # pull, deps, build, restart, reload nginx
```

Full one-time setup + redeploy details in [`deploy/DEPLOYMENT.md`](deploy/DEPLOYMENT.md).

## License

Internal project
