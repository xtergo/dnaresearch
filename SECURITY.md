# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by emailing security@dnaresearch.org or creating a private security advisory on GitHub.

## Security Updates

### 2025-01-11 - Dependency Security Updates

**Fixed Vulnerabilities:**
- **python-multipart**: Updated from 0.0.9 to 0.0.18 (CVE-2024-53981)
  - Fixed: Allocation of Resources Without Limits or Throttling
- **minio**: Updated from 7.2.7 to 7.2.11 (PVE-2024-74210)  
  - Fixed: Race Conditions leading to data corruption

**Remaining Known Issues:**
- **python-jose 3.3.0**: 2 vulnerabilities (CVE-2024-33664, CVE-2024-33663)
  - Status: No secure version available, considering replacement with PyJWT
  - Impact: JWT token processing vulnerabilities
  - Mitigation: Limited exposure in current implementation

## Security Best Practices

- All dependencies are regularly scanned for vulnerabilities
- Pre-commit hooks include security validation
- Docker containers use minimal base images
- Sensitive data is encrypted at rest (AES-256)
- All API endpoints require authentication
- Audit trails are immutable and cryptographically signed