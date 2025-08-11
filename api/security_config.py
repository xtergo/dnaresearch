"""
Security Configuration for DNA Research Platform
Centralized security settings and vulnerability management
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels"""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class SecurityScanType(Enum):
    """Types of security scans"""

    DEPENDENCY = "dependency"
    DOCKER = "docker"
    API = "api"
    PERMISSIONS = "permissions"
    CONFIGURATION = "configuration"


@dataclass
class VulnerabilityInfo:
    """Information about a security vulnerability"""

    cve_id: str
    package_name: str
    installed_version: str
    fixed_version: Optional[str]
    severity: VulnerabilitySeverity
    description: str
    scan_type: SecurityScanType


@dataclass
class SecurityScanConfig:
    """Configuration for security scanning"""

    # Scan enablement
    dependency_scan_enabled: bool = True
    docker_scan_enabled: bool = True
    api_scan_enabled: bool = True
    permission_scan_enabled: bool = True
    config_scan_enabled: bool = True

    # Severity thresholds
    fail_on_critical: bool = False  # Don't fail builds on security issues
    fail_on_high: bool = False
    warn_on_medium: bool = True

    # Scan timeouts (seconds)
    dependency_scan_timeout: int = 300
    docker_scan_timeout: int = 120
    api_scan_timeout: int = 180

    # Report settings
    generate_json_report: bool = True
    generate_markdown_report: bool = True
    store_historical_reports: bool = True

    # Known vulnerabilities to ignore (with justification)
    ignored_vulnerabilities: Dict[str, str] = None

    def __post_init__(self):
        if self.ignored_vulnerabilities is None:
            self.ignored_vulnerabilities = {
                # Known issues with justification
                "CVE-2024-33664": "python-jose vulnerability - limited exposure in current implementation",
                "CVE-2024-33663": "python-jose vulnerability - considering replacement with PyJWT",
            }


class SecurityManager:
    """Manages security scanning and vulnerability tracking"""

    def __init__(self, config: SecurityScanConfig = None):
        self.config = config or SecurityScanConfig()
        self.vulnerabilities: List[VulnerabilityInfo] = []

    def add_vulnerability(self, vulnerability: VulnerabilityInfo) -> None:
        """Add a vulnerability to the tracking list"""
        self.vulnerabilities.append(vulnerability)

    def get_vulnerabilities_by_severity(
        self, severity: VulnerabilitySeverity
    ) -> List[VulnerabilityInfo]:
        """Get vulnerabilities filtered by severity"""
        return [v for v in self.vulnerabilities if v.severity == severity]

    def get_critical_vulnerabilities(self) -> List[VulnerabilityInfo]:
        """Get critical severity vulnerabilities"""
        return self.get_vulnerabilities_by_severity(VulnerabilitySeverity.CRITICAL)

    def get_high_vulnerabilities(self) -> List[VulnerabilityInfo]:
        """Get high severity vulnerabilities"""
        return self.get_vulnerabilities_by_severity(VulnerabilitySeverity.HIGH)

    def should_fail_build(self) -> bool:
        """Determine if build should fail based on vulnerabilities"""
        if self.config.fail_on_critical and self.get_critical_vulnerabilities():
            return True
        if self.config.fail_on_high and self.get_high_vulnerabilities():
            return True
        return False

    def is_vulnerability_ignored(self, cve_id: str) -> bool:
        """Check if a vulnerability is in the ignore list"""
        return cve_id in self.config.ignored_vulnerabilities

    def get_ignore_reason(self, cve_id: str) -> Optional[str]:
        """Get the reason why a vulnerability is ignored"""
        return self.config.ignored_vulnerabilities.get(cve_id)

    def calculate_risk_score(self) -> int:
        """Calculate overall risk score based on vulnerabilities"""
        score = 0
        for vuln in self.vulnerabilities:
            if vuln.severity == VulnerabilitySeverity.CRITICAL:
                score += 10
            elif vuln.severity == VulnerabilitySeverity.HIGH:
                score += 5
            elif vuln.severity == VulnerabilitySeverity.MEDIUM:
                score += 2
            elif vuln.severity == VulnerabilitySeverity.LOW:
                score += 1
        return score

    def get_security_summary(self) -> Dict[str, int]:
        """Get summary of security scan results"""
        return {
            "total_vulnerabilities": len(self.vulnerabilities),
            "critical": len(self.get_critical_vulnerabilities()),
            "high": len(self.get_high_vulnerabilities()),
            "medium": len(
                self.get_vulnerabilities_by_severity(VulnerabilitySeverity.MEDIUM)
            ),
            "low": len(self.get_vulnerabilities_by_severity(VulnerabilitySeverity.LOW)),
            "risk_score": self.calculate_risk_score(),
        }


# Default security configuration
DEFAULT_SECURITY_CONFIG = SecurityScanConfig()

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    DEFAULT_SECURITY_CONFIG.fail_on_critical = True
    DEFAULT_SECURITY_CONFIG.fail_on_high = True
elif os.getenv("ENVIRONMENT") == "staging":
    DEFAULT_SECURITY_CONFIG.fail_on_critical = True

# Global security manager instance
security_manager = SecurityManager(DEFAULT_SECURITY_CONFIG)
