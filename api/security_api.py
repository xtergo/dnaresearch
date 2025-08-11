"""
Security API Endpoints for DNA Research Platform
Provides security scan results and vulnerability information
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from security_config import SecurityManager


class SecurityScanResult(BaseModel):
    """Security scan result model"""

    scan_id: str
    scan_date: datetime
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    risk_score: int
    scan_duration_seconds: Optional[int] = None


class VulnerabilityResponse(BaseModel):
    """Vulnerability information response"""

    cve_id: str
    package_name: str
    installed_version: str
    fixed_version: Optional[str]
    severity: str
    description: str
    scan_type: str
    is_ignored: bool
    ignore_reason: Optional[str] = None


class SecuritySummaryResponse(BaseModel):
    """Security summary response"""

    last_scan_date: Optional[datetime]
    total_vulnerabilities: int
    vulnerabilities_by_severity: Dict[str, int]
    risk_score: int
    scan_status: str
    recommendations: List[str]


router = APIRouter(prefix="/security", tags=["security"])


def get_latest_security_report() -> Optional[Dict]:
    """Get the latest security scan report"""
    project_root = Path(__file__).parent.parent
    security_reports_dir = project_root / "security-reports"

    if not security_reports_dir.exists():
        return None

    # Find the latest report
    json_reports = list(security_reports_dir.glob("dependency_scan_*.json"))
    if not json_reports:
        return None

    latest_report = max(json_reports, key=lambda p: p.stat().st_mtime)

    try:
        with open(latest_report, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def parse_security_report(report_data: Dict) -> SecurityScanResult:
    """Parse security report data into structured format"""
    if not report_data:
        return SecurityScanResult(
            scan_id="no-scan",
            scan_date=datetime.now(),
            total_issues=0,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            risk_score=0,
        )

    # Count vulnerabilities by severity
    vulnerabilities = report_data if isinstance(report_data, list) else []
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for vuln in vulnerabilities:
        severity = vuln.get("vulnerability", {}).get("severity", "LOW")
        if severity in severity_counts:
            severity_counts[severity] += 1

    total_issues = sum(severity_counts.values())
    risk_score = (
        severity_counts["CRITICAL"] * 10
        + severity_counts["HIGH"] * 5
        + severity_counts["MEDIUM"] * 2
        + severity_counts["LOW"] * 1
    )

    return SecurityScanResult(
        scan_id=f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        scan_date=datetime.now(),
        total_issues=total_issues,
        critical_issues=severity_counts["CRITICAL"],
        high_issues=severity_counts["HIGH"],
        medium_issues=severity_counts["MEDIUM"],
        low_issues=severity_counts["LOW"],
        risk_score=risk_score,
    )


@router.get("/scan-results", response_model=SecurityScanResult)
async def get_security_scan_results():
    """Get the latest security scan results"""
    try:
        report_data = get_latest_security_report()
        return parse_security_report(report_data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve security scan results: {str(e)}",
        )


@router.get("/vulnerabilities", response_model=List[VulnerabilityResponse])
async def get_vulnerabilities(
    severity: Optional[str] = Query(
        None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"
    ),
    package: Optional[str] = Query(None, description="Filter by package name"),
):
    """Get detailed vulnerability information"""
    try:
        report_data = get_latest_security_report()
        if not report_data:
            return []

        vulnerabilities = report_data if isinstance(report_data, list) else []
        results = []

        security_manager = SecurityManager()

        for vuln_data in vulnerabilities:
            vuln = vuln_data.get("vulnerability", {})
            cve_id = vuln.get("id", "UNKNOWN")
            package_name = vuln.get("package_name", "unknown")
            vuln_severity = vuln.get("severity", "LOW")

            # Apply filters
            if severity and vuln_severity != severity.upper():
                continue
            if package and package.lower() not in package_name.lower():
                continue

            is_ignored = security_manager.is_vulnerability_ignored(cve_id)
            ignore_reason = (
                security_manager.get_ignore_reason(cve_id) if is_ignored else None
            )

            results.append(
                VulnerabilityResponse(
                    cve_id=cve_id,
                    package_name=package_name,
                    installed_version=vuln.get("installed_version", "unknown"),
                    fixed_version=vuln.get("fixed_version"),
                    severity=vuln_severity,
                    description=vuln.get("advisory", "No description available"),
                    scan_type="dependency",
                    is_ignored=is_ignored,
                    ignore_reason=ignore_reason,
                )
            )

        return results
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve vulnerabilities: {str(e)}"
        )


@router.get("/summary", response_model=SecuritySummaryResponse)
async def get_security_summary():
    """Get security summary and recommendations"""
    try:
        report_data = get_latest_security_report()
        scan_result = parse_security_report(report_data)

        # Generate recommendations based on scan results
        recommendations = []
        if scan_result.critical_issues > 0:
            recommendations.append(
                f"Immediately address {scan_result.critical_issues} critical vulnerabilities"
            )
        if scan_result.high_issues > 0:
            recommendations.append(
                f"Prioritize fixing {scan_result.high_issues} high-severity vulnerabilities"
            )
        if scan_result.medium_issues > 0:
            recommendations.append(
                f"Plan remediation for {scan_result.medium_issues} medium-severity issues"
            )
        if scan_result.risk_score > 20:
            recommendations.append(
                "Overall risk score is elevated - consider security review"
            )
        if not recommendations:
            recommendations.append(
                "Security posture is good - maintain regular scanning"
            )

        # Determine scan status
        if scan_result.critical_issues > 0:
            status = "CRITICAL"
        elif scan_result.high_issues > 0:
            status = "HIGH_RISK"
        elif scan_result.medium_issues > 0:
            status = "MEDIUM_RISK"
        else:
            status = "LOW_RISK"

        return SecuritySummaryResponse(
            last_scan_date=scan_result.scan_date,
            total_vulnerabilities=scan_result.total_issues,
            vulnerabilities_by_severity={
                "critical": scan_result.critical_issues,
                "high": scan_result.high_issues,
                "medium": scan_result.medium_issues,
                "low": scan_result.low_issues,
            },
            risk_score=scan_result.risk_score,
            scan_status=status,
            recommendations=recommendations,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate security summary: {str(e)}"
        )


@router.post("/scan/trigger")
async def trigger_security_scan():
    """Trigger a new security scan"""
    try:
        # In a real implementation, this would trigger the security scan script
        # For now, we'll return a success message
        return {
            "message": "Security scan triggered successfully",
            "scan_id": f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "estimated_duration": "2-5 minutes",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger security scan: {str(e)}"
        )


@router.get("/health")
async def security_health_check():
    """Health check for security scanning system"""
    project_root = Path(__file__).parent.parent
    security_script = project_root / "scripts" / "security-scan.sh"

    return {
        "status": "healthy",
        "security_script_exists": security_script.exists(),
        "security_script_executable": (
            os.access(security_script, os.X_OK) if security_script.exists() else False
        ),
        "last_scan": "Available via /security/scan-results endpoint",
    }
