# Image Canvas Workspace - Makefile
# Automates setup and running of both backend and frontend

.PHONY: help start start-backend start-frontend install install-backend install-frontend setup clean kill-ports dev-logs health check-deps

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

# Default ports
BACKEND_PORT=8001
FRONTEND_PORT=5173

# Python virtual environment paths
VENV_PATH=./venv
PYTHON=$(VENV_PATH)/bin/python
PIP=$(VENV_PATH)/bin/pip

# Default target
help: ## Show this help message
	@echo "$(BLUE)Image Canvas Workspace - Makefile Commands$(NC)"
	@echo "=========================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: install-backend install-frontend ## Install all dependencies
	@echo "$(GREEN)✅ All dependencies installed successfully!$(NC)"

install-backend: ## Install backend Python dependencies
	@echo "$(YELLOW)📦 Installing backend dependencies...$(NC)"
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "$(YELLOW)Creating Python virtual environment...$(NC)"; \
		python3 -m venv $(VENV_PATH); \
	fi
	@$(PIP) install -r backend/requirements.txt
	@echo "$(GREEN)✅ Backend dependencies installed$(NC)"

install-frontend: ## Install frontend Node.js dependencies
	@echo "$(YELLOW)📦 Installing frontend dependencies...$(NC)"
	@cd image-canvas && npm install
	@echo "$(GREEN)✅ Frontend dependencies installed$(NC)"

# Setup targets
setup: install ## Run full setup including environment configuration
	@echo "$(YELLOW)🔧 Running backend setup...$(NC)"
	@cd backend && $(PYTHON) setup.py
	@if [ ! -f "backend/.env" ]; then \
		echo "$(YELLOW)Creating .env file from template...$(NC)"; \
		cp backend/env.config backend/.env; \
		echo "$(YELLOW)⚠️  Please edit backend/.env with your API keys$(NC)"; \
	fi
	@echo "$(GREEN)✅ Setup completed!$(NC)"
	@echo "$(BLUE)💡 Next steps:$(NC)"
	@echo "   1. Edit backend/.env with your API keys (HF_TOKEN, OPENAI_API_KEY)"
	@echo "   2. Run 'make start' to launch both services"

# Development targets
start: ## Start both backend and frontend in development mode
	@echo "$(BLUE)🚀 Starting Image Canvas Workspace...$(NC)"
	@$(MAKE) --no-print-directory kill-ports
	@echo "$(YELLOW)Starting backend server...$(NC)"
	@cd backend && $(PYTHON) start.py &
	@sleep 3
	@echo "$(YELLOW)Starting frontend server...$(NC)"
	@cd image-canvas && npm run dev &
	@sleep 2
	@echo "$(GREEN)✅ Both services started!$(NC)"
	@echo "$(BLUE)🌐 Access your application:$(NC)"
	@echo "   Frontend: http://localhost:$(FRONTEND_PORT)"
	@echo "   Backend API: http://localhost:$(BACKEND_PORT)"
	@echo "   API Docs: http://localhost:$(BACKEND_PORT)/docs"
	@echo "$(YELLOW)Press Ctrl+C to stop all services$(NC)"
	@$(MAKE) --no-print-directory wait-for-interrupt

start-backend: ## Start only the backend server
	@echo "$(YELLOW)🔧 Starting backend server...$(NC)"
	@$(MAKE) --no-print-directory kill-backend
	@cd backend && $(PYTHON) start.py
	@echo "$(GREEN)✅ Backend started on http://localhost:$(BACKEND_PORT)$(NC)"

start-frontend: ## Start only the frontend development server
	@echo "$(YELLOW)🎨 Starting frontend server...$(NC)"
	@$(MAKE) --no-print-directory kill-frontend
	@cd image-canvas && npm run dev
	@echo "$(GREEN)✅ Frontend started on http://localhost:$(FRONTEND_PORT)$(NC)"

# Production build targets
build: build-frontend ## Build frontend for production
	@echo "$(GREEN)✅ Production build completed!$(NC)"

build-frontend: ## Build frontend for production
	@echo "$(YELLOW)🏗️  Building frontend for production...$(NC)"
	@cd image-canvas && npm run build
	@echo "$(GREEN)✅ Frontend built successfully$(NC)"

# Utility targets
health: ## Check health of running services
	@echo "$(BLUE)🔍 Checking service health...$(NC)"
	@echo "$(YELLOW)Backend health:$(NC)"
	@curl -f http://localhost:$(BACKEND_PORT)/health 2>/dev/null | python3 -m json.tool || echo "$(RED)❌ Backend not responding$(NC)"
	@echo "\n$(YELLOW)Frontend status:$(NC)"
	@curl -f http://localhost:$(FRONTEND_PORT) >/dev/null 2>&1 && echo "$(GREEN)✅ Frontend responding$(NC)" || echo "$(RED)❌ Frontend not responding$(NC)"

