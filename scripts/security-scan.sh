#!/bin/bash
set -euo pipefail

# DNA Research Platform Security Scanner
# Comprehensive security vulnerability assessment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SECURITY_REPORT_DIR="$PROJECT_ROOT/security-reports"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Create security reports directory
mkdir -p "$SECURITY_REPORT_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "🔒 Starting DNA Research Platform Security Scan..."

# 1. Python Dependency Vulnerability Scan
log "📦 Scanning Python dependencies for vulnerabilities..."
if command -v safety >/dev/null 2>&1; then
    safety check --json > "$SECURITY_REPORT_DIR/dependency_scan_$TIMESTAMP.json" 2>/dev/null || {
        log "⚠️  Safety scan found vulnerabilities - see report"
    }
    safety check --short-report > "$SECURITY_REPORT_DIR/dependency_summary_$TIMESTAMP.txt" 2>/dev/null || true
else
    log "⚠️  Safety not installed - installing..."
    pip install safety
    safety check --json > "$SECURITY_REPORT_DIR/dependency_scan_$TIMESTAMP.json" 2>/dev/null || {
        log "⚠️  Safety scan found vulnerabilities - see report"
    }
fi

# 2. Docker Security Scan
log "🐳 Scanning Docker configurations..."
DOCKER_ISSUES=0

# Check for security best practices in Dockerfiles
find "$PROJECT_ROOT/docker" -name "Dockerfile*" | while read -r dockerfile; do
    log "  Checking $dockerfile..."
    
    # Check for root user
    if grep -q "USER root" "$dockerfile" 2>/dev/null; then
        echo "SECURITY: $dockerfile uses root user" >> "$SECURITY_REPORT_DIR/docker_issues_$TIMESTAMP.txt"
        ((DOCKER_ISSUES++))
    fi
    
    # Check for latest tags
    if grep -q ":latest" "$dockerfile" 2>/dev/null; then
        echo "SECURITY: $dockerfile uses :latest tag" >> "$SECURITY_REPORT_DIR/docker_issues_$TIMESTAMP.txt"
        ((DOCKER_ISSUES++))
    fi
    
    # Check for ADD instead of COPY
    if grep -q "^ADD " "$dockerfile" 2>/dev/null; then
        echo "SECURITY: $dockerfile uses ADD instead of COPY" >> "$SECURITY_REPORT_DIR/docker_issues_$TIMESTAMP.txt"
        ((DOCKER_ISSUES++))
    fi
done

# 3. API Security Analysis
log "🔐 Analyzing API security configurations..."
API_ISSUES=0

# Check for hardcoded secrets
log "  Checking for hardcoded secrets..."
if grep -r -i "password\|secret\|key\|token" "$PROJECT_ROOT/api" --include="*.py" | grep -v "test_" | grep -E "(=|:)" | grep -v "# " > "$SECURITY_REPORT_DIR/potential_secrets_$TIMESTAMP.txt" 2>/dev/null; then
    API_ISSUES=$((API_ISSUES + $(wc -l < "$SECURITY_REPORT_DIR/potential_secrets_$TIMESTAMP.txt")))
    log "  ⚠️  Found potential hardcoded secrets"
else
    echo "No hardcoded secrets detected" > "$SECURITY_REPORT_DIR/potential_secrets_$TIMESTAMP.txt"
fi

# Check for SQL injection patterns
log "  Checking for SQL injection vulnerabilities..."
if grep -r "execute.*%" "$PROJECT_ROOT/api" --include="*.py" > "$SECURITY_REPORT_DIR/sql_injection_$TIMESTAMP.txt" 2>/dev/null; then
    API_ISSUES=$((API_ISSUES + $(wc -l < "$SECURITY_REPORT_DIR/sql_injection_$TIMESTAMP.txt")))
    log "  ⚠️  Found potential SQL injection patterns"
else
    echo "No SQL injection patterns detected" > "$SECURITY_REPORT_DIR/sql_injection_$TIMESTAMP.txt"
fi

# 4. File Permission Analysis
log "🔑 Checking file permissions..."
PERM_ISSUES=0

