#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "🧹 Cleaning up test environment..."

cd "$PROJECT_ROOT"

# Stop and remove all containers
log "Stopping Docker containers..."
docker compose -f docker/docker-compose.dev.yml down --remove-orphans 2>/dev/null || true
docker compose -f docker/docker-compose.test.yml down --remove-orphans 2>/dev/null || true

# Remove test volumes
log "Removing test volumes..."
docker volume prune -f 2>/dev/null || true

# Clean up test artifacts
log "Cleaning up test artifacts..."
rm -rf api/.pytest_cache api/__pycache__ api/*.pyc 2>/dev/null || true
rm -rf api/htmlcov api/.coverage 2>/dev/null || true

# Clean up temporary files
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.log" -delete 2>/dev/null || true

log "✅ Environment cleanup completed"