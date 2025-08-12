#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load configuration
source "$SCRIPT_DIR/load-config.sh"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

log "📊 Analyzing test coverage..."

cd "$PROJECT_ROOT"

# Run coverage analysis
if [[ -f "api/coverage.xml" ]]; then
    # Extract coverage percentage from XML report
    COVERAGE_PERCENT=$(python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('api/coverage.xml')
root = tree.getroot()
coverage = root.attrib.get('line-rate', '0')
print(int(float(coverage) * 100))
")
else
    # Run coverage analysis if report doesn't exist
    cd api
    coverage run -m pytest
    COVERAGE_PERCENT=$(coverage report --format=total)
    cd ..
fi

# Store coverage metrics
if [[ "$STORE_METRICS" == "true" ]]; then
    mkdir -p metrics
    echo "$(date '+%Y-%m-%d %H:%M:%S'),coverage_percent,$COVERAGE_PERCENT" >> metrics/coverage-metrics.csv
fi

log "Coverage analysis completed: ${COVERAGE_PERCENT}%"

# Print coverage summary to screen
echo "📊 Coverage Summary:"
echo "   Total Coverage: ${COVERAGE_PERCENT}%"
if [[ $COVERAGE_PERCENT -ge 80 ]]; then
    echo "   Status: ✅ GOOD (≥80%)"
elif [[ $COVERAGE_PERCENT -ge 60 ]]; then
    echo "   Status: ⚠️  MODERATE (60-79%)"
else
    echo "   Status: ❌ LOW (<60%)"
fi
echo

# Output coverage percentage for use by calling script
echo "$COVERAGE_PERCENT"