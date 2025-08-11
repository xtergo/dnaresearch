#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load configuration
source "$SCRIPT_DIR/load-config.sh"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "🌐 Running E2E tests..."

cd "$PROJECT_ROOT"

# Start the application
log "Starting application for E2E tests..."
docker compose -f docker/docker-compose.dev.yml up -d --build

# Wait for services to be ready
log "Waiting for services to be ready..."
timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'

# Run E2E tests
log "Running E2E test suite..."

# Create E2E test script if it doesn't exist
if [[ ! -f "scripts/e2e-test-suite.py" ]]; then
    cat > scripts/e2e-test-suite.py << 'EOF'
#!/usr/bin/env python3
import requests
import json
import sys
import time

def test_health_endpoint():
    """Test health endpoint is accessible"""
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print("✅ Health endpoint test passed")

def test_api_documentation():
    """Test API documentation is accessible"""
    response = requests.get("http://localhost:8000/docs")
    assert response.status_code == 200
    print("✅ API documentation test passed")

def test_theory_validation():
    """Test theory validation endpoint"""
    theory = {
        "id": "e2e-test-theory",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 1.0}}
    }
    
    response = requests.post("http://localhost:8000/theories/validate", json=theory)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "valid"
    print("✅ Theory validation test passed")

def test_evidence_validation():
    """Test evidence validation endpoint"""
    evidence = {
        "type": "variant_hit",
        "weight": 2.5,
        "timestamp": "2025-01-11T10:30:00Z",
        "data": {
            "gene": "SHANK3",
            "variant": "c.3679C>T",
            "impact": "high"
        }
    }
    
    response = requests.post("http://localhost:8000/evidence/validate", json=evidence)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "valid"
    print("✅ Evidence validation test passed")

def test_gene_search():
    """Test gene search endpoint"""
    response = requests.get("http://localhost:8000/genes/search?query=autism")
    assert response.status_code == 200
    data = response.json()
    assert "hits" in data
    assert len(data["hits"]) > 0
    print("✅ Gene search test passed")

def main():
    print("🌐 Starting E2E test suite...")
    
    try:
        test_health_endpoint()
        test_api_documentation()
        test_theory_validation()
        test_evidence_validation()
        test_gene_search()
        
        print("🎉 All E2E tests passed!")
        return 0
        
    except Exception as e:
        print(f"❌ E2E test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
    chmod +x scripts/e2e-test-suite.py
fi

# Run the E2E tests
python3 scripts/e2e-test-suite.py

# Store test results
if [[ "$STORE_TEST_RESULTS" == "true" ]]; then
    mkdir -p test-results/e2e
    echo "E2E tests completed at $(date)" > test-results/e2e/e2e-test-results.txt
fi

# Cleanup if configured
if [[ "$CLEANUP_AFTER_TESTS" == "true" ]]; then
    log "Cleaning up E2E test environment..."
    docker compose -f docker/docker-compose.dev.yml down
fi

log "✅ E2E tests completed successfully"