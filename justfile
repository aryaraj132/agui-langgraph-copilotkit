# Default recipe
default:
    @just --list

# Install all dependencies (backend + frontend)
prepare:
    uv sync
    cd frontend && npm install

# Install backend dependencies only
install:
    uv sync

# Run the FastAPI backend server
backend:
    uv run python -m agui_backend_demo.main

# Run the Next.js frontend dev server
frontend:
    cd frontend && npm run dev

# Run backend (alias for backward compat)
run: backend

# Run linter
lint:
    uv run ruff check

# Run linter with auto-fix
lint-fix:
    uv run ruff check --fix

# Check formatting
format-check:
    uv run ruff format --check

# Fix formatting
format:
    uv run ruff format

# Run all checks (lint + format)
check: lint format-check

# Fix all issues (lint + format)
fix: lint-fix format

# Run tests
test:
    uv run pytest tests/
