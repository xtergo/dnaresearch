# Developer Setup

## Development Environment

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git
- IDE with Python support (VS Code recommended)

### Local Development Setup
```bash
# Clone and enter directory
git clone https://github.com/YOUR_USERNAME/dnaresearch.git
cd dnaresearch

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install API dependencies
cd api
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Run API locally
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Development Workflow
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Run tests: `pytest`
4. Commit with descriptive message
5. Push and create pull request

### Code Standards
- Follow PEP 8 for Python
- Use type hints for all functions
- Write docstrings for public APIs
- Maintain test coverage >80%
- Use pre-commit hooks for validation

### Project Structure
```
dnaresearch/
├── api/                 # FastAPI backend
├── portal/             # Frontend interface
├── docs/               # Documentation
│   ├── user/          # User guides
│   ├── developer/     # Developer docs
│   ├── architecture/  # Technical specs
│   ├── troubleshooting/ # Problem solving
│   └── testing/       # Test documentation
├── schemas/           # JSON schemas (planned)
├── tests/             # Test suites (planned)
└── docker/            # Container configs
```

### Environment Variables
Create `.env` file for local development:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/dnaresearch

# Storage
S3_BUCKET=dna-research-dev
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```