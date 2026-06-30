# Local Development Guide

## Quick Start: Run Everything Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### Backend Setup (Terminal 1)

```bash
cd C:\Data\Pre-Market\backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies (already done, but for reference)
pip install -r requirements.txt

# Verify .env exists with API key
# The .env file should have:
# ANTHROPIC_API_KEY=sk-ant-api03-...

# Start backend server
uvicorn app.main:app --reload --port 8000
```

Server will start at: **http://localhost:8000**

Health check: `curl http://localhost:8000/health`

### Frontend Setup (Terminal 2)

```bash
cd C:\Data\Pre-Market\frontend

# Install dependencies (one time)
npm install

# Start dev server
npm run dev
```

Dashboard will be at: **http://localhost:5173**

Frontend auto-proxies API calls to `http://localhost:8000`

---

## Testing the Flow

### Step 1: Open Dashboard
- Go to **http://localhost:5173** in your browser
- You should see the Pre-Market Dashboard with:
  - 📊 Scan Status Bar (showing last scan time, next scan countdown)
  - 🎯 Candidates Table (empty until you trigger a scan)

### Step 2: Trigger a Scan
- Click **"🔄 Scan Now"** button
- Watch the backend (Terminal 1) logs as it:
  1. Fetches market data from yfinance (10 tickers)
  2. Gathers news from RSS feeds
  3. Screens against swing trading rules
  4. Saves results to SQLite

Scan takes **~10-15 seconds** to complete

### Step 3: View Candidates
- After scan completes, the **Candidates Table** will populate
- You'll see stocks that matched the screening rules:
  - 🟢 Green gap% = up movement
  - 🔴 Red gap% = down movement
  - 💚 Green volume = high volume spike
  - 📰 News indicator = recent news found

### Step 4: Click on a Candidate
- Click any "View" button to see stock details
- You'll see:
  - Stock name & exchange
  - Recent news (from CNBC, MarketWatch, Yahoo)
  - "🤖 Analyze" button

### Step 5: Run Claude AI Analysis
- Click **"🤖 Analyze"** button
- Claude will:
  - Analyze the gap, volume, EMA100 position
  - Review recent news for catalysts
  - Generate a 2-3 sentence swing trade recommendation

Results are cached for 5 minutes (refresh available)

---

## API Endpoints (for testing)

You can test endpoints directly:

```bash
# Health check
curl http://localhost:8000/health

# Trigger a scan (background job)
curl -X POST http://localhost:8000/api/scan

# Get scan status
curl http://localhost:8000/api/scan/status

# Get current candidates
curl http://localhost:8000/api/candidates

# Get stock details
curl http://localhost:8000/api/stock/AAPL

# Get news for a ticker
curl http://localhost:8000/api/news/AAPL

# Analyze a stock with Claude
curl -X POST http://localhost:8000/api/stock/AAPL/analyze
```

---

## Database

- **Location**: `backend/data/premarket.db` (SQLite)
- **Tables**:
  - `tickers` - stock universe
  - `scans` - scan records
  - `scan_results` - screening results
  - `news_items` - fetched news
  - `ai_analyses` - Claude analysis cache

View with any SQLite viewer:
```bash
# PowerShell example
sqlite3 backend/data/premarket.db "SELECT * FROM scans LIMIT 5;"
```

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.10+

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Check if port 8000 is in use
netstat -ano | findstr :8000
```

### Frontend won't connect to backend
- Check backend is running at `http://localhost:8000`
- Check CORS is enabled (it is by default)
- Open browser DevTools → Network tab → see API calls

### No candidates found
- Make sure scan completed (check backend logs)
- Check swing trading rule thresholds in `backend/app/config.py`:
  - `GAP_THRESHOLD_PERCENT`: 2.0%
  - `VOLUME_MULTIPLIER`: 1.5x
  - Lower these to get more candidates during testing

### Claude API fails
- Verify `.env` file has correct `ANTHROPIC_API_KEY`
- Check API key is valid: https://console.anthropic.com

---

## Development Tips

### Watch Logs
- **Backend**: Check Terminal 1 for detailed logging
- **Frontend**: Check browser DevTools Console

### Hot Reload
- **Backend**: Changes auto-reload (Uvicorn with `--reload`)
- **Frontend**: Changes auto-refresh (Vite dev server)

### Clear Database
```bash
# Remove database and let it be recreated
cd backend
rm -r data/
# Next scan will create new tables
```

### Check Database Contents
```bash
cd backend
venv\Scripts\python -c "
from app.db import SessionLocal
from app.models import Scan, ScanResult
db = SessionLocal()
scans = db.query(Scan).order_by(Scan.id.desc()).limit(5).all()
for s in scans:
    print(f'Scan {s.id}: {s.candidate_count} candidates at {s.timestamp}')
"
```

---

## Next Steps: Deploy to skzdev02

Once you've tested locally:

1. **Push to GitHub**
   ```bash
   git push origin development
   ```

2. **Create PR to main branch**

3. **Deploy to skzdev02** (Fas 4)
   - Set up systemd unit
   - Configure nginx
   - Run `deploy/deploy.sh`

---

## Performance Tips

- Frontend polls candidates every 30 seconds (configurable)
- Backend scans every 5 minutes during pre-market hours
- Claude analysis results cached for 5 minutes
- SQLite can handle 500+ tickers without issues
- For >500 stocks, consider PostgreSQL

---

## Questions?

Check `CLAUDE.md` for architecture details and `README.md` for feature overview.
