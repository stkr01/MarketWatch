# Pre-Market Swing Trading Dashboard

A live dashboard for monitoring pre-market swing trading opportunities on US equities (NASDAQ/NYSE).

**Status**: MVP Phase 0 (Setup Complete)

## Features

- 📊 Real-time market scanning every 5 minutes during pre-market hours
- 🎯 Swing trading rule-based screening (gap%, volume, EMA100, news catalysts)
- 🤖 On-demand Claude AI analysis of candidates
- 📱 Live dashboard with polling updates
- 🔌 Tailscale private network access on skzdev02

## Tech Stack

- **Backend**: Python + FastAPI + SQLAlchemy + SQLite
- **Frontend**: React 18 + Vite + TypeScript
- **AI**: Anthropic Claude API
- **Data**: yfinance, feedparser, pandas
- **Scheduler**: APScheduler (pre-market scans)

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

## Development Checklist

### Fas 1 — Data Pipeline
- [ ] `collectors/universe.py` — Top 10 tickers
- [ ] `collectors/market_data.py` — gap%, volume, EMA100
- [ ] `collectors/news_feed.py` — feedparser integration
- [ ] `screeners/swing_rules.py` — rule implementation

### Fas 2 — Backend API + Scheduler
- [ ] `scheduler.py` — APScheduler 5-min jobs
- [ ] Implement all `/api` endpoints
- [ ] `ai/claude_analyzer.py` — Claude on-demand analysis

### Fas 3 — Frontend
- [ ] CandidateTable polling + rendering
- [ ] StockDetail drill-down
- [ ] AIAnalysisPanel Claude results
- [ ] ScanStatusBar UI

### Fas 4 — Deploy
- [ ] systemd unit file
- [ ] nginx reverse proxy config
- [ ] deploy.sh automation

### Fas 5 — Polish
- [ ] GitHub Actions CI
- [ ] Error handling
- [ ] README + docs

## Configuration

Key settings in `backend/app/config.py`:

- `TOP_N_TICKERS`: Number of tickers to scan (dev: 10, prod: 500)
- `SCAN_INTERVAL_MINUTES`: Frequency (default: 5 min)
- `GAP_THRESHOLD_PERCENT`: Min gap to trigger (default: 2%)
- `VOLUME_MULTIPLIER`: Volume spike threshold (default: 1.5x)
- `NEWS_LOOKBACK_HOURS`: Recent news window (default: 48h)

Override via `.env` file.

## Next Steps

1. **Setup Anthropic API key** — Get key from https://console.anthropic.com
2. **Confirm swing trading rules** — Gap%, volume, news thresholds
3. **Start Fas 1** — Implement data collectors
4. **Test locally** — Run backend + frontend in dev mode
5. **Deploy to skzdev02** — Follow deploy/DEPLOY.md

## License

Internal project
