#!/usr/bin/env bash
# Verify PostgreSQL and Redis are reachable before starting the backend.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "${PROJECT_ROOT}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

ok() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; FAILED=1; }

FAILED=0

echo "=== MediVault AI — Service Check ==="

# PostgreSQL
if command -v pg_isready &>/dev/null; then
    if pg_isready -h localhost -p 5432 &>/dev/null; then
        ok "PostgreSQL is running on :5432"
    else
        fail "PostgreSQL installed but not running. Run: sudo systemctl start postgresql"
    fi
else
    fail "PostgreSQL not installed. Run: sudo ./scripts/setup_fedora.sh"
fi

# Redis / Valkey (Fedora 44+ ships Valkey with redis-cli compatibility)
if command -v redis-cli &>/dev/null; then
    if redis-cli ping 2>/dev/null | grep -q PONG; then
        ok "Redis/Valkey is running on :6379"
    else
        fail "Redis/Valkey installed but not running. Run: sudo systemctl start valkey"
    fi
else
    fail "Valkey/Redis not installed. Run: sudo ./scripts/setup_fedora.sh"
fi

# ngrok
if command -v ngrok &>/dev/null; then
    ok "ngrok is installed"
else
    fail "ngrok not installed. Download from https://ngrok.com/download"
fi

# .env
if [[ -f .env ]]; then
    if grep -q '^APP_NAME=MediVault AI$' .env 2>/dev/null; then
        fail ".env has unquoted APP_NAME — run: sed -i 's/^APP_NAME=MediVault AI/APP_NAME=\"MediVault AI\"/' .env"
    else
        ok ".env exists"
    fi
else
    fail ".env missing — run: cp .env.example .env"
fi

# venv
if [[ -d .venv ]]; then
    ok "Python venv exists"
else
    fail "venv missing — run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

echo ""
if [[ "${FAILED}" -eq 0 ]]; then
    echo -e "${GREEN}All checks passed. Ready to start.${NC}"
    echo "  ./scripts/start_with_tunnel.sh"
    exit 0
else
    echo -e "${RED}Some checks failed. Fix the items above, then re-run this script.${NC}"
    echo ""
    echo "Quick fix (Fedora, no Docker):"
    echo "  sudo ./scripts/fix_postgres_auth.sh && alembic upgrade head"
    echo "  sudo ./scripts/setup_fedora.sh"
    exit 1
fi
