#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "🔍 Running Python linting..."

cd "$PROJECT_ROOT"

# Install linting tools if not present
if ! command -v flake8 &> /dev/null; then
    log "Installing flake8..."
    pip install flake8 black isort
fi

# Run Black formatter check
log "Checking code formatting with Black..."
if ! black --check --diff api/; then
    log "❌ Code formatting issues found. Run 'black api/' to fix."
    exit 1
fi

# Run isort import sorting check
log "Checking import sorting with isort..."
if ! isort --check-only --diff api/; then
    log "❌ Import sorting issues found. Run 'isort api/' to fix."
    exit 1
fi

# Run flake8 linting
log "Running flake8 linting..."
if ! flake8 api/ --max-line-length=100 --extend-ignore=E203,W503,E501; then
    log "❌ Linting issues found."
    exit 1
fi

log "✅ Python linting passed"