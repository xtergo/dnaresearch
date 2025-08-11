# Contributing to DNA Research Platform

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/dnaresearch.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Node.js (for portal development)

### Local Development
```bash
# Install API dependencies
cd api
pip install -r requirements.txt

# Run with Docker
docker-compose -f docker/docker-compose.yml up
```

## Project Structure
- `api/` - FastAPI backend
- `portal/` - Frontend interface
- `docs/` - Technical documentation
- `docker/` - Container configurations
- `schemas/` - JSON schemas (planned)
- `tests/` - Test suites (planned)

## Roadmap Alignment
This project follows the roadmap in [`docs/blueprint.md`](docs/blueprint.md):
- **Sprint 1-2**: MVP Core (JSON schemas, API, storage)
- **Sprint 3-4**: Integrations (webhooks, theory engine)
- **Sprint 5-6**: Hardening (security, monitoring)

## Code Standards
- Follow PEP 8 for Python
- Use type hints
- Write tests for new features
- Update documentation

## Privacy & Ethics
This platform handles sensitive genomic data. All contributions must:
- Respect privacy by design principles
- Follow GDPR compliance requirements
- Implement proper consent mechanisms
- Maintain audit trails

## License
This project aims to be open source while protecting novel IP through strategic patenting.