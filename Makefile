.PHONY: install dev test lint format clean docker-build docker-up docker-down

# Variables
PYTHON = python3
POETRY = poetry
DOCKER_COMPOSE = docker-compose

# Development setup
install:
	$(POETRY) install

dev:
	$(POETRY) run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Testing
test:
	$(POETRY) run pytest -v

test-watch:
	$(POETRY) run pytest -v --watch

# Code quality
lint:
	$(POETRY) run ruff check src tests
	$(POETRY) run black --check src tests

format:
	$(POETRY) run ruff check --fix src tests
	$(POETRY) run black src tests
	$(POETRY) run isort src tests

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

# Docker
docker-build:
	docker build -f ops/docker/Dockerfile -t seederbot:latest .

docker-up:
	$(DOCKER_COMPOSE) up -d

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f

# Pre-commit
pre-commit-install:
	$(POETRY) run pre-commit install

pre-commit-run:
	$(POETRY) run pre-commit run --all-files

# Environment
env-example:
	cp .env.example .env
	@echo "Please edit .env with your actual configuration"

# Help
help:
	@echo "Available commands:"
	@echo "  install           Install dependencies"
	@echo "  dev              Run development server"
	@echo "  test             Run tests"
	@echo "  lint             Check code quality"
	@echo "  format           Format code"
	@echo "  clean            Clean up build artifacts"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-up        Start services with Docker Compose"
	@echo "  docker-down      Stop Docker Compose services"
	@echo "  pre-commit-install Install pre-commit hooks"
	@echo "  env-example      Copy .env.example to .env"