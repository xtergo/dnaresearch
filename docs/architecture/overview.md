# Architecture Overview

## System Architecture

```mermaid
flowchart TB
    subgraph "Frontend Layer"
        Portal[Portal UI]
        API_Docs[API Documentation]
    end
    
    subgraph "API Layer"
        FastAPI[FastAPI Application]
        Auth[Authentication]
        Validation[Request Validation]
    end
    
    subgraph "Business Logic"
        TheoryEngine[Theory Engine]
        BayesianUpdater[Bayesian Updater]
        GeneInterpreter[Gene Interpreter]
        ConsentManager[Consent Manager]
    end
    
    subgraph "Storage Layer"
        PostgreSQL[(PostgreSQL)]
        S3[(S3/MinIO)]
        Redis[(Redis Cache)]
        Blockchain[(Permissioned Ledger)]
    end
    
    subgraph "External Services"
        SequencingPartners[Sequencing Partners]
        PublicDBs[Public Gene DBs]
    end
    
    Portal --> FastAPI
    API_Docs --> FastAPI
    FastAPI --> Auth
    FastAPI --> Validation
    FastAPI --> TheoryEngine
    FastAPI --> BayesianUpdater
    FastAPI --> GeneInterpreter
    FastAPI --> ConsentManager
    
    TheoryEngine --> PostgreSQL
    TheoryEngine --> Redis
    BayesianUpdater --> PostgreSQL
    GeneInterpreter --> PublicDBs
    ConsentManager --> Blockchain
    
    S3 --> FastAPI
    SequencingPartners --> FastAPI
```

## Core Components

### API Layer (FastAPI)
- RESTful API with OpenAPI documentation
- Request validation and serialization
- Authentication and authorization
- Rate limiting and security headers

### Theory Engine
- JSON-based theory definitions
- Version management (SemVer)
- Theory forking and inheritance
- Dependency tracking

### Bayesian Updater
- Evidence accumulation from families/cohorts
- Posterior probability calculations
- Support classification (Weak/Moderate/Strong)
- Federated computation support

### Storage Strategy
- **Anchor+Diff**: Hierarchical genomic storage
- **PostgreSQL**: Metadata, theories, evidence
- **S3/MinIO**: Genomic files, encrypted artifacts
- **Redis**: Caching and session management
- **Blockchain**: Consent and audit trails

### Privacy & Security
- Encryption at rest (AES-256)
- Consent-aware data access
- Immutable audit logging
- GDPR compliance features

## Data Flow

1. **Theory Creation**: Researcher defines JSON theory
2. **Evidence Ingestion**: Genomic data from sequencing partners
3. **Bayesian Update**: Evidence updates theory posteriors
4. **Result Generation**: Reports for families and researchers
5. **Audit Trail**: All actions logged to blockchain

## Scalability Considerations
- Horizontal scaling via containerization
- Database sharding for large cohorts
- CDN for static assets
- Queue-based processing for heavy computations

## Security Architecture
- Zero-trust network model
- End-to-end encryption
- Role-based access control (RBAC)
- Attribute-based access control (ABAC)
- Regular security audits