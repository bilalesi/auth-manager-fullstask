.PHONY: help full-stack window vault install

.DEFAULT_GOAL := help

BACKEND_DIR := auth-manager
FRONTEND_DIR := frontend

BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m

help: ## Show available commands
	@echo "$(BLUE)Auth Manager Full-Stack - Available Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

full-stack:  ## Start both backend and frontend
	@echo "$(BLUE)Starting full-stack application...$(NC)"
	@echo "$(YELLOW)Starting backend in background...$(NC)"
	@cd $(BACKEND_DIR) && $(MAKE) dev-local & \
	echo "$(YELLOW)Starting frontend...$(NC)" && \
	cd $(FRONTEND_DIR) && pnpm dev

vault: ## Start backend only
	@echo "$(BLUE)Starting backend...$(NC)"
	@cd $(BACKEND_DIR) && $(MAKE) dev-local

window: ## Start frontend only
	@echo "$(BLUE)Starting frontend...$(NC)"
	@cd $(FRONTEND_DIR) && pnpm dev


##@ Setup

install: ## Install all dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@cd $(BACKEND_DIR) && $(MAKE) install
	@cd $(FRONTEND_DIR) && pnpm install
	@echo "See the application-specific documentation for instructions on setting up the environment."

