# Getting Started - DNA Research Platform

## Overview
The DNA Research Platform enables researchers and families to create, test, and evolve genomic theories using privacy-preserving Bayesian analysis.

## Quick Setup

### Prerequisites
- Docker and Docker Compose
- Web browser (Chrome/Firefox recommended)

### Installation
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/dnaresearch.git
cd dnaresearch

# Start the platform
docker-compose -f docker/docker-compose.yml up -d

# Verify installation
curl http://localhost:8000/health
```

### Access Points
- **Portal**: http://localhost:8080 - User-friendly interface
- **API Documentation**: http://localhost:8000/docs - Interactive API explorer

## First Steps

### For Families
1. Access the portal at http://localhost:8080
2. Review available theories and their evidence
3. Understand gene interpretations in plain language

### For Researchers
1. Explore the API at http://localhost:8000/docs
2. Review existing theories and their Bayesian posteriors
3. Consider creating or forking theories for your research

## Key Concepts
- **Theories**: JSON-defined hypotheses with transparent priors
- **Evidence**: Genomic data that updates theory confidence
- **Bayesian Updates**: Statistical method for accumulating evidence
- **Privacy by Design**: Consent-aware processing with audit trails

## Support
- Technical issues: See [troubleshooting docs](../troubleshooting/)
- Development: See [developer docs](../developer/)
- Architecture: See [architecture docs](../architecture/)