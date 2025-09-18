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
	docker build -t seederbot:latest .

docker-run:
	docker run --rm -p 8000:8000 --env-file .env seederbot:latest

docker-run-test:
	docker run --rm -p 8001:8000 -e APP_TOKEN=test-token seederbot:latest

# Docker Compose - Full stack
docker-up:
	$(DOCKER_COMPOSE) up -d

docker-up-build:
	$(DOCKER_COMPOSE) up -d --build

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f

# Docker Compose - Standalone
docker-up-standalone:
	$(DOCKER_COMPOSE) -f docker-compose.standalone.yml up -d

docker-down-standalone:
	$(DOCKER_COMPOSE) -f docker-compose.standalone.yml down

# Docker Compose - Development
docker-up-dev:
	$(DOCKER_COMPOSE) -f docker-compose.development.yml up -d

docker-down-dev:
	$(DOCKER_COMPOSE) -f docker-compose.development.yml down

# Docker Compose - With proxy
docker-up-proxy:
	$(DOCKER_COMPOSE) --profile proxy up -d

# Docker Compose - Full media stack
docker-up-full:
	$(DOCKER_COMPOSE) --profile full-stack up -d

# Docker cleanup
docker-clean:
	docker system prune -f
	docker image prune -f

docker-clean-all:
	docker system prune -a -f

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
	@echo ""
	@echo "Development:"
	@echo "  install              Install dependencies"
	@echo "  dev                  Run development server"
	@echo "  test                 Run tests"
	@echo "  lint                 Check code quality"
	@echo "  format               Format code"
	@echo "  clean                Clean up build artifacts"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build         Build Docker image"
	@echo "  docker-run           Run single container with .env"
	@echo "  docker-run-test      Run single container with test token"
	@echo ""
	@echo "Docker Compose:"
	@echo "  docker-up            Start full media stack"
	@echo "  docker-up-build      Start full stack with rebuild"
	@echo "  docker-up-standalone Start SeederBot only"
	@echo "  docker-up-dev        Start development environment"
	@echo "  docker-up-proxy      Start with nginx proxy"
	@echo "  docker-up-full       Start complete media stack"
	@echo "  docker-down          Stop services"
	@echo "  docker-logs          View service logs"
	@echo ""
	@echo "Environment:"
	@echo "  env-example          Copy .env.example to .env"
	@echo "  pre-commit-install   Install pre-commit hooks"