dev-logs: ## Show logs from both services
	@echo "$(BLUE)📋 Service logs (press Ctrl+C to exit):$(NC)"
	@tail -f backend/*.log image-canvas/*.log 2>/dev/null || echo "$(YELLOW)No log files found - logs appear in terminal$(NC)"

check-deps: ## Check if all dependencies are available
	@echo "$(BLUE)🔍 Checking dependencies...$(NC)"
	@echo "$(YELLOW)Python version:$(NC)"
	@python3 --version || echo "$(RED)❌ Python 3 not found$(NC)"
	@echo "$(YELLOW)Node.js version:$(NC)"
	@node --version || echo "$(RED)❌ Node.js not found$(NC)"
	@echo "$(YELLOW)npm version:$(NC)"
	@npm --version || echo "$(RED)❌ npm not found$(NC)"
	@echo "$(YELLOW)Virtual environment:$(NC)"
	@[ -d "$(VENV_PATH)" ] && echo "$(GREEN)✅ Virtual environment exists$(NC)" || echo "$(RED)❌ Virtual environment not found$(NC)"
	@echo "$(YELLOW)Backend dependencies:$(NC)"
	@[ -f "backend/requirements.txt" ] && echo "$(GREEN)✅ requirements.txt found$(NC)" || echo "$(RED)❌ requirements.txt not found$(NC)"
	@echo "$(YELLOW)Frontend dependencies:$(NC)"
	@[ -f "image-canvas/package.json" ] && echo "$(GREEN)✅ package.json found$(NC)" || echo "$(RED)❌ package.json not found$(NC)"

# Cleanup targets
clean: kill-ports ## Stop all services and clean temporary files
	@echo "$(YELLOW)🧹 Cleaning up...$(NC)"
	@rm -rf backend/__pycache__ backend/*.pyc
	@rm -rf image-canvas/dist image-canvas/node_modules/.cache
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

kill-ports: kill-backend kill-frontend ## Kill processes on both frontend and backend ports

kill-backend: ## Kill processes running on backend port
	@echo "$(YELLOW)🔌 Stopping backend services on port $(BACKEND_PORT)...$(NC)"
	@lsof -ti:$(BACKEND_PORT) | xargs kill -9 2>/dev/null || true
	@pkill -f "uvicorn.*main:app" 2>/dev/null || true
	@pkill -f "python.*start.py" 2>/dev/null || true

kill-frontend: ## Kill processes running on frontend port  
	@echo "$(YELLOW)🔌 Stopping frontend services on port $(FRONTEND_PORT)...$(NC)"
	@lsof -ti:$(FRONTEND_PORT) | xargs kill -9 2>/dev/null || true
	@pkill -f "vite.*dev" 2>/dev/null || true

# Testing targets
test-connection: ## Test if backend is responding
	@echo "$(BLUE)🔗 Testing backend connection...$(NC)"
	@curl -X POST http://localhost:$(BACKEND_PORT)/debug/simple-test 2>/dev/null | python3 -m json.tool || echo "$(RED)❌ Backend connection failed$(NC)"

test-ai: ## Test AI analysis pipeline
	@echo "$(BLUE)🤖 Testing AI analysis...$(NC)"
	@curl -X POST http://localhost:$(BACKEND_PORT)/debug/test-analysis 2>/dev/null | python3 -m json.tool || echo "$(RED)❌ AI analysis test failed$(NC)"

# Development utility targets
logs-backend: ## Show backend logs
	@cd backend && $(PYTHON) -c "import sys; print('Backend logs:', sys.executable)"

logs-frontend: ## Show frontend logs  
	@cd image-canvas && npm run dev 2>&1 | grep -E "(Local|ready|error)"

wait-for-interrupt: ## Wait for user interrupt (used internally)
	@trap 'echo "\n$(YELLOW)🛑 Stopping all services...$(NC)"; $(MAKE) --no-print-directory kill-ports; exit 0' INT; \
	while true; do sleep 1; done

# Quick development targets
dev: start ## Alias for start (quick development)

run: start ## Alias for start  

serve: start ## Alias for start

# Environment management
env-check: ## Check environment variables
	@echo "$(BLUE)🔍 Environment configuration:$(NC)"
	@echo "$(YELLOW)Backend .env file:$(NC)"
	@[ -f "backend/.env" ] && echo "$(GREEN)✅ Found$(NC)" || echo "$(RED)❌ Not found - run 'make setup'$(NC)"
	@[ -f "backend/.env" ] && echo "$(YELLOW)Contents:$(NC)" && grep -v "^#\|^$$" backend/.env | sed 's/=.*$$/=***/' || true

env-template: ## Recreate .env from template
	@echo "$(YELLOW)📄 Recreating .env file...$(NC)"
	@cp backend/env.config backend/.env
	@echo "$(GREEN)✅ .env file created from template$(NC)"
	@echo "$(YELLOW)⚠️  Please edit backend/.env with your actual API keys$(NC)"

# Documentation
docs: ## Open API documentation in browser
	@echo "$(BLUE)📚 Opening API documentation...$(NC)"
	@open http://localhost:$(BACKEND_PORT)/docs 2>/dev/null || \
	 xdg-open http://localhost:$(BACKEND_PORT)/docs 2>/dev/null || \
	 echo "$(YELLOW)📱 Manual: http://localhost:$(BACKEND_PORT)/docs$(NC)"

# Advanced targets
debug: ## Start services with debug information
	@echo "$(BLUE)🔍 Starting in debug mode...$(NC)"
	@$(MAKE) --no-print-directory check-deps
	@$(MAKE) --no-print-directory env-check  
	@$(MAKE) --no-print-directory start

monitor: health ## Monitor service health continuously
	@echo "$(BLUE)📊 Monitoring services (Ctrl+C to stop)...$(NC)"
	@while true; do \
		$(MAKE) --no-print-directory health; \
		sleep 10; \
		echo "$(YELLOW)---$(NC)"; \
	done

# Platform-specific notes
.ONESHELL:
ifeq ($(OS),Windows_NT)
    SHELL := cmd.exe
    PYTHON := $(VENV_PATH)/Scripts/python.exe
    PIP := $(VENV_PATH)/Scripts/pip.exe
endif
