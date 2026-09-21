#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID=$(gcloud config get-value project)
REGION="${1:-us-central1}"
BUCKET_NAME="hasamex-tfstate-${PROJECT_ID}"

echo "=========================================================================="
echo "Hasamex GCS Remote State Bootstrap"
echo "Project: ${PROJECT_ID}"
echo "Region:  ${REGION}"
echo "Bucket:  gs://${BUCKET_NAME}"
echo "=========================================================================="

echo ">> Enabling Cloud Resource Manager and Storage APIs..."
gcloud services enable cloudresourcemanager.googleapis.com storage.googleapis.com --project="${PROJECT_ID}"

if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" &>/dev/null; then
  echo ">> Creating state bucket gs://${BUCKET_NAME}..."
  gcloud storage buckets create "gs://${BUCKET_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
  
  echo ">> Enabling object versioning..."
  gcloud storage buckets update "gs://${BUCKET_NAME}" --versioning
else
  echo ">> Bucket gs://${BUCKET_NAME} already exists."
fi

echo ">> Remote state bucket is ready."
