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

  echo '>> Ensuring python3.12-venv is installed...'
  sudo apt-get update -y -qq
  sudo apt-get install -y --no-install-recommends python3-venv python3.12-venv python3-pip

  echo '>> Setting up Python virtual environment...'
  if [ ! -f /opt/hasamex/.venv/bin/pip ]; then
    sudo rm -rf /opt/hasamex/.venv
    sudo python3 -m venv /opt/hasamex/.venv
  fi
  sudo /opt/hasamex/.venv/bin/pip install --upgrade pip
  sudo /opt/hasamex/.venv/bin/pip install -e /opt/hasamex

  echo '>> Installing frontend dependencies and building Next.js...'
  cd /opt/hasamex/apps/web
  sudo npm ci
  sudo npm run build
  cd /opt/hasamex

  echo '>> Ensuring PM2 is installed...'
  if ! command -v pm2 &> /dev/null; then
    sudo npm install -g pm2
  fi

  echo '>> Configuring Nginx reverse proxy...'
  sudo tee /etc/nginx/sites-available/hasamex > /dev/null <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    # 1. API routes, Docs & OpenAPI to FastAPI (PM2 hasamex-api on port 8000)
    location ~ ^/(api|docs|openapi\.json) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Disable buffering for Server-Sent Events (SSE) streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # 2. Frontend web application routes and assets to Next.js (PM2 hasamex-web on port 3000)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
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

  echo '>> Setting permissions and stopping legacy systemd units...'
  sudo systemctl stop hasamex hasamex-api hasamex-web 2>/dev/null || true
  sudo systemctl disable hasamex hasamex-api hasamex-web 2>/dev/null || true

  export PM2_HOME=\"/opt/hasamex/.pm2\"
  sudo mkdir -p \"\$PM2_HOME\"
  sudo chown -R www-data:www-data /opt/hasamex \"\$PM2_HOME\"

  echo '>> Starting/Reloading processes with PM2...'
  cd /opt/hasamex
  sudo -u www-data PM2_HOME=\"\$PM2_HOME\" pm2 startOrReload ecosystem.config.js
  sudo -u www-data PM2_HOME=\"\$PM2_HOME\" pm2 save
  sudo env PATH=\$PATH:/usr/bin pm2 startup systemd -u www-data --hp /opt/hasamex || true

  echo '>> Restarting Nginx...'
  sudo systemctl restart nginx
  sudo -u www-data PM2_HOME=\"\$PM2_HOME\" pm2 status
"

echo "=========================================================================="
echo ">> Git update complete! Both backend and frontend services reloaded."
echo "=========================================================================="
