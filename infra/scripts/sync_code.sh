#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ZONE="${1:-us-central1-a}"
INSTANCE="hasamex-platform-vm"

echo "=========================================================================="
echo "Syncing code directly to Hasamex VM (${INSTANCE} in ${ZONE}) - Zero Docker"
echo "=========================================================================="

cd "${REPO_ROOT}"

# Pre-build Next.js static export locally
echo ">> Building Next.js static frontend..."
cd apps/web
npm run build
cd "${REPO_ROOT}"

# Create deployment bundle excluding virtualenvs, git history, and caches
BUNDLE_PATH="/tmp/hasamex-deploy.tar.gz"
echo ">> Creating deployment archive: ${BUNDLE_PATH}..."
tar --exclude='.git' \
    --exclude='.venv' \
    --exclude='node_modules' \
    --exclude='apps/web/node_modules' \
    --exclude='.next' \
    --exclude='apps/web/.next' \
    --exclude='.pytest_cache' \
    --exclude='__pycache__' \
    -czf "${BUNDLE_PATH}" \
    apps data evaluation pyproject.toml Makefile README.md

# Copy to VM via gcloud compute scp
echo ">> Uploading archive to ${INSTANCE}..."
gcloud compute scp "${BUNDLE_PATH}" "${INSTANCE}:/tmp/hasamex-deploy.tar.gz" --zone="${ZONE}"

# Execute update on VM
echo ">> Extracting and setting up application on VM..."
gcloud compute ssh "${INSTANCE}" --zone="${ZONE}" --command='
  set -euo pipefail
  echo ">> Unpacking archive to /opt/hasamex..."
  sudo tar -xzf /tmp/hasamex-deploy.tar.gz -C /opt/hasamex/

  if [ ! -d /opt/hasamex/.venv ]; then
    echo ">> Creating Python virtual environment..."
    sudo python3 -m venv /opt/hasamex/.venv
  fi

  echo ">> Installing Python package..."
  sudo /opt/hasamex/.venv/bin/pip install --upgrade pip
  sudo /opt/hasamex/.venv/bin/pip install -e /opt/hasamex

  echo ">> Configuring systemd service..."
  sudo tee /etc/systemd/system/hasamex.service > /dev/null <<EOF
[Unit]
Description=Hasamex Expert Interview Analysis Platform
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/hasamex
EnvironmentFile=/opt/hasamex/.env
ExecStart=/opt/hasamex/.venv/bin/uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

  echo ">> Configuring Nginx reverse proxy..."
  sudo tee /etc/nginx/sites-available/hasamex > /dev/null <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
EOF

  sudo rm -f /etc/nginx/sites-enabled/default
  sudo ln -sf /etc/nginx/sites-available/hasamex /etc/nginx/sites-enabled/hasamex
  sudo nginx -t

  echo ">> Precomputing analyses into PostgreSQL database..."
  set +e
  sudo -u www-data bash -c "cd /opt/hasamex && export \$(grep -v \"^#\" .env | xargs) && /opt/hasamex/.venv/bin/python3 -m apps.api.app.services.precompute"
  set -e

  echo ">> Setting permissions..."
  sudo chown -R www-data:www-data /opt/hasamex

  echo ">> Restarting systemd services..."
  sudo systemctl daemon-reload
  sudo systemctl enable hasamex
  sudo systemctl restart hasamex
  sudo systemctl restart nginx
  sudo systemctl status hasamex --no-pager
'

echo "=========================================================================="
echo ">> Code sync complete! Application service reloaded."
echo "=========================================================================="
