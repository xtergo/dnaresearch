# Docker Development Environment

## Overview
All development, testing, and production environments use Docker Compose for consistency and reproducibility.

## Prerequisites
- Docker Engine 20.10+
- Docker Compose v2.0+

## Development Setup

### Quick Start
```bash
# Clone repository
git clone https://github.com/xtergo/dnaresearch.git
cd dnaresearch

# Start development environment
docker compose -f docker/docker-compose.dev.yml up --build

# Access services
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Database: localhost:5432
# Redis: localhost:6379
```

### Development Services
- **API**: FastAPI with hot reload
- **PostgreSQL**: Development database with test data
- **Redis**: Caching and session storage
- **MinIO**: S3-compatible object storage for VCF files

## Testing Environment

### Run Tests
```bash
# Run all tests in isolated environment
docker compose -f docker/docker-compose.test.yml up --build --abort-on-container-exit

# Run specific test suite
docker compose -f docker/docker-compose.test.yml run --rm api pytest test_health.py -v

# Run tests with coverage
docker compose -f docker/docker-compose.test.yml run --rm api pytest --cov=. --cov-report=html
```

### Test Database
- Isolated PostgreSQL instance
- Automatic schema creation
- Test data fixtures
- Cleaned between test runs

## Production Environment

### Production Deployment
```bash
# Production build and deploy
docker compose -f docker/docker-compose.prod.yml up -d --build

# View logs
docker compose -f docker/docker-compose.prod.yml logs -f

# Scale API instances
docker compose -f docker/docker-compose.prod.yml up -d --scale api=3
```

### Production Features
- Multi-stage builds for smaller images
- Health checks and restart policies
- Resource limits and reservations
- Production-grade PostgreSQL configuration
- SSL/TLS termination with Nginx

## Environment Files

### Development (.env.dev)
```env
DATABASE_URL=postgresql://dev_user:dev_pass@postgres:5432/dnaresearch_dev
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=dev_access_key
MINIO_SECRET_KEY=dev_secret_key
API_SECRET_KEY=dev_secret_key_change_in_production
DEBUG=true
```

### Testing (.env.test)
```env
DATABASE_URL=postgresql://test_user:test_pass@postgres_test:5432/dnaresearch_test
REDIS_URL=redis://redis_test:6379/1
API_SECRET_KEY=test_secret_key
DEBUG=true
TESTING=true
```

### Production (.env.prod)
```env
DATABASE_URL=postgresql://prod_user:secure_password@postgres:5432/dnaresearch_prod
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=production_access_key
MINIO_SECRET_KEY=production_secret_key
API_SECRET_KEY=production_secret_key_very_secure
DEBUG=false
```

## Docker Compose Files Structure

```
docker/
├── docker-compose.dev.yml      # Development environment
├── docker-compose.test.yml     # Testing environment
├── docker-compose.prod.yml     # Production environment
├── Dockerfile.api              # API service image
├── Dockerfile.nginx            # Nginx reverse proxy
└── init-scripts/
    ├── init-dev-db.sql         # Development database setup
    ├── init-test-db.sql        # Test database setup
    └── test-data.sql           # Sample data for development
```

## Development Workflow

### Daily Development
```bash
# Start development environment
docker compose -f docker/docker-compose.dev.yml up -d

# View API logs
docker compose -f docker/docker-compose.dev.yml logs -f api

# Run tests
docker compose -f docker/docker-compose.test.yml run --rm api pytest

# Stop environment
docker compose -f docker/docker-compose.dev.yml down
```

### Database Operations
```bash
# Access development database
docker compose -f docker/docker-compose.dev.yml exec postgres psql -U dev_user -d dnaresearch_dev

# Run database migrations
docker compose -f docker/docker-compose.dev.yml exec api alembic upgrade head

# Reset development database
docker compose -f docker/docker-compose.dev.yml down -v
docker compose -f docker/docker-compose.dev.yml up -d postgres
```

### Code Changes
- API code changes trigger automatic reload in development
- Schema changes require container rebuild
- Database schema changes need migration scripts

## Debugging

### Container Debugging
```bash
# Access API container shell
docker compose -f docker/docker-compose.dev.yml exec api bash

# Check container logs
docker compose -f docker/docker-compose.dev.yml logs api

# Monitor resource usage
docker stats
```

### Database Debugging
```bash
# Check database connections
docker compose -f docker/docker-compose.dev.yml exec postgres pg_stat_activity

# Backup development database
docker compose -f docker/docker-compose.dev.yml exec postgres pg_dump -U dev_user dnaresearch_dev > backup.sql
```

## Performance Optimization

### Development
- Volume mounts for hot reload
- Shared networks for service communication
- Resource limits to prevent system overload

### Production
- Multi-stage builds for smaller images
- Health checks for automatic recovery
- Resource reservations for guaranteed performance
- Connection pooling for database efficiency

## Security Considerations

### Development
- Default credentials (change for production)
- Debug mode enabled
- All ports exposed for development

### Production
- Secure credentials via environment variables
- Debug mode disabled
- Only necessary ports exposed
- SSL/TLS encryption
- Network isolation between services

## Troubleshooting

### Common Issues
1. **Port conflicts**: Change ports in docker-compose files
2. **Permission issues**: Check file ownership and Docker daemon permissions
3. **Memory issues**: Increase Docker memory limits
4. **Network issues**: Restart Docker daemon or recreate networks

### Clean Reset
```bash
# Stop all containers and remove volumes
docker compose -f docker/docker-compose.dev.yml down -v

# Remove all images
docker system prune -a

# Rebuild from scratch
docker compose -f docker/docker-compose.dev.yml up --build
```

---

**Benefits of Dockerized Development:**
- ✅ Consistent environment across team members
- ✅ Easy onboarding for new developers
- ✅ Isolated testing environment
- ✅ Production parity
- ✅ Easy deployment and scaling
- ✅ Reproducible builds

**Last Updated**: 2025-01-XX  
**Next Review**: After major Docker Compose changes