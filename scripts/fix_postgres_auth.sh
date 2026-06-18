#!/usr/bin/env bash
# Fix PostgreSQL password authentication for the medivault app user on Fedora.
# Fedora defaults to ident/peer auth — asyncpg needs scram-sha-256 over TCP.
set -euo pipefail

DB_USER="medivault"
DB_PASS="medivault_secret"
DB_NAME="medivault"

if [[ "${EUID}" -ne 0 ]]; then
    echo "Re-running with sudo..."
    exec sudo bash "$0" "$@"
fi

PG_DATA="/var/lib/pgsql/data"
PG_HBA="${PG_DATA}/pg_hba.conf"

if [[ ! -f "${PG_HBA}" ]]; then
    echo "ERROR: ${PG_HBA} not found. Is PostgreSQL installed?"
    exit 1
fi

echo "=== Fixing PostgreSQL auth for ${DB_USER} ==="

cp "${PG_HBA}" "${PG_HBA}.medivault.bak.$(date +%s)"

# Allow password auth for TCP connections to localhost (required by asyncpg)
sed -i -E \
    -e 's/^(host[[:space:]]+all[[:space:]]+all[[:space:]]+127\.0\.0\.1\/32[[:space:]]+).*/\1scram-sha-256/' \
    -e 's/^(host[[:space:]]+all[[:space:]]+all[[:space:]]+::1\/128[[:space:]]+).*/\1scram-sha-256/' \
    "${PG_HBA}"

if ! grep -qE '^host[[:space:]]+all[[:space:]]+all[[:space:]]+127\.0\.0\.1/32[[:space:]]+scram-sha-256' "${PG_HBA}"; then
    echo "host    all             all             127.0.0.1/32            scram-sha-256" >> "${PG_HBA}"
fi
if ! grep -qE '^host[[:space:]]+all[[:space:]]+all[[:space:]]+::1/128[[:space:]]+scram-sha-256' "${PG_HBA}"; then
    echo "host    all             all             ::1/128                 scram-sha-256" >> "${PG_HBA}"
fi

systemctl reload postgresql || systemctl restart postgresql

echo "Configuring database user and permissions..."
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASS}';
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
\c ${DB_NAME}
GRANT ALL ON SCHEMA public TO ${DB_USER};
ALTER SCHEMA public OWNER TO ${DB_USER};
SQL

echo ""
echo "Testing connection as ${DB_USER}..."
if PGPASSWORD="${DB_PASS}" psql -h 127.0.0.1 -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" &>/dev/null; then
    echo "✓ PostgreSQL password auth works for ${DB_USER}@localhost"
else
    echo "✗ Connection test failed. Check ${PG_HBA}"
    exit 1
fi

echo ""
echo "Done. Now run (as your normal user):"
echo "  cd \"$(dirname "$(dirname "$(readlink -f "$0")")")\""
echo "  source .venv/bin/activate"
echo "  alembic upgrade head"
