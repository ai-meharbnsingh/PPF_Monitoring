#!/usr/bin/env bash
# install.sh — PPF Workshop Monitoring System backend setup
# Run from project root: bash scripts/setup/install.sh

set -e

echo "=== PPF Backend Setup ==="
echo ""

# ── Python version check ──────────────────────────────────────────────────────
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d" " -f2 | cut -d"." -f1,2)
echo "Python version: $PYTHON_VERSION"
if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"; then
  echo "[OK] Python 3.11+ detected"
else
  echo "[ERROR] Python 3.11+ required"
  exit 1
fi

# ── Virtual environment ───────────────────────────────────────────────────────
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate
echo "[OK] Virtual environment activated"

# ── Install dependencies ──────────────────────────────────────────────────────
echo "Installing dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "[OK] Dependencies installed"

# ── Environment file ──────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "[WARN] .env created from .env.example — fill in your secrets before starting!"
else
  echo "[OK] .env file exists"
fi

# ── Create logs directory ─────────────────────────────────────────────────────
mkdir -p logs
echo "[OK] logs/ directory ready"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your database/MQTT credentials"
echo "  2. Start PostgreSQL and run migrations:"
echo "     alembic upgrade head"
echo "  3. Seed sensor types:"
echo "     psql -U <user> -d ppf_monitoring -f database/migrations/002_seed_sensor_types.sql"
echo "  4. Seed super admin:"
echo "     curl -X POST http://localhost:8000/api/v1/admin/seed-super-admin"
echo "  5. Start the server:"
echo "     uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
