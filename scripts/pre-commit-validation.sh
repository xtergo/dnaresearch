#!/bin/bash
set -euo pipefail

# DNA Research Platform Pre-commit Validation
# Comprehensive validation pipeline for genomic research platform

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/.dnaresearch-dev-config"
METRICS_DIR="$PROJECT_ROOT/metrics"
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results"

# Load configuration
source "$SCRIPT_DIR/load-config.sh"

# Initialize directories
mkdir -p "$METRICS_DIR" "$TEST_RESULTS_DIR"

# Logging function
log() {
    local level="$1"
    shift
    if [[ "$LOG_LEVEL" == "DEBUG" ]] || [[ "$level" != "DEBUG" ]]; then
        echo "[$level] $(date '+%Y-%m-%d %H:%M:%S') $*"
    fi
}

# Metrics collection
collect_metric() {
    local metric_name="$1"
    local metric_value="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [[ "$STORE_METRICS" == "true" ]]; then
        echo "$timestamp,$metric_name,$metric_value" >> "$METRICS_DIR/pre-commit-metrics.csv"
    fi
}

# Timer functions
start_timer() {
    echo $(date +%s)
}

end_timer() {
    local start_time="$1"
    local end_time=$(date +%s)
    echo $((end_time - start_time))
}

log "INFO" "🧬 DNA Research Platform Pre-commit Validation Starting..."

TOTAL_START=$(start_timer)

# 1. Python Linting
if [[ "$PYTHON_LINT_ENABLED" == "true" ]]; then
    log "INFO" "🔍 Running Python linting..."
    LINT_START=$(start_timer)
    
    if ! "$SCRIPT_DIR/python-lint.sh"; then
        log "ERROR" "❌ Python linting failed"
        exit 1
    fi
    
    LINT_DURATION=$(end_timer $LINT_START)
    collect_metric "python_lint_duration_sec" "$LINT_DURATION"
    log "INFO" "✅ Python linting passed (${LINT_DURATION}s)"
fi

# 2. JSON Schema Validation
if [[ "$SCHEMA_VALIDATION_ENABLED" == "true" ]]; then
    log "INFO" "📋 Validating JSON schemas..."
    SCHEMA_START=$(start_timer)
    
    if ! "$SCRIPT_DIR/validate-schemas.sh"; then
        log "ERROR" "❌ Schema validation failed"
        exit 1
    fi
    
    SCHEMA_DURATION=$(end_timer $SCHEMA_START)
    collect_metric "schema_validation_duration_sec" "$SCHEMA_DURATION"
    log "INFO" "✅ Schema validation passed (${SCHEMA_DURATION}s)"
fi

# 3. Database Migration Validation
if [[ "$VALIDATE_MIGRATIONS" == "true" ]]; then
    log "INFO" "🗄️ Validating database migrations..."
    MIGRATION_START=$(start_timer)
    
    if ! "$SCRIPT_DIR/validate-migrations.sh"; then
        log "ERROR" "❌ Migration validation failed"
        exit 1
    fi
    
    MIGRATION_DURATION=$(end_timer $MIGRATION_START)
    collect_metric "migration_validation_duration_sec" "$MIGRATION_DURATION"
    log "INFO" "✅ Migration validation passed (${MIGRATION_DURATION}s)"
fi

# 4. Unit Tests
log "INFO" "🧪 Running unit tests..."
UNIT_TEST_START=$(start_timer)

if ! "$SCRIPT_DIR/run-unit-tests.sh"; then
    log "ERROR" "❌ Unit tests failed"
    exit 1
fi

UNIT_TEST_DURATION=$(end_timer $UNIT_TEST_START)
collect_metric "unit_test_duration_sec" "$UNIT_TEST_DURATION"

if [[ "$ENFORCE_TEST_DURATION_THRESHOLD" == "true" ]] && [[ $UNIT_TEST_DURATION -gt $TEST_DURATION_THRESHOLD_SEC ]]; then
    log "ERROR" "❌ Unit tests exceeded duration threshold (${UNIT_TEST_DURATION}s > ${TEST_DURATION_THRESHOLD_SEC}s)"
    exit 1
fi

log "INFO" "✅ Unit tests passed (${UNIT_TEST_DURATION}s)"

