#!/bin/bash
set -e

echo "Pre-Market Dashboard Deploy Script"
echo "===================================="

DEPLOY_ENV=${1:-production}
echo "Deploying to: $DEPLOY_ENV"

# Navigate to project root
cd "$(dirname "$0")/.."

echo "1. Pulling latest code from git..."
git pull origin main

echo "2. Setting up backend..."
cd backend

# Create virtual env if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# TODO: Run migrations with alembic
# alembic upgrade head

echo "3. Building frontend..."
cd ../frontend

npm ci
npm run build

echo "4. Restarting services..."
sudo systemctl restart premarket-backend

echo "✓ Deployment complete!"
echo "Frontend: http://premarket.tailscale"
echo "API: http://premarket.tailscale/api"
