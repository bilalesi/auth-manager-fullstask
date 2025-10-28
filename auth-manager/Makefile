.PHONY: help install dev dev-docker dev-local stop clean up down logs shell db-migrate db-upgrade db-downgrade db-revision db-current db-history lint format check build bake deploy 

# Default target
.DEFAULT_GOAL := help

export ENV ?= dev
export APP_VERSION := $(shell git describe --tags --always --dirty --abbrev=10 2>/dev/null || echo "0.0.0")
export COMMIT_SHA := $(shell git rev-parse --short=10 HEAD 2>/dev/null || echo "unknown")
export APP_NAME := auth-manager
export SERVICE_NAME ?= $(APP_NAME)
export SERVICE_TAG := $(APP_VERSION)
export SERVICE_TAG_LABEL := latest

ifneq ($(ENV), prod)
	export SERVICE_TAG := $(ENV)-$(SERVICE_TAG)
	export SERVICE_TAG_LABEL := $(ENV)-$(SERVICE_TAG_LABEL)
endif

PYTHON := python3
UV := uv
DOCKER_COMPOSE := docker compose
DOCKER_COMPOSE_DEV := $(DOCKER_COMPOSE) 
PROJECT_NAME := Authentication Manager Service

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ Help

help: ## Display this help message
	@echo "$(BLUE)$(PROJECT_NAME) - Makefile Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development Setup

install: ## Install dependencies using uv
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@command -v uv >/dev/null 2>&1 || { echo "$(RED)uv is not installed. Install it from https://docs.astral.sh/uv/$(NC)"; exit 1; }
	$(UV) sync
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

install-dev: install ## Install dependencies including dev dependencies
	@echo "$(BLUE)Installing dev dependencies...$(NC)"
	$(UV) sync --all-extras
	@echo "$(GREEN)Dev dependencies installed successfully!$(NC)"

##@ Development Server


dev-docker: ## Start development server with Docker Compose (hot-reload enabled)
	@echo "$(BLUE)Starting development server with Docker Compose...$(NC)"
	$(DOCKER_COMPOSE_DEV) --profile "nightfall" up --build --watch --remove-orphans 

dev-local: ## Start development server locally (requires local PostgreSQL)
	@echo "$(BLUE)Starting development server locally...$(NC)"
	@echo "$(YELLOW)Make sure PostgreSQL is running and .env is configured correctly.$(NC)"
	@echo "$(BLUE)Starting infrastructure with Docker Compose...$(NC)"
	$(DOCKER_COMPOSE_DEV) --profile "greenland" up --build --remove-orphans  -d
	@command -v uv >/dev/null 2>&1 || { echo "$(RED)uv is not installed. Run 'make install' first.$(NC)"; exit 1; }
	$(UV) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

dev: ## Start development server locally (requires local PostgreSQL)
	@echo "$(BLUE)Starting development server locally...$(NC)"
	@echo "$(YELLOW)Make sure PostgreSQL is running and .env is configured correctly.$(NC)"
	@command -v uv >/dev/null 2>&1 || { echo "$(RED)uv is not installed. Run 'make install' first.$(NC)"; exit 1; }
	$(UV) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug


##@ Docker Operations

up: ## Start services in production mode
	@echo "$(BLUE)Starting services...$(NC)"
	$(DOCKER_COMPOSE)  --profile "*" up  -d 
	@echo "$(GREEN)Services started successfully!$(NC)"

down: ## Stop and remove containers
	@echo "$(BLUE)Stopping services...$(NC)"
	$(DOCKER_COMPOSE) --profile "*" down 
	@echo "$(GREEN)Services stopped successfully!$(NC)"


restart: down up

logs: ## View logs from all services
	$(DOCKER_COMPOSE) logs -f


shell: ## Open an interactive shell in a running container
	@echo "$(BLUE)Listing running containers...$(NC)"; \
	containers=$$($(DOCKER_COMPOSE) ps --filter "status=running" --format "{{.Names}}"); \
	if [ -z "$$containers" ]; then \
		echo "$(RED)No running containers found.$(NC)"; \
		exit 1; \
	fi; \
	echo "Select a container to open shell:"; \
	select container in $$containers; do \
		if [ -n "$$container" ]; then \
			echo "$(BLUE)Opening shell in container: $$container$(NC)"; \
			docker debug $$container;  \
			break; \
		else \
			echo "$(RED)Invalid selection. Please try again.$(NC)"; \
		fi; \
	done

shell-db: ## Open PostgreSQL shell
	@echo "$(BLUE)Opening PostgreSQL shell...$(NC)"
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d auth_manager

