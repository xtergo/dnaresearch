# Common Issues & Solutions

## Installation Issues

### Docker Compose Fails to Start
**Problem**: `docker-compose up` fails with port conflicts
```
Error: Port 8000 is already in use
```

**Solution**:
```bash
# Check what's using the port
lsof -i :8000
# Kill the process or change port in docker-compose.yml
```

### API Health Check Fails
**Problem**: `/health` endpoint returns 500 error

**Solutions**:
1. Check container logs: `docker-compose logs api`
2. Verify Python dependencies: `pip install -r requirements.txt`
3. Check database connectivity

## Development Issues

### Import Errors
**Problem**: `ModuleNotFoundError` when running locally

**Solution**:
```bash
# Ensure you're in the correct directory and virtual environment
cd api
source ../venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Database Connection Issues
**Problem**: Cannot connect to PostgreSQL

**Solutions**:
1. Verify database is running: `docker-compose ps`
2. Check connection string in environment variables
3. Ensure database exists and user has permissions

## Performance Issues

### Slow Gene Search
**Problem**: `/genes/search` endpoint is slow

**Solutions**:
1. Check Redis cache status
2. Verify database indexes
3. Monitor query execution plans

### High Memory Usage
**Problem**: Application consuming excessive memory

**Solutions**:
1. Check for memory leaks in genomic data processing
2. Implement pagination for large datasets
3. Optimize anchor/diff storage queries

## Security Issues

### Authentication Failures
**Problem**: API returns 401 Unauthorized

**Solutions**:
1. Verify JWT token validity
2. Check token expiration
3. Ensure correct authentication headers

### CORS Errors
**Problem**: Browser blocks API requests

**Solution**:
```python
# Add to FastAPI configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Data Issues

### Genomic File Processing Errors
**Problem**: VCF files fail to process

**Solutions**:
1. Validate file format and headers
2. Check file permissions and encoding
3. Verify genomic coordinates are valid

### Theory Validation Failures
**Problem**: JSON theory fails schema validation

**Solutions**:
1. Use JSON schema validator
2. Check required fields are present
3. Verify data types match schema

## Logging & Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Application Logs
```bash
# Docker logs
docker-compose logs -f api

# Local development
tail -f logs/app.log
```

### Database Query Debugging
```python
# Enable SQLAlchemy logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## Getting Help

1. Check existing [GitHub issues](https://github.com/YOUR_USERNAME/dnaresearch/issues)
2. Review [architecture documentation](../architecture/)
3. Join community discussions
4. Contact maintainers for critical issues

## Reporting Bugs

When reporting issues, include:
- Operating system and version
- Python version
- Docker version
- Steps to reproduce
- Error messages and logs
- Expected vs actual behavior