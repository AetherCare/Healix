#!/usr/bin/env bash
# MediVault AI — Native Fedora setup (no Docker required).
# Installs PostgreSQL, Valkey/Redis, OCR deps, creates DB, runs migrations.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DB_USER="medivault"
DB_PASS="medivault_secret"
DB_NAME="medivault"

configure_postgres_auth() {
    PG_HBA="/var/lib/pgsql/data/pg_hba.conf"
    [[ -f "${PG_HBA}" ]] || return 0

    cp "${PG_HBA}" "${PG_HBA}.medivault.bak.$(date +%s)" 2>/dev/null || true
    sed -i -E \
        -e 's/^(host[[:space:]]+all[[:space:]]+all[[:space:]]+127\.0\.0\.1\/32[[:space:]]+).*/\1scram-sha-256/' \
        -e 's/^(host[[:space:]]+all[[:space:]]+all[[:space:]]+::1\/128[[:space:]]+).*/\1scram-sha-256/' \
        "${PG_HBA}"
    grep -qE '^host[[:space:]]+all[[:space:]]+all[[:space:]]+127\.0\.0\.1/32' "${PG_HBA}" || \
        echo "host    all             all             127.0.0.1/32            scram-sha-256" >> "${PG_HBA}"
    grep -qE '^host[[:space:]]+all[[:space:]]+all[[:space:]]+::1/128' "${PG_HBA}" || \
        echo "host    all             all             ::1/128                 scram-sha-256" >> "${PG_HBA}"
    systemctl reload postgresql 2>/dev/null || systemctl restart postgresql
}

start_cache_service() {
    if systemctl list-unit-files valkey.service &>/dev/null; then
        systemctl enable --now valkey
    elif systemctl list-unit-files redis.service &>/dev/null; then
        systemctl enable --now redis
    else
        echo "WARNING: No valkey/redis service found."
    fi
}

echo "=== MediVault AI — Fedora Native Setup ==="

if [[ "${EUID}" -ne 0 ]]; then
    echo "Re-running with sudo (required for package install + PostgreSQL)..."
    exec sudo bash "$0" "$@"
fi

REAL_USER="${SUDO_USER:-$USER}"

echo "[1/7] Installing system packages..."
dnf install -y \
    postgresql-server \
    postgresql \
    valkey \
    valkey-compat-redis \
    tesseract \
    tesseract-langpack-eng \
    poppler-utils \
    curl \
    python3-pip \
    gcc \
    python3-devel \
    libpq-devel

echo "[2/7] Initializing PostgreSQL (if needed)..."
if [[ ! -f /var/lib/pgsql/data/PG_VERSION ]] && [[ ! -f /var/lib/pgsql/data/postgresql.conf ]]; then
    postgresql-setup --initdb 2>/dev/null || postgresql-setup initdb 2>/dev/null || true
fi

echo "[3/7] Starting PostgreSQL and Valkey/Redis..."
systemctl enable --now postgresql
start_cache_service

echo "[4/7] Configuring PostgreSQL password authentication..."
configure_postgres_auth

echo "[5/7] Creating database and user..."
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
        CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';
    ELSE
        ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASS}';
    END IF;
END \$\$;
SELECT 'CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}')\gexec
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
\c ${DB_NAME}
GRANT ALL ON SCHEMA public TO ${DB_USER};
ALTER SCHEMA public OWNER TO ${DB_USER};
SQL

echo "[6/7] Installing Python dependencies..."
cd "${PROJECT_ROOT}"
if [[ ! -d .venv ]]; then
    sudo -u "${REAL_USER}" python3 -m venv .venv
fi
sudo -u "${REAL_USER}" bash -c "
    cd '${PROJECT_ROOT}'
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
"

echo "[7/7] Running database migrations..."
sudo -u "${REAL_USER}" bash -c "
    cd '${PROJECT_ROOT}'
    source .venv/bin/activate
    alembic upgrade head
"

echo ""
echo "=============================================="
echo "  Setup complete!"
echo "=============================================="
echo ""
echo "PostgreSQL: localhost:5432 / db=${DB_NAME} / user=${DB_USER}"
echo "Valkey:     localhost:6379 (redis-compatible)"
echo ""
echo "Next steps (as ${REAL_USER}, NOT root):"
echo "  cd '${PROJECT_ROOT}'"
echo "  source .venv/bin/activate"
echo "  ./scripts/check_services.sh"
echo "  ./scripts/start_with_tunnel.sh          # Terminal 1"
echo "  celery -A app.tasks.celery_app worker --loglevel=info   # Terminal 2"
echo ""
echo "Install ngrok separately if not installed:"
echo "  https://ngrok.com/download"
echo "  ngrok config add-authtoken YOUR_TOKEN"
echo ""
