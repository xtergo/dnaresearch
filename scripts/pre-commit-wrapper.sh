#!/bin/bash
set -euo pipefail

# Pre-commit wrapper that handles metrics file staging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set environment variable to indicate we're in pre-commit mode
export PRE_COMMIT=1

# Run the main validation
"$SCRIPT_DIR/pre-commit-validation.sh"
VALIDATION_EXIT_CODE=$?

exit $VALIDATION_EXIT_CODE