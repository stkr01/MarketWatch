# Deploying Pre-Market Dashboard to skzdev02

Target: **skzdev02** (Azure VM, Ubuntu 24.04, private Tailscale network).
Runs alongside other apps (linkportal, md-editor, todo-app) — this deploy uses
**dedicated free ports** and its own nginx site + systemd service, so it never
touches them.

| Component | Where | Port |
|---|---|---|
| Backend (FastAPI/uvicorn) | `127.0.0.1:8000` (localhost only) | 8000 |
| Frontend (nginx static + `/api` proxy) | Tailscale iface | **3000** |
| Database | `/opt/premarket/data/premarket.db` (SQLite) | — |

SSH: `ssh -i C:\dev\keys\skzdev02_key adminskz@100.94.139.84`

---

## One-time setup

Run these on skzdev02. `<REPO_URL>` = your private GitHub repo (e.g.
`git@github.com:skrantz71/premarket-dashboard.git`).

```bash
# 1. Code into /opt/premarket (owned by the deploy user)
sudo mkdir -p /opt/premarket
sudo chown "$USER:$USER" /opt/premarket
git clone <REPO_URL> /opt/premarket
cd /opt/premarket

# 2. Backend venv + deps
cd backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt
mkdir -p /opt/premarket/data

# 3. Secrets — create the real .env (NEVER committed)
cp .env.production.example .env
nano .env            # paste ANTHROPIC_API_KEY, Telegram token/chat id, etc.

# 4. Frontend build
cd ../frontend
npm ci
npm run build        # outputs frontend/dist

# 5. systemd service
sudo cp /opt/premarket/deploy/skzdev02/premarket-backend.service \
        /etc/systemd/system/premarket-backend.service
sudo systemctl daemon-reload
sudo systemctl enable --now premarket-backend
systemctl status premarket-backend --no-pager     # should be active (running)

# 6. nginx site (port 3000)
sudo cp /opt/premarket/deploy/skzdev02/premarket.conf \
        /etc/nginx/sites-available/premarket
sudo ln -sf /etc/nginx/sites-available/premarket \
        /etc/nginx/sites-enabled/premarket
sudo nginx -t                                      # MUST pass before reload
sudo systemctl reload nginx
```

### Verify
```bash
curl -s http://127.0.0.1:8000/health          # {"status":"ok",...}
curl -s http://127.0.0.1:3000/api/scan/status # served through nginx
```
Then from your machine (on Tailscale): open **http://skzdev02:3000**

---

## Redeploy (after pushing new code)

```bash
/opt/premarket/deploy/deploy.sh
```
Pulls `main`, updates deps, rebuilds the frontend, restarts the backend and
reloads nginx (with `nginx -t` first). The DB in `/opt/premarket/data` is left
untouched.

---

## Notes & troubleshooting

- **Migrations**: `ensure_schema()` runs on startup and adds new columns to the
  SQLite DB in place — no manual migration step.
- **Logs**: `journalctl -u premarket-backend -f`
- **Scheduler**: with `DEBUG=false` the scan runs every 5 min, 04:00–09:30 ET,
  Mon–Fri (pre-market). Set `DEBUG=true` only for debugging (scans every minute).
- **Port already in use**: nothing should be on 8000/3000, but check with
  `ss -tln | grep -E ':(8000|3000)'` before starting.
- **Firewall**: access is over Tailscale; no public ports are opened. If you
  later expose it, add auth first (see PROJECT_STATUS.md security notes).
- **Hardening (optional)**: to run under a dedicated unprivileged user instead
  of `adminskz`, create a `premarket` system user, `chown -R` the tree, and set
  `User=premarket` in the service file.
