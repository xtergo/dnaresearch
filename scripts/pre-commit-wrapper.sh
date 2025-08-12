#!/bin/bash
set -euo pipefail

# Pre-commit wrapper that handles metrics file staging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the main validation
"$SCRIPT_DIR/pre-commit-validation.sh"
VALIDATION_EXIT_CODE=$?

# If validation passed, stage any updated metrics files
if [[ $VALIDATION_EXIT_CODE -eq 0 ]]; then
    # Stage metrics files if they exist and were modified
    if [[ -f "metrics/pre-commit-metrics.csv" ]]; then
        git add metrics/pre-commit-metrics.csv 2>/dev/null || true
    fi
    
    if [[ -f "metrics/coverage-metrics.csv" ]]; then
        git add metrics/coverage-metrics.csv 2>/dev/null || true
    fi
fi

exit $VALIDATION_EXIT_CODE