"""GDPR Compliance Manager - Privacy Impact Assessment and Breach Notification"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


class BreachSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class PIAStatus(Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_UPDATE = "requires_update"


class BreachStatus(Enum):
    REPORTED = "reported"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    REGULATORY_NOTIFIED = "regulatory_notified"


@dataclass
class DataProcessingAgreement:
    dpa_id: str
    partner_name: str
    purpose: str
    data_categories: List[str]
    retention_period: str
    security_measures: List[str]
    signed_date: str
    expiry_date: str
    status: str


@dataclass
class PrivacyAssessment:
    pia_id: str
    purpose: str
    data_categories: List[str]
    processing_activities: List[str]
    risk_level: RiskLevel
    status: PIAStatus
    mitigation_measures: List[str]
    created_at: str
    updated_at: str
    reviewer: Optional[str] = None
    approval_date: Optional[str] = None


@dataclass
class BreachNotification:
    breach_id: str
    severity: BreachSeverity
    description: str
    affected_count: int
    data_categories: List[str]
    reported_at: str
    status: BreachStatus
    containment_measures: List[str]
    notification_deadline: str
    regulatory_notified: bool = False
    affected_notified: bool = False


class GDPRComplianceManager:
    def __init__(self):
        self.assessments: Dict[str, PrivacyAssessment] = {}
        self.breaches: Dict[str, BreachNotification] = {}
        self.dpas: Dict[str, DataProcessingAgreement] = {}
        self._init_default_data()

    def _init_default_data(self):
        """Initialize default genomic research PIA and DPA"""
        # Default PIA for genomic research
        pia = PrivacyAssessment(
            pia_id="pia_genomic_001",
            purpose="Genomic research and variant analysis for rare disease diagnosis",
            data_categories=["genetic_data", "health_data", "personal_identifiers"],
            processing_activities=[
                "variant_analysis",
                "theory_testing",
                "report_generation",
            ],
            risk_level=RiskLevel.HIGH,
            status=PIAStatus.APPROVED,
            mitigation_measures=[
                "End-to-end encryption (AES-256)",
                "Consent-based access control",
                "Immutable audit trails",
                "Regular security assessments",
                "Data minimization principles",
            ],
            created_at=datetime.utcnow().isoformat() + "Z",
            updated_at=datetime.utcnow().isoformat() + "Z",
            reviewer="dpo@dnaresearch.org",
            approval_date=datetime.utcnow().isoformat() + "Z",
        )
        self.assessments[pia.pia_id] = pia

        # Default DPA template
        dpa = DataProcessingAgreement(
            dpa_id="dpa_template_001",
            partner_name="Sequencing Partner Template",
            purpose="Genomic sequencing and data processing",
            data_categories=["genetic_samples", "sequencing_data", "quality_metrics"],
            retention_period="7 years post-analysis",
            security_measures=[
                "ISO 27001 certification",
                "SOC 2 Type II compliance",
                "Encrypted data transmission",
                "Access logging and monitoring",
            ],
            signed_date="",
            expiry_date="",
            status="template",
        )
        self.dpas[dpa.dpa_id] = dpa

    def create_privacy_assessment(
        self,
        purpose: str,
        data_categories: List[str] = None,
        processing_activities: List[str] = None,
    ) -> PrivacyAssessment:
        """Create comprehensive privacy impact assessment"""
        pia_id = f"pia_{len(self.assessments) + 1:03d}"

        # Determine risk level based on data categories
        risk_level = RiskLevel.MEDIUM
        if data_categories:
            if "genetic_data" in data_categories or "health_data" in data_categories:
                risk_level = RiskLevel.HIGH
            if "biometric_data" in data_categories:
                risk_level = RiskLevel.VERY_HIGH

        # Default mitigation measures based on risk level
        mitigation_measures = [
            "Data encryption at rest and in transit",
            "Access control and authentication",
            "Regular security audits",
        ]

        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            mitigation_measures.extend(
                [
                    "Pseudonymization of personal data",
                    "Consent management system",
                    "Data retention policies",
                    "Incident response procedures",
                ]
            )

        pia = PrivacyAssessment(
            pia_id=pia_id,
            purpose=purpose,
            data_categories=data_categories or ["personal_data"],
            processing_activities=processing_activities or ["data_analysis"],
            risk_level=risk_level,
            status=PIAStatus.DRAFT,
            mitigation_measures=mitigation_measures,
            created_at=datetime.utcnow().isoformat() + "Z",
            updated_at=datetime.utcnow().isoformat() + "Z",
        )
        self.assessments[pia_id] = pia
        return pia

    def create_data_processing_agreement(
        self,
        partner_name: str,
        purpose: str,
        data_categories: List[str],
        retention_period: str,
    ) -> DataProcessingAgreement:
        """Create data processing agreement with partner"""
        dpa_id = f"dpa_{len(self.dpas) + 1:03d}"

        # Standard security measures for genomic data
        security_measures = [
            "End-to-end encryption (AES-256)",
            "Multi-factor authentication",
            "Regular security assessments",
            "Incident response procedures",
            "Data breach notification within 72 hours",
            "Staff training on data protection",
        ]

        # Calculate expiry date (default 3 years)
        expiry_date = (datetime.utcnow() + timedelta(days=1095)).isoformat() + "Z"

        dpa = DataProcessingAgreement(
            dpa_id=dpa_id,
            partner_name=partner_name,
            purpose=purpose,
            data_categories=data_categories,
            retention_period=retention_period,
            security_measures=security_measures,
            signed_date=datetime.utcnow().isoformat() + "Z",
            expiry_date=expiry_date,
            status="active",
        )
        self.dpas[dpa_id] = dpa
        return dpa

    def report_breach(
        self,
        description: str,
        affected_count: int,
        severity: str,
        data_categories: List[str] = None,
    ) -> BreachNotification:
        """Report data breach with enhanced tracking"""
        breach_id = f"breach_{len(self.breaches) + 1:03d}"

        # Calculate notification deadline (72 hours for regulatory)
        notification_deadline = (
            datetime.utcnow() + timedelta(hours=72)
        ).isoformat() + "Z"

        # Default containment measures
        containment_measures = [
            "Immediate system isolation",
            "Access revocation for affected accounts",
            "Forensic analysis initiated",
            "Incident response team activated",
        ]

        breach = BreachNotification(
            breach_id=breach_id,
            severity=BreachSeverity(severity),
            description=description,
            affected_count=affected_count,
            data_categories=data_categories or ["unknown"],
            reported_at=datetime.utcnow().isoformat() + "Z",
            status=BreachStatus.REPORTED,
            containment_measures=containment_measures,
            notification_deadline=notification_deadline,
        )
        self.breaches[breach_id] = breach
        return breach

    def update_breach_status(
        self, breach_id: str, status: str, notify_regulatory: bool = False
    ) -> bool:
        """Update breach status and handle notifications"""
        if breach_id not in self.breaches:
            return False

        breach = self.breaches[breach_id]
        breach.status = BreachStatus(status)

        if notify_regulatory:
            breach.regulatory_notified = True
            breach.status = BreachStatus.REGULATORY_NOTIFIED

        return True

    def get_compliance_status(self) -> Dict:
        """Get comprehensive GDPR compliance status"""
        approved_pias = sum(
            1 for p in self.assessments.values() if p.status == PIAStatus.APPROVED
        )
        total_pias = len(self.assessments)

        resolved_breaches = sum(
            1 for b in self.breaches.values() if b.status == BreachStatus.RESOLVED
        )
        total_breaches = len(self.breaches)

        active_dpas = sum(1 for d in self.dpas.values() if d.status == "active")
        total_dpas = len([d for d in self.dpas.values() if d.status != "template"])

        # Enhanced compliance scoring
        score = 0.0

        # PIA compliance (40% weight)
        if total_pias > 0:
            score += (approved_pias / total_pias) * 0.4

        # Breach management (30% weight)
        if total_breaches > 0:
            score += (resolved_breaches / total_breaches) * 0.3
        else:
            score += 0.3  # No breaches is good

        # DPA compliance (30% weight)
        if total_dpas > 0:
            score += (active_dpas / total_dpas) * 0.3
        else:
            score += 0.3  # No partners yet

        # Check for overdue breach notifications
        overdue_breaches = 0
        for breach in self.breaches.values():
            if breach.status in [BreachStatus.REPORTED, BreachStatus.INVESTIGATING]:
                deadline = datetime.fromisoformat(
                    breach.notification_deadline.replace("Z", "+00:00")
                )
                if datetime.utcnow().replace(tzinfo=deadline.tzinfo) > deadline:
                    overdue_breaches += 1

        return {
            "compliance_score": min(1.0, score),
            "privacy_assessments": {
                "total": total_pias,
                "approved": approved_pias,
                "pending_review": sum(
                    1
                    for p in self.assessments.values()
                    if p.status == PIAStatus.UNDER_REVIEW
                ),
            },
            "breach_notifications": {
                "total": total_breaches,
                "resolved": resolved_breaches,
                "overdue": overdue_breaches,
            },
            "data_processing_agreements": {
                "total": total_dpas,
                "active": active_dpas,
                "expiring_soon": self._count_expiring_dpas(),
            },
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

    def _count_expiring_dpas(self) -> int:
        """Count DPAs expiring within 90 days"""
        threshold = datetime.utcnow() + timedelta(days=90)
        count = 0
        for dpa in self.dpas.values():
            if dpa.status == "active" and dpa.expiry_date:
                expiry = datetime.fromisoformat(dpa.expiry_date.replace("Z", "+00:00"))
                if expiry.replace(tzinfo=None) <= threshold:
                    count += 1
        return count

    def generate_compliance_report(self) -> Dict:
        """Generate comprehensive GDPR compliance report"""
        status = self.get_compliance_status()

        # Risk assessment summary
        risk_summary = {
            "high_risk_activities": len(
                [
                    p
                    for p in self.assessments.values()
                    if p.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]
                ]
            ),
            "critical_breaches": len(
                [
                    b
                    for b in self.breaches.values()
                    if b.severity == BreachSeverity.CRITICAL
                ]
            ),
            "regulatory_notifications_required": len(
                [
                    b
                    for b in self.breaches.values()
                    if not b.regulatory_notified
                    and b.severity in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]
                ]
            ),
        }

        # Recommendations
        recommendations = []
        if status["privacy_assessments"]["pending_review"] > 0:
            recommendations.append(
                "Review and approve pending privacy impact assessments"
            )
        if status["breach_notifications"]["overdue"] > 0:
            recommendations.append(
                "Address overdue breach notifications to regulatory authorities"
            )
        if status["data_processing_agreements"]["expiring_soon"] > 0:
            recommendations.append("Renew expiring data processing agreements")
        if status["compliance_score"] < 0.8:
            recommendations.append(
                "Improve overall compliance score through systematic remediation"
            )

        return {
            "report_id": f"compliance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "compliance_status": status,
            "risk_summary": risk_summary,
            "recommendations": recommendations,
            "next_review_date": (datetime.utcnow() + timedelta(days=90)).isoformat()
            + "Z",
        }

    def list_assessments(self) -> List[PrivacyAssessment]:
        return list(self.assessments.values())

    def list_breaches(self) -> List[BreachNotification]:
        return list(self.breaches.values())

    def list_dpas(self) -> List[DataProcessingAgreement]:
        return [dpa for dpa in self.dpas.values() if dpa.status != "template"]

    def get_dpa_template(self) -> DataProcessingAgreement:
        """Get DPA template for new agreements"""
        return next(
            (dpa for dpa in self.dpas.values() if dpa.status == "template"), None
        )
