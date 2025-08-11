#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "🗄️ Validating database migrations..."

cd "$PROJECT_ROOT"

# Check if migration files were modified
MIGRATION_CHANGES=$(git diff --cached --name-only | grep "docker/init-scripts" || true)

if [[ -z "$MIGRATION_CHANGES" ]]; then
    log "✅ No migration changes detected"
    exit 0
fi

log "📋 Migration changes detected, running validation..."

# Validate SQL syntax in migration files
for file in $MIGRATION_CHANGES; do
    if [[ "$file" == *.sql ]]; then
        log "Validating SQL file: $file"
        
        # Basic SQL syntax checks
        if grep -q "CREATE TABLE.*(" "$file" && ! grep -q "IF NOT EXISTS" "$file"; then
            log "⚠️  WARNING: $file creates table without IF NOT EXISTS"
        fi
        
        if grep -q "DROP TABLE" "$file" && ! grep -q "IF EXISTS" "$file"; then
            log "⚠️  WARNING: $file drops table without IF EXISTS"
        fi
        
        # Check for dangerous operations
        if grep -qi "DROP DATABASE\|TRUNCATE\|DELETE FROM.*WHERE" "$file"; then
            log "⚠️  WARNING: $file contains potentially dangerous operations"
        fi
        
        # Validate SQL can be parsed (basic check)
        if ! python3 -c "
import re
with open('$file') as f:
    content = f.read()
    
# Remove comments and check for basic SQL structure
content = re.sub(r'--.*', '', content)
content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

if content.strip() and not re.search(r'(CREATE|ALTER|DROP|INSERT|UPDATE|DELETE)', content, re.IGNORECASE):
    print('❌ No valid SQL statements found')
    exit(1)
else:
    print('✅ Basic SQL structure valid')
"; then
            log "❌ SQL validation failed for $file"
            exit 1
        fi
    fi
done

log "✅ Database migration validation passed"