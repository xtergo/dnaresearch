#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "📋 Validating JSON schemas..."

cd "$PROJECT_ROOT"

# Install jsonschema if not present
if ! python3 -c "import jsonschema" 2>/dev/null; then
    log "Installing jsonschema..."
    pip install jsonschema
fi

# Validate all JSON schema files
SCHEMA_ERRORS=0

for schema_file in schemas/*.json; do
    if [[ -f "$schema_file" ]]; then
        log "Validating schema: $schema_file"
        
        # Check if it's valid JSON
        if ! python3 -c "import json; json.load(open('$schema_file'))" 2>/dev/null; then
            log "❌ Invalid JSON in $schema_file"
            SCHEMA_ERRORS=$((SCHEMA_ERRORS + 1))
            continue
        fi
        
        # Validate against JSON Schema meta-schema
        if ! python3 -c "
import json
import jsonschema
from jsonschema import Draft202012Validator

with open('$schema_file') as f:
    schema = json.load(f)

try:
    Draft202012Validator.check_schema(schema)
    print('✅ Schema $schema_file is valid')
except jsonschema.SchemaError as e:
    print(f'❌ Schema $schema_file is invalid: {e}')
    exit(1)
"; then
            SCHEMA_ERRORS=$((SCHEMA_ERRORS + 1))
        fi
    fi
done

if [[ $SCHEMA_ERRORS -gt 0 ]]; then
    log "❌ Found $SCHEMA_ERRORS schema validation errors"
    exit 1
fi

log "✅ All JSON schemas are valid"