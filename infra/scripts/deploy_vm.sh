#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TF_DIR="${REPO_ROOT}/infra/terraform"

echo "=========================================================================="
echo "Hasamex Single-Instance VM Deployment via Terraform (No Docker)"
echo "=========================================================================="

cd "${REPO_ROOT}"

# 1. Load GEMINI_API_KEY from .env if not already set
if [ -z "${GEMINI_API_KEY:-}" ]; then
  if [ -f .env ]; then
    echo ">> Reading GEMINI_API_KEY from local .env..."
    GEMINI_API_KEY=$(grep -E "^GEMINI_API_KEY=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    export GEMINI_API_KEY
  fi
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "ERROR: GEMINI_API_KEY is not set in environment or .env file."
  exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
echo ">> Active GCP Project: ${PROJECT_ID}"

# 2. Bootstrap GCS remote state bucket
echo ">> Ensuring GCS remote state bucket exists..."
"${REPO_ROOT}/infra/bootstrap/bootstrap_state.sh" "us-central1"

# 3. Authenticate Terraform via active gcloud session
echo ">> Obtaining Google OAuth access token..."
export GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth print-access-token)

# 4. Terraform Init & Apply
cd "${TF_DIR}"

echo ">> Initializing Terraform..."
terraform init -reconfigure

echo ">> Planning Terraform deployment..."
terraform plan -var="gemini_api_key=${GEMINI_API_KEY}" -out=tfplan

echo ">> Applying Terraform deployment..."
terraform apply -auto-approve tfplan

# 5. Extract outputs
VM_IP=$(terraform output -raw vm_public_ip)
WEB_URL=$(terraform output -raw web_url)
HEALTH_URL=$(terraform output -raw health_url)

echo "=========================================================================="
echo "Infrastructure Provisioned Successfully!"
echo "Instance Public IP: ${VM_IP}"
echo "Application URL:    ${WEB_URL}"
echo "Health Endpoint:    ${HEALTH_URL}"
echo "=========================================================================="

# 6. Wait for VM SSH to become responsive
echo ">> Waiting for instance SSH to become ready..."
for i in {1..30}; do
  if gcloud compute ssh hasamex-platform-vm --zone=us-central1-a --command="echo 'VM online'" 2>/dev/null; then
    echo ">> VM SSH is ready!"
    break
  fi
  echo ">> Waiting for VM SSH access ($i/30)..."
  sleep 10
done

# 7. Sync current local codebase to the VM
echo ">> Syncing application code to VM..."
"${REPO_ROOT}/infra/scripts/sync_code.sh" "us-central1-a"

# 8. Verify Health Check
echo ">> Polling health endpoint at ${HEALTH_URL}..."
for i in {1..20}; do
  if curl -s -f "${HEALTH_URL}" | grep -q "healthy"; then
    echo "=========================================================================="
    echo "DEPLOYMENT VERIFIED & HEALTHY!"
    echo "Open the application in your browser: ${WEB_URL}"
    echo "=========================================================================="
    exit 0
  fi
  echo ">> Waiting for ${HEALTH_URL} to respond ($i/20)..."
  sleep 10
done

echo "WARNING: Health check did not respond within expected time."
echo "Check PM2 and Nginx process status with:"
echo "  gcloud compute ssh hasamex-platform-vm --zone=us-central1-a --command=\"sudo -u www-data PM2_HOME=/opt/hasamex/.pm2 pm2 status && sudo systemctl status nginx\""