clean: ## Remove containers, volumes, and images
	@echo "$(YELLOW)This will remove all containers, volumes, and images. Continue? [y/N]$(NC)" && read ans && [ $${ans:-N} = y ]
	$(DOCKER_COMPOSE) down --volumes --rmi all --remove-orphans
	docker volume rm -f auth-manager-postgres_data || true
	docker volume prune -f
	@echo "$(GREEN)Cleanup completed!$(NC)"

##@ Database Migrations

db-revision: ## Create a new migration revision (usage: make db-revision MESSAGE="description")
	@if [ -z "$(MESSAGE)" ]; then \
		echo "$(RED)Error: MESSAGE is required. Usage: make db-revision MESSAGE=\"your message\"$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Creating new migration revision...$(NC)"
	@if [ -n "$$(docker ps -q -f name=$(SERVICE_NAME))" ]; then \
		$(DOCKER_COMPOSE) exec $(SERVICE_NAME) alembic revision --autogenerate -m "$(MESSAGE)"; \
	else \
		$(UV) run alembic revision --autogenerate -m "$(MESSAGE)"; \
	fi
	@echo "$(GREEN)Migration revision created!$(NC)"

db-migrate: ## Run database migrations (upgrade to head)
	@echo "$(BLUE)Running database migrations...$(NC)"
	@if [ -n "$$(docker ps -q -f name=$(SERVICE_NAME))" ]; then \
		echo "$(YELLOW)Running migrations in Docker container...$(NC)"; \
		$(DOCKER_COMPOSE) exec $(SERVICE_NAME) alembic upgrade head; \
	else \
		echo "$(YELLOW)Running migrations locally...$(NC)"; \
		$(UV) run alembic upgrade head; \
	fi
	@echo "$(GREEN)Migrations completed successfully!$(NC)"


db-current: ## Show current database revision
	@echo "$(BLUE)Current database revision:$(NC)"
	@if [ -n "$$(docker ps -q -f name=$(SERVICE_NAME))" ]; then \
		$(DOCKER_COMPOSE) exec $(SERVICE_NAME) alembic current; \
	else \
		$(UV) run alembic current; \
	fi

db-history: ## Show migration history
	@echo "$(BLUE)Migration history:$(NC)"
	@if [ -n "$$(docker ps -q -f name=$(SERVICE_NAME))" ]; then \
		$(DOCKER_COMPOSE) exec $(SERVICE_NAME) alembic history; \
	else \
		$(UV) run alembic history; \
	fi

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)WARNING: This will destroy all data in the database!$(NC)"
	@echo "$(YELLOW)Continue? [y/N]$(NC)" && read ans && [ $${ans:-N} = y ]
	@echo "$(BLUE)Resetting database...$(NC)"
	$(DOCKER_COMPOSE) down -v
	$(DOCKER_COMPOSE) up -d db
	@sleep 5
	@$(MAKE) db-migrate
	@echo "$(GREEN)Database reset completed!$(NC)"

##@ CI Checks

lint: ## Run linter (ruff)
	@echo "$(BLUE)Running linter...$(NC)"
	$(UV) run -m ruff format --check
	$(UV) run -m ruff check
	$(UV) run -m ty check

format: ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	$(UV) run ruff format 
	$(UV) run ruff check --fix  
	@echo "$(GREEN)Code formatted successfully!$(NC)"

type: ## Run type check with ty
	@echo "$(BLUE)Type checking...$(NC)"
	$(UV) run ty check --color=always
	@echo "$(GREEN)Code formatted successfully!$(NC)"

audit: ## Run audit
	$(UV) run --with pip-audit pip-audit -l

##@ Tools

env: ## Copy .env.example to .env if it doesn't exist
	@if [ ! -f .env ]; then \
		echo "$(BLUE)Creating .env file from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN).env file created! Please update it with your configuration.$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists.$(NC)"; \
	fi


health: ## Check health of running services
	@echo "$(BLUE)Checking service health...$(NC)"
	@curl -f http://localhost:8000/health || echo "$(RED)Service is not healthy$(NC)"

version: ## Show project version
	@echo "$(BLUE)Project: $(PROJECT_NAME)$(NC)"
	@grep "^version" pyproject.toml | head -1

build: ## Build Docker image for the service
	@echo "$(BLUE)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) --profile "*" --progress=plain build $(SERVICE_NAME) --no-cache

bake: ## Build Docker image using bake
	docker buildx bake --print
	docker buildx bake --progress=plain 

deploy: ## Publish the Docker image to DockerHub
	$(MAKE) build
	$(DOCKER_COMPOSE) --profile "nightfall" push $(SERVICE_NAME)