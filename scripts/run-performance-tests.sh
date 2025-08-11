#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load configuration
source "$SCRIPT_DIR/load-config.sh"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "⚡ Running performance tests..."

cd "$PROJECT_ROOT"

# Ensure test results directory exists
mkdir -p test-results/performance

# Start the API server if not running
if [[ "$ENVIRONMENT_TYPE" == "docker" ]]; then
    log "Starting API server in Docker..."
    docker compose -f docker/docker-compose.test.yml up -d api
    
    # Wait for API to be ready
    log "Waiting for API to be ready..."
    timeout 30 bash -c 'until curl -s http://localhost:8000/health > /dev/null; do sleep 1; done'
    
    API_BASE_URL="http://localhost:8000"
else
    log "Using local API server at $API_BASE_URL"
fi

# Install locust if not available
if ! command -v locust &> /dev/null; then
    log "Installing Locust..."
    pip install locust
fi

# Run load tests
log "Running load tests with Locust..."

# Run different test scenarios
SCENARIOS=(
    "health:10:30"      # 10 users for 30 seconds
    "gene_search:20:60" # 20 users for 60 seconds  
    "theory_exec:5:30"  # 5 users for 30 seconds (heavy operations)
)

for scenario in "${SCENARIOS[@]}"; do
    IFS=':' read -r test_name users duration <<< "$scenario"
    
    log "Running $test_name scenario: $users users for ${duration}s"
    
    locust \
        -f "$PROJECT_ROOT/tests/performance/locustfile.py" \
        --headless \
        --users "$users" \
        --spawn-rate 2 \
        --run-time "${duration}s" \
        --host "$API_BASE_URL" \
        --html "test-results/performance/${test_name}_report.html" \
        --csv "test-results/performance/${test_name}" \
        --tags "$test_name" \
        --loglevel INFO
done

# Analyze results
log "📊 Analyzing performance results..."
python3 "$PROJECT_ROOT/scripts/analyze-performance.py" "$PROJECT_ROOT/test-results/performance"

# Cleanup
if [[ "$ENVIRONMENT_TYPE" == "docker" ]]; then
    docker compose -f docker/docker-compose.test.yml down
fi

log "✅ Performance tests completed successfully"
log "📊 Results available in test-results/performance/"
log "📋 Summary report: test-results/performance/performance_summary.json"