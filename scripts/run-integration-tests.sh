#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load configuration
source "$SCRIPT_DIR/load-config.sh"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "🔗 Running integration tests..."

cd "$PROJECT_ROOT"

# Start test environment
log "Starting integration test environment..."
docker compose -f docker/docker-compose.test.yml up -d --build

# Wait for services to be ready
log "Waiting for test services to be ready..."
timeout 30 bash -c 'until docker compose -f docker/docker-compose.test.yml exec postgres_test pg_isready -U test_user -d dnaresearch_test; do sleep 2; done'

# Run integration tests
log "Running integration test suite..."
docker compose -f docker/docker-compose.test.yml run --rm api python -m pytest tests/integration/ -v

# Store test results
if [[ "$STORE_TEST_RESULTS" == "true" ]]; then
    mkdir -p test-results/integration
    docker compose -f docker/docker-compose.test.yml run --rm api python -m pytest tests/integration/ --junitxml=/tmp/integration-results.xml
    docker cp $(docker compose -f docker/docker-compose.test.yml ps -q api):/tmp/integration-results.xml test-results/integration/ 2>/dev/null || true
fi

# Cleanup
if [[ "$CLEANUP_AFTER_TESTS" == "true" ]]; then
    log "Cleaning up integration test environment..."
    docker compose -f docker/docker-compose.test.yml down -v
fi

log "✅ Integration tests completed successfully"