#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load configuration
source "$SCRIPT_DIR/load-config.sh"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "🧪 Running unit tests..."

cd "$PROJECT_ROOT"

if [[ "$ENVIRONMENT_TYPE" == "docker" ]]; then
    # Run tests in Docker environment
    log "Using Docker environment for unit tests"
    
    # Build test image if needed
    if [[ "$DOCKER_BUILD_FAST" == "false" ]]; then
        docker compose -f docker/docker-compose.test.yml build --no-cache
    else
        docker compose -f docker/docker-compose.test.yml build
    fi
    
    # Run unit tests
    if [[ "$PARALLEL_TESTS" == "true" ]]; then
        docker compose -f docker/docker-compose.test.yml run --rm api pytest -v -n auto --cov=. --cov-report=xml --cov-report=term-missing
    else
        docker compose -f docker/docker-compose.test.yml run --rm api pytest -v --cov=. --cov-report=xml --cov-report=term-missing
    fi
    
    # Store test results
    if [[ "$STORE_TEST_RESULTS" == "true" ]]; then
        mkdir -p test-results/unit
        docker compose -f docker/docker-compose.test.yml run --rm api pytest --junitxml=/tmp/unit-test-results.xml
        docker cp $(docker compose -f docker/docker-compose.test.yml ps -q api):/tmp/unit-test-results.xml test-results/unit/ 2>/dev/null || true
    fi
    
else
    # Run tests in local environment
    log "Using local environment for unit tests"
    
    cd api
    
    if [[ "$PARALLEL_TESTS" == "true" ]]; then
        pytest -v -n auto --cov=. --cov-report=xml --cov-report=term-missing
    else
        pytest -v --cov=. --cov-report=xml --cov-report=term-missing
    fi
    
    # Store test results
    if [[ "$STORE_TEST_RESULTS" == "true" ]]; then
        mkdir -p ../test-results/unit
        pytest --junitxml=../test-results/unit/unit-test-results.xml
    fi
fi

log "✅ Unit tests completed successfully"