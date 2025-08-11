# Pre-commit Hooks - DNA Research Platform

## Overview
Comprehensive pre-commit validation pipeline ensuring code quality, test coverage, and deployment readiness for the genomic research platform.

## Installation

### Install pre-commit
```bash
pip install pre-commit
```

### Install hooks
```bash
cd dnaresearch
pre-commit install
```

## Configuration

### Development Configuration File
Edit `.dnaresearch-dev-config` to customize validation behavior:

```bash
# Core validation settings
verify_pre_commit=true
environment_type=docker
require_all_tests_pass=true

# Coverage settings
enable_coverage_metrics=true
enforce_coverage_threshold=true
coverage_threshold=80

# Test settings
test_types=all
parallel_tests=true
e2e_timeout_sec=300

# Performance settings
enforce_test_duration_threshold=true
test_duration_threshold_sec=30
```

## Validation Pipeline

### 1. Python Linting
- **Black** code formatting
- **isort** import sorting
- **flake8** style checking
- Configurable via `python_lint_enabled=true`

### 2. JSON Schema Validation
- Validates all schemas in `schemas/` directory
- Ensures JSON Schema 2020-12 compliance
- Configurable via `schema_validation_enabled=true`

### 3. Database Migration Validation
- Validates SQL syntax in migration files
- Checks for dangerous operations
- Ensures proper IF EXISTS/IF NOT EXISTS usage
- Configurable via `validate_migrations=true`

### 4. Unit Tests
- Runs all unit tests with coverage
- Supports parallel execution
- Enforces coverage thresholds
- Configurable via `require_all_tests_pass=true`

### 5. Integration Tests
- Tests API endpoints with database
- Validates schema integration
- Uses isolated test environment
- Configurable via `test_types=all`

### 6. End-to-End Tests
- Deploys full application stack
- Tests complete user workflows
- Validates API documentation
- Configurable via `test_types=all`

### 7. Coverage Analysis
- Measures test coverage percentage
- Enforces minimum thresholds
- Stores metrics for tracking
- Configurable via `enable_coverage_metrics=true`

### 8. Security Scanning (Optional)
- Scans dependencies for vulnerabilities
- Checks for security best practices
- Configurable via `security_scan_enabled=false`

### 9. Performance Tests (Optional)
- Basic API performance validation
- Response time monitoring
- Configurable via `performance_test_enabled=false`

## Usage

### Automatic (Recommended)
Pre-commit hooks run automatically on `git commit`:

```bash
git add .
git commit -m "Add new feature"
# Hooks run automatically
```

### Manual Execution
Run hooks manually without committing:

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run python-lint
pre-commit run schema-validation
```

### Skip Hooks (Emergency)
Skip hooks for emergency commits:

```bash
git commit -m "Emergency fix" --no-verify
```

## Configuration Options

### Test Types
```bash
test_types=unit              # Unit tests only
test_types=unit,integration  # Unit and integration
test_types=all              # All test types
```

### Environment Types
```bash
environment_type=docker     # Use Docker Compose (recommended)
environment_type=local      # Use local Python environment
```

### Coverage Enforcement
```bash
enforce_coverage_threshold=true
coverage_threshold=80       # Minimum 80% coverage
```

### Performance Tuning
```bash
parallel_tests=true         # Run tests in parallel
docker_build_fast=true      # Use Docker layer caching
cleanup_after_tests=true    # Clean up after validation
```

## Metrics and Reporting

### Metrics Storage
Validation metrics are stored in `metrics/pre-commit-metrics.csv`:

```csv
timestamp,metric_name,metric_value
2025-01-11 10:30:00,python_lint_duration_sec,5
2025-01-11 10:30:05,unit_test_duration_sec,25
2025-01-11 10:30:30,test_coverage_percent,85
2025-01-11 10:30:35,total_validation_duration_sec,45
```

### Test Results
Test results are stored in `test-results/`:

```
test-results/
├── unit/
│   └── unit-test-results.xml
├── integration/
│   └── integration-results.xml
└── e2e/
    └── e2e-test-results.txt
```

## Troubleshooting

### Common Issues

#### 1. Docker Permission Issues
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Restart shell
```

#### 2. Coverage Below Threshold
```bash
# Lower threshold temporarily
echo "coverage_threshold=70" >> .dnaresearch-dev-config

# Or improve test coverage
pytest --cov=. --cov-report=html
# Open htmlcov/index.html to see uncovered lines
```

#### 3. Test Timeout Issues
```bash
# Increase timeout
echo "e2e_timeout_sec=600" >> .dnaresearch-dev-config
```

#### 4. Slow Validation
```bash
# Enable fast mode
echo "docker_build_fast=true" >> .dnaresearch-dev-config
echo "parallel_tests=true" >> .dnaresearch-dev-config
echo "test_types=unit" >> .dnaresearch-dev-config
```

### Debug Mode
Enable debug logging:

```bash
echo "log_level=DEBUG" >> .dnaresearch-dev-config
```

### Skip Specific Validations
Temporarily disable validations:

```bash
echo "python_lint_enabled=false" >> .dnaresearch-dev-config
echo "schema_validation_enabled=false" >> .dnaresearch-dev-config
```

## Performance Optimization

### Fast Development Mode
For rapid development iterations:

```bash
# .dnaresearch-dev-config
verify_pre_commit=true
test_types=unit
parallel_tests=true
docker_build_fast=true
cleanup_after_tests=false
enforce_coverage_threshold=false
```

### Full Validation Mode
For production-ready commits:

```bash
# .dnaresearch-dev-config
verify_pre_commit=true
test_types=all
parallel_tests=true
enforce_coverage_threshold=true
coverage_threshold=80
security_scan_enabled=true
```

## Integration with CI/CD

Pre-commit hooks complement CI/CD pipelines:

- **Local**: Fast feedback during development
- **CI/CD**: Comprehensive validation before deployment

### GitHub Actions Integration
```yaml
name: Validation
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install pre-commit
      - run: pre-commit run --all-files
```

## Best Practices

### 1. Regular Configuration Review
Review `.dnaresearch-dev-config` monthly to optimize for team needs.

### 2. Metrics Monitoring
Monitor validation metrics to identify performance trends:

```bash
# View recent metrics
tail -20 metrics/pre-commit-metrics.csv
```

### 3. Team Consistency
Ensure all team members use the same configuration:

```bash
# Commit configuration to repository
git add .dnaresearch-dev-config
git commit -m "Update development configuration"
```

### 4. Gradual Adoption
Start with basic validations and gradually enable more:

```bash
# Week 1: Basic linting
python_lint_enabled=true
schema_validation_enabled=true

# Week 2: Add unit tests
require_all_tests_pass=true

# Week 3: Add coverage
enforce_coverage_threshold=true
coverage_threshold=60

# Week 4: Full pipeline
test_types=all
```

---

**Benefits:**
- ✅ Consistent code quality across team
- ✅ Early detection of issues
- ✅ Automated test execution
- ✅ Coverage tracking and enforcement
- ✅ Performance monitoring
- ✅ Configurable validation pipeline

**Last Updated**: 2025-01-XX  
**Next Review**: After major pipeline changes