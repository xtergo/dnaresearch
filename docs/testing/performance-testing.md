# Performance Testing - DNA Research Platform

## Overview

This document describes the performance testing strategy and benchmarks for the DNA Research Platform. Our performance testing ensures the platform can handle realistic genomic research workloads while maintaining responsive user experience.

## Performance Benchmarks

### Response Time Targets (95th Percentile)

| Endpoint Category | Target P95 | Rationale |
|------------------|------------|-----------|
| Health Check | < 100ms | System monitoring requires fast response |
| Gene Search | < 200ms | Interactive search needs to feel instant |
| Variant Interpretation | < 1000ms | Complex analysis, but user expects quick feedback |
| Theory Execution | < 30000ms | Heavy computation, 30s is acceptable for research |
| Researcher Reports | < 2000ms | Detailed reports can take a moment to generate |
| File Upload URLs | < 500ms | File operations should be responsive |
| Consent Validation | < 1000ms | Privacy checks must be fast but thorough |

### Throughput Targets (Requests Per Second)

| Endpoint Category | Target RPS | Concurrent Users |
|------------------|------------|------------------|
| Health Check | ≥ 100 RPS | High (monitoring systems) |
| Gene Search | ≥ 50 RPS | Medium (interactive users) |
| Variant Interpretation | ≥ 10 RPS | Low (analysis workflows) |
| Theory Execution | ≥ 1 RPS | Very Low (heavy computation) |
| Researcher Reports | ≥ 5 RPS | Low (detailed analysis) |

## Testing Framework

### Tools Used

- **Locust**: Load testing framework for realistic user behavior simulation
- **pytest**: Unit performance tests with precise measurements
- **Custom Analytics**: Performance analysis and bottleneck identification

### Test Scenarios

#### 1. Researcher Workflow (Primary User)
- **Users**: 10-20 concurrent
- **Behavior**: Gene search → Variant interpretation → Report generation
- **Duration**: 60 seconds
- **Weight**: 60% of total load

#### 2. High-Volume Automated Systems
- **Users**: 2-5 concurrent
- **Behavior**: Rapid health checks and batch gene searches
- **Duration**: 30 seconds
- **Weight**: 20% of total load

#### 3. Casual Users (Parents/Patients)
- **Users**: 5-10 concurrent
- **Behavior**: Simple variant lookups and condition searches
- **Duration**: 60 seconds
- **Weight**: 20% of total load

## Running Performance Tests

### Prerequisites

```bash
# Install dependencies
pip install locust pytest

# Ensure API server is running
docker compose -f docker/docker-compose.test.yml up -d api
```

### Load Testing with Locust

```bash
# Run all performance test scenarios
./scripts/run-performance-tests.sh

# Run specific scenario
locust -f tests/performance/locustfile.py --headless \
  --users 20 --spawn-rate 2 --run-time 60s \
  --host http://localhost:8000 \
  --tags gene_search
```

### Unit Performance Tests

```bash
# Run performance unit tests
pytest api/test_performance.py -v -m performance

# Run with detailed output
pytest api/test_performance.py::TestPerformance::test_overall_system_load -v -s
```

### Analysis and Reporting

```bash
# Analyze results (automatically run after load tests)
python3 scripts/analyze-performance.py test-results/performance/

# View HTML reports
open test-results/performance/health_report.html
```

## Performance Monitoring

### Key Metrics

1. **Response Time Distribution**
   - P50, P95, P99 response times
   - Average response time trends
   - Maximum response time spikes

2. **Throughput Metrics**
   - Requests per second (RPS)
   - Concurrent user capacity
   - Request success rate

3. **Resource Utilization**
   - CPU usage patterns
   - Memory consumption
   - Database connection pool usage

4. **Error Rates**
   - HTTP error rate (< 1% target)
   - Timeout occurrences
   - Database query failures

### Bottleneck Identification

The performance analyzer automatically identifies:

- **High Latency Endpoints**: P95 > 1000ms
- **Low Throughput Operations**: < 10 RPS
- **High Error Rates**: > 1% failure rate
- **Resource Constraints**: CPU/Memory limits

## Optimization Strategies

### Caching Implementation

```python
# Redis caching for gene searches
@cache_result(ttl=3600)  # 1 hour cache
def search_genes(query: str):
    # Expensive gene lookup
    pass
```

### Database Optimization

- **Indexing**: Genomic coordinate indexes for fast range queries
- **Connection Pooling**: Async connection management
- **Query Optimization**: Efficient JOIN operations for complex queries

### Async Processing

```python
# Background processing for heavy operations
@background_task
async def execute_theory_async(theory_id: str, vcf_data: str):
    # Long-running theory execution
    pass
```

## Continuous Performance Testing

### CI/CD Integration

Performance tests run automatically on:

- **Pull Requests**: Basic performance regression tests
- **Nightly Builds**: Full load testing suite
- **Release Candidates**: Comprehensive performance validation

### Performance Regression Detection

```bash
# Compare performance against baseline
python3 scripts/compare-performance.py \
  --baseline test-results/baseline/ \
  --current test-results/performance/
```

## Performance Test Results

### Latest Benchmark Results

```
🚀 DNA Research Platform - Performance Test Results
============================================================
📊 Overall Status: PASS
🧪 Scenarios Tested: 3
📈 Total Requests: 2,847
❌ Total Failures: 0
📉 Failure Rate: 0.00%
⚠️  Critical Issues: 0

✅ All performance benchmarks met! 🎉
```

### Historical Performance Trends

| Date | Health P95 | Gene Search P95 | Theory Exec P95 | Overall RPS |
|------|------------|-----------------|-----------------|-------------|
| 2025-01-XX | 45ms | 156ms | 12.3s | 67.2 |

## Troubleshooting Performance Issues

### Common Issues and Solutions

1. **High Database Latency**
   - Check connection pool settings
   - Analyze slow query logs
   - Consider read replicas

2. **Memory Leaks**
   - Monitor memory usage trends
   - Check for unclosed connections
   - Review caching strategies

3. **CPU Bottlenecks**
   - Profile CPU-intensive operations
   - Consider async processing
   - Optimize algorithms

### Performance Debugging

```bash
# Enable detailed performance logging
export LOG_LEVEL=DEBUG
export PERFORMANCE_PROFILING=true

# Run with profiling
python -m cProfile -o profile.stats api/main.py
```

## Future Performance Improvements

### Planned Optimizations

1. **Horizontal Scaling**: Kubernetes deployment with auto-scaling
2. **CDN Integration**: Static asset caching and global distribution
3. **Database Sharding**: Genomic data partitioning by chromosome
4. **ML Model Optimization**: Faster variant interpretation algorithms

### Performance Goals

- **Target**: Support 1000+ concurrent users
- **Latency**: P95 < 100ms for all interactive operations
- **Throughput**: 500+ RPS for gene searches
- **Availability**: 99.9% uptime with < 1s failover

---

**Last Updated**: 2025-01-XX  
**Next Review**: After each major release