# Check for overly permissive files
find "$PROJECT_ROOT" -type f -perm -o+w 2>/dev/null | grep -v ".git" > "$SECURITY_REPORT_DIR/world_writable_$TIMESTAMP.txt" || true
if [ -s "$SECURITY_REPORT_DIR/world_writable_$TIMESTAMP.txt" ]; then
    PERM_ISSUES=$((PERM_ISSUES + $(wc -l < "$SECURITY_REPORT_DIR/world_writable_$TIMESTAMP.txt")))
    log "  ⚠️  Found world-writable files"
fi

# 5. Configuration Security
log "⚙️  Analyzing configuration security..."
CONFIG_ISSUES=0

# Check for debug mode in production configs
if grep -r "debug.*=.*true\|DEBUG.*=.*True" "$PROJECT_ROOT" --include="*.py" --include="*.yml" --include="*.yaml" > "$SECURITY_REPORT_DIR/debug_mode_$TIMESTAMP.txt" 2>/dev/null; then
    CONFIG_ISSUES=$((CONFIG_ISSUES + $(wc -l < "$SECURITY_REPORT_DIR/debug_mode_$TIMESTAMP.txt")))
    log "  ⚠️  Found debug mode enabled"
else
    echo "No debug mode issues detected" > "$SECURITY_REPORT_DIR/debug_mode_$TIMESTAMP.txt"
fi

# 6. Generate Security Summary Report
log "📊 Generating security summary report..."
cat > "$SECURITY_REPORT_DIR/security_summary_$TIMESTAMP.md" << EOF
# DNA Research Platform Security Scan Report

**Scan Date**: $(date)
**Scan ID**: $TIMESTAMP

## Summary

| Category | Issues Found |
|----------|--------------|
| Dependencies | See dependency report |
| Docker | $DOCKER_ISSUES |
| API Security | $API_ISSUES |
| File Permissions | $PERM_ISSUES |
| Configuration | $CONFIG_ISSUES |

## Dependency Vulnerabilities

$(cat "$SECURITY_REPORT_DIR/dependency_summary_$TIMESTAMP.txt" 2>/dev/null || echo "Dependency scan completed - see JSON report for details")

## Recommendations

### High Priority
1. Review and remediate any dependency vulnerabilities
2. Fix hardcoded secrets if found
3. Address file permission issues

### Medium Priority
1. Update Docker configurations for security best practices
2. Review debug mode configurations
3. Implement additional input validation

### Low Priority
1. Regular security scans in CI/CD pipeline
2. Security headers implementation
3. Rate limiting enhancements

## Files Generated
- \`dependency_scan_$TIMESTAMP.json\` - Detailed dependency vulnerability report
- \`dependency_summary_$TIMESTAMP.txt\` - Human-readable dependency summary
- \`docker_issues_$TIMESTAMP.txt\` - Docker security issues
- \`potential_secrets_$TIMESTAMP.txt\` - Potential hardcoded secrets
- \`sql_injection_$TIMESTAMP.txt\` - SQL injection patterns
- \`world_writable_$TIMESTAMP.txt\` - File permission issues
- \`debug_mode_$TIMESTAMP.txt\` - Debug mode configurations

## Next Steps
1. Review all generated reports
2. Prioritize remediation based on severity
3. Implement fixes and re-scan
4. Update security documentation
EOF

# 7. Check scan results and exit appropriately
TOTAL_ISSUES=$((DOCKER_ISSUES + API_ISSUES + PERM_ISSUES + CONFIG_ISSUES))

log "📋 Security scan completed!"
log "📁 Reports saved to: $SECURITY_REPORT_DIR/"
log "📊 Total issues found: $TOTAL_ISSUES"

if [ $TOTAL_ISSUES -gt 0 ]; then
    log "⚠️  Security issues detected - review reports for details"
    log "📖 Summary report: $SECURITY_REPORT_DIR/security_summary_$TIMESTAMP.md"
    # Don't fail the build for security issues - just report them
    exit 0
else
    log "✅ No critical security issues detected"
    exit 0
fi