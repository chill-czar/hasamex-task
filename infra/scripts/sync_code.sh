#!/usr/bin/env bash
set -euo pipefail

ZONE="${1:-us-central1-a}"
INSTANCE="hasamex-platform-vm"
BRANCH="${2:-main}"
REPO_URL="https://github.com/chill-czar/hasamex-task.git"

echo "=========================================================================="
echo "Updating Hasamex VM (${INSTANCE} in ${ZONE}) via Git Pull from ${REPO_URL} (${BRANCH})"
echo "=========================================================================="

gcloud compute ssh --quiet "${INSTANCE}" --zone="${ZONE}" --command="
  set -euo pipefail

  echo '>> Syncing code via Git on VM...'
  if [ -d /opt/hasamex/.git ]; then
    cd /opt/hasamex
    sudo git remote set-url origin ${REPO_URL} || true
    sudo git fetch origin ${BRANCH}
    sudo git reset --hard origin/${BRANCH}
  else
    echo '>> Initializing git clone at /opt/hasamex...'
    sudo mkdir -p /opt/hasamex
    sudo git clone --branch ${BRANCH} ${REPO_URL} /tmp/hasamex_repo
    sudo cp -r /tmp/hasamex_repo/.git /opt/hasamex/
    sudo rm -rf /tmp/hasamex_repo
    cd /opt/hasamex
    sudo git reset --hard origin/${BRANCH}
  fi

  echo '>> Setting up Python virtual environment...'
  if [ ! -d /opt/hasamex/.venv ]; then
    sudo python3 -m venv /opt/hasamex/.venv
  fi
  sudo /opt/hasamex/.venv/bin/pip install --upgrade pip
  sudo /opt/hasamex/.venv/bin/pip install -e /opt/hasamex

  echo '>> Installing frontend dependencies and building Next.js...'
  cd /opt/hasamex/apps/web
  sudo npm ci
  sudo npm run build
  cd /opt/hasamex

  echo '>> Configuring systemd services: hasamex-api and hasamex-web...'
  sudo tee /etc/systemd/system/hasamex-api.service > /dev/null <<EOF
[Unit]
Description=Hasamex FastAPI Backend Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/hasamex
EnvironmentFile=/opt/hasamex/.env
ExecStart=/opt/hasamex/.venv/bin/uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

  sudo tee /etc/systemd/system/hasamex-web.service > /dev/null <<EOF
[Unit]
Description=Hasamex Next.js Frontend Server
After=network.target hasamex-api.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/hasamex/apps/web
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

  echo '>> Configuring Nginx reverse proxy...'
  sudo tee /etc/nginx/sites-available/hasamex > /dev/null <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    # 1. API routes, Docs & OpenAPI to FastAPI
    location ~ ^/(api|docs|openapi\.json) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;

        # Disable buffering for Server-Sent Events (SSE) streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # 2. Frontend web application routes and assets to Next.js server
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
    }
}
EOF

  sudo rm -f /etc/nginx/sites-enabled/default
  sudo ln -sf /etc/nginx/sites-available/hasamex /etc/nginx/sites-enabled/hasamex
  sudo nginx -t

  echo '>> Precomputing analyses into PostgreSQL database...'
  set +e
  sudo -u www-data bash -c \"cd /opt/hasamex && export \\\$(grep -v '^#' .env | xargs) && /opt/hasamex/.venv/bin/python3 -m apps.api.app.services.precompute\"
  set -e

  echo '>> Setting permissions...'
  sudo chown -R www-data:www-data /opt/hasamex

  echo '>> Restarting systemd services...'
  sudo systemctl daemon-reload
  sudo systemctl stop hasamex || true
  sudo systemctl disable hasamex || true
  sudo systemctl enable --now hasamex-api hasamex-web
  sudo systemctl restart hasamex-api hasamex-web nginx
  sudo systemctl status hasamex-api hasamex-web --no-pager
"

echo "=========================================================================="
echo ">> Git update complete! Both backend and frontend services reloaded."
echo "=========================================================================="
