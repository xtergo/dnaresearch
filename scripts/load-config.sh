#!/bin/bash

# Load DNA Research Platform Development Configuration
# Sets default values and loads from config file

# Default configuration values
VERIFY_PRE_COMMIT=${VERIFY_PRE_COMMIT:-true}
ENVIRONMENT_TYPE=${ENVIRONMENT_TYPE:-docker}
ENABLE_COVERAGE_METRICS=${ENABLE_COVERAGE_METRICS:-true}
ENFORCE_COVERAGE_THRESHOLD=${ENFORCE_COVERAGE_THRESHOLD:-false}
COVERAGE_THRESHOLD=${COVERAGE_THRESHOLD:-80}
REQUIRE_ALL_TESTS_PASS=${REQUIRE_ALL_TESTS_PASS:-true}
ENFORCE_TEST_DURATION_THRESHOLD=${ENFORCE_TEST_DURATION_THRESHOLD:-true}
TEST_DURATION_THRESHOLD_SEC=${TEST_DURATION_THRESHOLD_SEC:-30}
CLEANUP_AFTER_TESTS=${CLEANUP_AFTER_TESTS:-true}
TEST_TYPES=${TEST_TYPES:-all}
STORE_TEST_RESULTS=${STORE_TEST_RESULTS:-true}
DB_LINT_ENABLED=${DB_LINT_ENABLED:-true}
PYTHON_LINT_ENABLED=${PYTHON_LINT_ENABLED:-true}
SCHEMA_VALIDATION_ENABLED=${SCHEMA_VALIDATION_ENABLED:-true}
API_DOCS_VALIDATION_ENABLED=${API_DOCS_VALIDATION_ENABLED:-true}
DOCKER_BUILD_FAST=${DOCKER_BUILD_FAST:-true}
PARALLEL_TESTS=${PARALLEL_TESTS:-true}
E2E_TIMEOUT_SEC=${E2E_TIMEOUT_SEC:-300}
VALIDATE_MIGRATIONS=${VALIDATE_MIGRATIONS:-true}
SECURITY_SCAN_ENABLED=${SECURITY_SCAN_ENABLED:-false}
PERFORMANCE_TEST_ENABLED=${PERFORMANCE_TEST_ENABLED:-false}
LOG_LEVEL=${LOG_LEVEL:-INFO}
STORE_METRICS=${STORE_METRICS:-true}

# Load configuration from file if it exists
if [[ -f "$CONFIG_FILE" ]]; then
    # Source the config file, ignoring comments and empty lines
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z $key ]] && continue
        
        # Remove leading/trailing whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        # Export the variable
        if [[ -n $key && -n $value ]]; then
            export "$key"="$value"
        fi
    done < "$CONFIG_FILE"
fi

# Validate configuration values
validate_boolean() {
    local var_name="$1"
    local var_value="${!var_name}"
    
    if [[ "$var_value" != "true" && "$var_value" != "false" ]]; then
        echo "ERROR: $var_name must be 'true' or 'false', got '$var_value'"
        exit 1
    fi
}

validate_number() {
    local var_name="$1"
    local var_value="${!var_name}"
    local min_val="${2:-0}"
    local max_val="${3:-999999}"
    
    if ! [[ "$var_value" =~ ^[0-9]+$ ]] || [[ $var_value -lt $min_val ]] || [[ $var_value -gt $max_val ]]; then
        echo "ERROR: $var_name must be a number between $min_val and $max_val, got '$var_value'"
        exit 1
    fi
}

# Validate boolean configurations
validate_boolean "VERIFY_PRE_COMMIT"
validate_boolean "ENABLE_COVERAGE_METRICS"
validate_boolean "ENFORCE_COVERAGE_THRESHOLD"
validate_boolean "REQUIRE_ALL_TESTS_PASS"
validate_boolean "ENFORCE_TEST_DURATION_THRESHOLD"
validate_boolean "CLEANUP_AFTER_TESTS"
validate_boolean "STORE_TEST_RESULTS"
validate_boolean "DB_LINT_ENABLED"
validate_boolean "PYTHON_LINT_ENABLED"
validate_boolean "SCHEMA_VALIDATION_ENABLED"
validate_boolean "API_DOCS_VALIDATION_ENABLED"
validate_boolean "DOCKER_BUILD_FAST"
validate_boolean "PARALLEL_TESTS"
validate_boolean "VALIDATE_MIGRATIONS"
validate_boolean "SECURITY_SCAN_ENABLED"
validate_boolean "PERFORMANCE_TEST_ENABLED"
validate_boolean "STORE_METRICS"

# Validate numeric configurations
validate_number "COVERAGE_THRESHOLD" 0 100
validate_number "TEST_DURATION_THRESHOLD_SEC" 1 3600
validate_number "E2E_TIMEOUT_SEC" 30 1800

# Validate enum configurations
if [[ "$ENVIRONMENT_TYPE" != "docker" && "$ENVIRONMENT_TYPE" != "local" ]]; then
    echo "ERROR: ENVIRONMENT_TYPE must be 'docker' or 'local', got '$ENVIRONMENT_TYPE'"
    exit 1
fi

if [[ "$LOG_LEVEL" != "DEBUG" && "$LOG_LEVEL" != "INFO" && "$LOG_LEVEL" != "WARN" && "$LOG_LEVEL" != "ERROR" ]]; then
    echo "ERROR: LOG_LEVEL must be one of DEBUG/INFO/WARN/ERROR, got '$LOG_LEVEL'"
    exit 1
fi

# Export all variables for use in other scripts
export VERIFY_PRE_COMMIT ENVIRONMENT_TYPE ENABLE_COVERAGE_METRICS ENFORCE_COVERAGE_THRESHOLD
export COVERAGE_THRESHOLD REQUIRE_ALL_TESTS_PASS ENFORCE_TEST_DURATION_THRESHOLD
export TEST_DURATION_THRESHOLD_SEC CLEANUP_AFTER_TESTS TEST_TYPES STORE_TEST_RESULTS
export DB_LINT_ENABLED PYTHON_LINT_ENABLED SCHEMA_VALIDATION_ENABLED API_DOCS_VALIDATION_ENABLED
export DOCKER_BUILD_FAST PARALLEL_TESTS E2E_TIMEOUT_SEC VALIDATE_MIGRATIONS
export SECURITY_SCAN_ENABLED PERFORMANCE_TEST_ENABLED LOG_LEVEL STORE_METRICS