# Makefile for Hasamex Expert Interview Analysis Platform
.PHONY: help install test eval run-backend run-frontend dev docker-build docker-up docker-down clean

SHELL := /bin/bash
VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
PYTEST := $(VENV)/bin/pytest

help:
	@echo "=========================================================================="
	@echo "Hasamex Evidence-Grounded Expert Interview Analysis Platform"
	@echo "=========================================================================="
	@echo "Available commands:"
	@echo "  make install       - Install backend (pip) and frontend (npm) dependencies"
	@echo "  make test          - Run backend pytest test suite"
	@echo "  make eval          - Run quantitative evaluation suite (retrieval, quote, timestamp)"
	@echo "  make run-backend   - Start FastAPI backend with live Gemini on port 8000"
	@echo "  make run-frontend  - Start Next.js App Router dashboard on port 3000"
	@echo "  make docker-build  - Build Docker containers for PostgreSQL, Backend, Frontend"
	@echo "  make docker-up     - Start all services with Docker Compose"
	@echo "  make docker-down   - Stop Docker Compose services"
	@echo "  make clean         - Remove cache directories, build artifacts, and temp files"
	@echo "=========================================================================="

install:
	@echo ">> Installing backend dependencies in $(VENV)..."
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .
	$(PIP) install pytest pytest-asyncio
	@echo ">> Installing frontend dependencies in apps/web..."
	cd apps/web && npm install
	@echo ">> Installation complete."

test:
	@echo ">> Running backend test suite..."
	$(PYTEST) apps/api/tests/ -v

test-api: test

eval:
	@echo ">> Running quantitative evaluation against ground truth benchmarks..."
	$(PYTHON) evaluation/evaluate.py

benchmark-latency:
	@echo ">> Running end-to-end latency benchmarks across API and architecture..."
	$(PYTHON) evaluation/benchmark_latency.py

benchmark: benchmark-latency


run-backend:
	@echo ">> Starting FastAPI backend on http://localhost:8000..."
	$(UVICORN) apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	@echo ">> Starting Next.js frontend on http://localhost:3000..."
	cd apps/web && npm run dev

dev:
	@echo "To run both concurrently in separate terminals:"
	@echo "  Terminal 1: make run-backend"
	@echo "  Terminal 2: make run-frontend"

deploy-infra:
	@echo ">> Provisioning infrastructure and deploying to Google Cloud (Zero Docker)..."
	./infra/scripts/deploy_vm.sh

sync-code:
	@echo ">> Syncing code to live Google Cloud VM..."
	./infra/scripts/sync_code.sh

docker-build:
	@echo ">> Building Docker Compose containers..."
	docker compose build

docker-up:
	@echo ">> Starting all services with Docker Compose..."
	docker compose up

docker-down:
	@echo ">> Stopping Docker Compose services..."
	docker compose down

clean:
	@echo ">> Cleaning cache and build artifacts..."
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf apps/web/.next
	rm -f hasamex.db
	@echo ">> Clean complete."
