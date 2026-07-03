#!/bin/bash
# Redeploy the Pre-Market Dashboard after code changes.
# Run on skzdev02 as the deploy user (adminskz):
#   /opt/premarket/deploy/deploy.sh
# First-time setup is in deploy/DEPLOYMENT.md — this script assumes the repo,
# venv, .env, systemd unit and nginx site already exist.
set -e

echo "Pre-Market Dashboard — deploy"
echo "============================="

# Repo root = parent of this script's dir
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
echo "Repo: $ROOT"

echo "1. Pulling latest code (main)..."
git pull origin main

echo "2. Backend deps..."
cd "$ROOT/backend"
[ -d venv ] || python3 -m venv venv
venv/bin/pip install -q -r requirements.txt
mkdir -p "$ROOT/data"   # SQLite DB lives here

echo "3. Building frontend..."
cd "$ROOT/frontend"
npm ci
npm run build

echo "4. Restarting backend service..."
sudo systemctl restart premarket-backend

echo "5. Reloading nginx (config test first)..."
sudo nginx -t && sudo systemctl reload nginx

echo "✓ Deploy complete"
echo "  Dashboard: http://skzdev02:3000"
echo "  API:       http://skzdev02:3000/api  (backend on 127.0.0.1:8000)"