# 5. Integration Tests
if [[ "$TEST_TYPES" == "all" ]] || [[ "$TEST_TYPES" == *"integration"* ]]; then
    log "INFO" "🔗 Running integration tests..."
    INTEGRATION_START=$(start_timer)
    
    if ! "$SCRIPT_DIR/run-integration-tests.sh"; then
        log "ERROR" "❌ Integration tests failed"
        exit 1
    fi
    
    INTEGRATION_DURATION=$(end_timer $INTEGRATION_START)
    collect_metric "integration_test_duration_sec" "$INTEGRATION_DURATION"
    log "INFO" "✅ Integration tests passed (${INTEGRATION_DURATION}s)"
fi

# 6. E2E Tests
if [[ "$TEST_TYPES" == "all" ]] || [[ "$TEST_TYPES" == *"e2e"* ]]; then
    log "INFO" "🌐 Running E2E tests..."
    E2E_START=$(start_timer)
    
    if ! timeout "$E2E_TIMEOUT_SEC" "$SCRIPT_DIR/run-e2e-tests.sh"; then
        log "ERROR" "❌ E2E tests failed or timed out"
        exit 1
    fi
    
    E2E_DURATION=$(end_timer $E2E_START)
    collect_metric "e2e_test_duration_sec" "$E2E_DURATION"
    log "INFO" "✅ E2E tests passed (${E2E_DURATION}s)"
fi

# 7. Coverage Analysis
if [[ "$ENABLE_COVERAGE_METRICS" == "true" ]]; then
    log "INFO" "📊 Analyzing test coverage..."
    COVERAGE_START=$(start_timer)
    
    COVERAGE_PERCENT=$("$SCRIPT_DIR/analyze-coverage.sh")
    
    if [[ "$ENFORCE_COVERAGE_THRESHOLD" == "true" ]] && [[ $(echo "$COVERAGE_PERCENT < $COVERAGE_THRESHOLD" | bc -l) -eq 1 ]]; then
        log "ERROR" "❌ Coverage below threshold (${COVERAGE_PERCENT}% < ${COVERAGE_THRESHOLD}%)"
        exit 1
    fi
    
    COVERAGE_DURATION=$(end_timer $COVERAGE_START)
    collect_metric "coverage_analysis_duration_sec" "$COVERAGE_DURATION"
    collect_metric "test_coverage_percent" "$COVERAGE_PERCENT"
    
    # Coverage summary is already printed by analyze-coverage.sh
    log "INFO" "✅ Coverage analysis completed (${COVERAGE_DURATION}s)"
fi

# 8. Security Scan
if [[ "$SECURITY_SCAN_ENABLED" == "true" ]]; then
    log "INFO" "🔒 Running security scan..."
    SECURITY_START=$(start_timer)
    
    if ! "$SCRIPT_DIR/security-scan.sh"; then
        log "ERROR" "❌ Security scan failed"
        exit 1
    fi
    
    SECURITY_DURATION=$(end_timer $SECURITY_START)
    collect_metric "security_scan_duration_sec" "$SECURITY_DURATION"
    log "INFO" "✅ Security scan passed (${SECURITY_DURATION}s)"
fi

# 9. Performance Tests
if [[ "$PERFORMANCE_TEST_ENABLED" == "true" ]]; then
    log "INFO" "⚡ Running performance tests..."
    PERF_START=$(start_timer)
    
    if ! "$SCRIPT_DIR/run-performance-tests.sh"; then
        log "ERROR" "❌ Performance tests failed"
        exit 1
    fi
    
    PERF_DURATION=$(end_timer $PERF_START)
    collect_metric "performance_test_duration_sec" "$PERF_DURATION"
    log "INFO" "✅ Performance tests passed (${PERF_DURATION}s)"
fi

# 10. Cleanup
if [[ "$CLEANUP_AFTER_TESTS" == "true" ]]; then
    log "INFO" "🧹 Cleaning up test environment..."
    "$SCRIPT_DIR/cleanup-environment.sh" || true
fi

TOTAL_DURATION=$(end_timer $TOTAL_START)
collect_metric "total_validation_duration_sec" "$TOTAL_DURATION"

log "INFO" "🎉 All validations passed! Total time: ${TOTAL_DURATION}s"
log "INFO" "📈 Metrics stored in: $METRICS_DIR/pre-commit-metrics.csv"

if [[ "$STORE_TEST_RESULTS" == "true" ]]; then
    log "INFO" "📋 Test results stored in: $TEST_RESULTS_DIR/"
fi

exit 0