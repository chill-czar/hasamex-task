#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="/var/log/hasamex-bootstrap.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=========================================================================="
echo "Starting Hasamex Platform VM Bootstrap at $(date -u)"
echo "=========================================================================="

export DEBIAN_FRONTEND=noninteractive

# 1. System packages
echo ">> Installing system dependencies..."
apt-get update -y
apt-get install -y --no-install-recommends \
  python3 \
  python3-pip \
  python3-venv \
  python3.12-venv \
  python3-dev \
  build-essential \
  git \
  curl \
  jq \
  ca-certificates \
  nginx \
  libpq5 \
  libpq-dev

# 2. Node.js 22 LTS
if ! command -v node &> /dev/null; then
  echo ">> Installing Node.js 22..."
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y nodejs
fi

echo ">> Node version: $(node -v)"
echo ">> Python version: $(python3 --version)"

# 3. Application Directory & Source
APP_DIR="/opt/hasamex"
echo ">> Preparing application directory at $APP_DIR..."
mkdir -p "$APP_DIR"

if [ ! -d "$APP_DIR/.git" ]; then
  echo ">> Cloning repository from ${git_repo_url} (branch: ${git_branch})..."
  git clone --branch "${git_branch}" "${git_repo_url}" "$APP_DIR" || {
    echo ">> Git clone fallback: initialized empty repo or directory already contains code."
  }
fi

# 4. Fetch Secrets from Secret Manager via GCP Instance Metadata
echo ">> Retrieving secrets from Google Cloud Secret Manager..."
GEMINI_KEY=$(gcloud secrets versions access latest --secret="${gemini_secret_id}" --project="${project_id}" 2>/dev/null || echo "${fallback_gemini_key}")
DB_PASS=$(gcloud secrets versions access latest --secret="${db_password_secret_id}" --project="${project_id}" 2>/dev/null || echo "")

# 5. Environment configuration
cat <<EOF > "$APP_DIR/.env"
ENVIRONMENT=production
PORT=8000
GEMINI_API_KEY=$GEMINI_KEY
DATABASE_URL=postgresql://${db_user}:$DB_PASS@${db_host}:5432/${db_name}
GEMINI_MODEL=gemini-3.6-flash
DATA_DIR=$APP_DIR/data/transcripts
GUIDE_FILE=$APP_DIR/data/guide/Interview_Guide.txt
EOF

# 6. Python Virtualenv & Dependencies
echo ">> Setting up Python virtual environment..."
cd "$APP_DIR"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip

if [ -f "$APP_DIR/pyproject.toml" ]; then
  .venv/bin/pip install -e .

  # 7. Frontend Build
  if [ -d "$APP_DIR/apps/web" ]; then
    echo ">> Building Next.js application..."
    cd "$APP_DIR/apps/web"
    npm ci
    npm run build
    cd "$APP_DIR"
  fi

  # 8. Run Initial Database Precomputation
  echo ">> Running precomputation to persist all analyses in PostgreSQL..."
  set +e
  .venv/bin/python3 -m apps.api.app.services.precompute
  set -e
fi

# 9. Set permissions for www-data
chown -R www-data:www-data "$APP_DIR"

# 10. Systemd Services (Backend API & Frontend Web)
echo ">> Configuring systemd services: hasamex-api and hasamex-web..."
cat <<EOF > /etc/systemd/system/hasamex-api.service
[Unit]
Description=Hasamex FastAPI Backend Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

cat <<EOF > /etc/systemd/system/hasamex-web.service
[Unit]
Description=Hasamex Next.js Frontend Server
After=network.target hasamex-api.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR/apps/web
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/usr/bin/npm run start -- -p 3000 -H 127.0.0.1
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 11. Nginx Reverse Proxy
echo ">> Configuring Nginx reverse proxy..."
cat <<EOF > /etc/nginx/sites-available/hasamex
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    # 1. API routes, Docs & OpenAPI to FastAPI
    location ~ ^/(api|docs|openapi\.json) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Disable buffering for Server-Sent Events (SSE) streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # 2. Frontend web application routes and assets to Next.js server
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/hasamex /etc/nginx/sites-enabled/hasamex

# 12. Start Services
echo ">> Starting systemd services..."
systemctl daemon-reload
systemctl stop hasamex || true
systemctl disable hasamex || true
systemctl enable --now hasamex-api hasamex-web
systemctl restart hasamex-api hasamex-web nginx

echo "=========================================================================="
echo "Hasamex VM Bootstrap Complete at $(date -u)!"
echo "=========================================================================="
