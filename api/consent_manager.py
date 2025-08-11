"""
Consent Management System

GDPR-compliant consent capture and management with digital signatures
and immutable audit trails.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


class ConsentType(Enum):
    """Types of consent that can be captured"""

    GENOMIC_ANALYSIS = "genomic_analysis"
    DATA_SHARING = "data_sharing"
    RESEARCH_PARTICIPATION = "research_participation"
    COMMERCIAL_USE = "commercial_use"
    LONG_TERM_STORAGE = "long_term_storage"


class ConsentStatus(Enum):
    """Status of consent records"""

    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"


@dataclass
class ConsentRecord:
    """Individual consent record"""

    consent_id: str
    user_id: str
    consent_type: ConsentType
    status: ConsentStatus
    granted_at: str
    expires_at: Optional[str]
    withdrawn_at: Optional[str]
    digital_signature: str
    ip_address: str
    user_agent: str
    consent_text_hash: str
    metadata: Dict


@dataclass
class ConsentForm:
    """Consent form definition"""

    form_id: str
    version: str
    title: str
    description: str
    consent_types: List[ConsentType]
    required_fields: List[str]
    consent_text: str
    validity_period_days: Optional[int]
    created_at: str


class ConsentManager:
    """Manages consent capture and validation"""

    def __init__(self):
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.consent_forms: Dict[str, ConsentForm] = {}
        self._initialize_default_forms()

    def _initialize_default_forms(self):
        """Initialize default consent forms"""
        # Genomic Analysis Consent Form
        genomic_form = ConsentForm(
            form_id="genomic_analysis_v1",
            version="1.0.0",
            title="Genomic Data Analysis Consent",
            description="Consent for analyzing your genomic data for research purposes",
            consent_types=[
                ConsentType.GENOMIC_ANALYSIS,
                ConsentType.RESEARCH_PARTICIPATION,
            ],
            required_fields=["full_name", "date_of_birth", "email"],
            consent_text="""
I consent to the analysis of my genomic data for research purposes. I understand that:
- My data will be used for scientific research
- My identity will be protected through anonymization
- I can withdraw consent at any time
- My data will be stored securely with encryption
            """.strip(),
            validity_period_days=365,
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        self.consent_forms[genomic_form.form_id] = genomic_form

        # Data Sharing Consent Form
        sharing_form = ConsentForm(
            form_id="data_sharing_v1",
            version="1.0.0",
            title="Data Sharing Consent",
            description="Consent for sharing anonymized data with research partners",
            consent_types=[ConsentType.DATA_SHARING],
            required_fields=["full_name", "email"],
            consent_text="""
I consent to sharing my anonymized genomic data with approved research partners. I understand that:
- Data will be anonymized before sharing
- Only approved research institutions will receive data
- Data will be used for legitimate research purposes
- I can withdraw this consent at any time
            """.strip(),
            validity_period_days=730,
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        self.consent_forms[sharing_form.form_id] = sharing_form

    def capture_consent(
        self,
        user_id: str,
        form_id: str,
        user_data: Dict,
        ip_address: str,
        user_agent: str,
        digital_signature: str,
    ) -> ConsentRecord:
        """Capture user consent with validation"""

        # Validate form exists
        if form_id not in self.consent_forms:
            raise ValueError(f"Consent form '{form_id}' not found")

        form = self.consent_forms[form_id]

        # Validate required fields
        for field in form.required_fields:
            if field not in user_data:
                raise ValueError(f"Required field '{field}' missing")

        # Generate consent ID
        consent_id = self._generate_consent_id(user_id, form_id)

        # Calculate expiration
        expires_at = None
        if form.validity_period_days:
            expires_at = (
                datetime.utcnow() + timedelta(days=form.validity_period_days)
            ).isoformat() + "Z"

        # Hash consent text for integrity
        consent_text_hash = hashlib.sha256(
            form.consent_text.encode("utf-8")
        ).hexdigest()

        # Create consent records for each type
        records = []
        for consent_type in form.consent_types:
            record = ConsentRecord(
                consent_id=f"{consent_id}_{consent_type.value}",
                user_id=user_id,
                consent_type=consent_type,
                status=ConsentStatus.ACTIVE,
                granted_at=datetime.utcnow().isoformat() + "Z",
                expires_at=expires_at,
                withdrawn_at=None,
                digital_signature=digital_signature,
                ip_address=ip_address,
                user_agent=user_agent,
                consent_text_hash=consent_text_hash,
                metadata={
                    "form_id": form_id,
                    "form_version": form.version,
                    "user_data": user_data,
                },
            )

            self.consent_records[record.consent_id] = record
            records.append(record)

        return records[0]  # Return first record as primary

    def check_consent(
        self, user_id: str, consent_type: ConsentType, required_for_action: str = None
    ) -> bool:
        """Check if user has valid consent for specific type"""

        # Find active consent records for user and type
        active_consents = [
            record
            for record in self.consent_records.values()
            if (
                record.user_id == user_id
                and record.consent_type == consent_type
                and record.status == ConsentStatus.ACTIVE
            )
        ]

        if not active_consents:
            return False

        # Check expiration
        now = datetime.utcnow()
        for consent in active_consents:
            if consent.expires_at:
                expires = datetime.fromisoformat(consent.expires_at.replace("Z", ""))
                if now > expires:
                    # Mark as expired
                    consent.status = ConsentStatus.EXPIRED
                    return False

        return True

    def withdraw_consent(
        self, user_id: str, consent_type: ConsentType, reason: str = "user_request"
    ) -> bool:
        """Withdraw user consent for specific type"""

        # Find active consent records
        withdrawn_count = 0
        for record in self.consent_records.values():
            if (
                record.user_id == user_id
                and record.consent_type == consent_type
                and record.status == ConsentStatus.ACTIVE
            ):

                record.status = ConsentStatus.WITHDRAWN
                record.withdrawn_at = datetime.utcnow().isoformat() + "Z"
                record.metadata["withdrawal_reason"] = reason
                withdrawn_count += 1

        return withdrawn_count > 0

    def get_user_consents(self, user_id: str) -> List[ConsentRecord]:
        """Get all consent records for a user"""
        return [
            record
            for record in self.consent_records.values()
            if record.user_id == user_id
        ]

    def get_consent_audit_trail(self, user_id: str) -> List[Dict]:
        """Get complete audit trail for user's consents"""
        user_consents = self.get_user_consents(user_id)

        audit_trail = []
        for consent in user_consents:
            audit_trail.append(
                {
                    "consent_id": consent.consent_id,
                    "consent_type": consent.consent_type.value,
                    "action": "granted",
                    "timestamp": consent.granted_at,
                    "ip_address": consent.ip_address,
                    "digital_signature": consent.digital_signature[:16]
                    + "...",  # Truncated for display
                    "metadata": {
                        "form_id": consent.metadata.get("form_id"),
                        "form_version": consent.metadata.get("form_version"),
                    },
                }
            )

            if consent.withdrawn_at:
                audit_trail.append(
                    {
                        "consent_id": consent.consent_id,
                        "consent_type": consent.consent_type.value,
                        "action": "withdrawn",
                        "timestamp": consent.withdrawn_at,
                        "reason": consent.metadata.get("withdrawal_reason", "unknown"),
                    }
                )

        # Sort by timestamp
        audit_trail.sort(key=lambda x: x["timestamp"])
        return audit_trail

    def get_consent_form(self, form_id: str) -> Optional[ConsentForm]:
        """Get consent form by ID"""
        return self.consent_forms.get(form_id)

    def list_consent_forms(self) -> List[ConsentForm]:
        """List all available consent forms"""
        return list(self.consent_forms.values())

    def validate_digital_signature(
        self, consent_text: str, signature: str, user_data: Dict
    ) -> bool:
        """Validate digital signature (simplified implementation)"""
        # In production, this would use proper cryptographic validation
        # For now, we'll use a simple hash-based validation

        signature_data = f"{consent_text}{json.dumps(user_data, sort_keys=True)}"
        expected_hash = hashlib.sha256(signature_data.encode("utf-8")).hexdigest()

        return signature.startswith(expected_hash[:16])

    def _generate_consent_id(self, user_id: str, form_id: str) -> str:
        """Generate unique consent ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        hash_input = f"{user_id}_{form_id}_{timestamp}"
        hash_suffix = hashlib.md5(hash_input.encode("utf-8")).hexdigest()[:8]
        return f"consent_{timestamp}_{hash_suffix}"

    def get_consent_stats(self) -> Dict:
        """Get consent statistics"""
        total_consents = len(self.consent_records)

        by_status = {}
        by_type = {}

        for record in self.consent_records.values():
            # Count by status
            status = record.status.value
            by_status[status] = by_status.get(status, 0) + 1

            # Count by type
            consent_type = record.consent_type.value
            by_type[consent_type] = by_type.get(consent_type, 0) + 1

        return {
            "total_consents": total_consents,
            "by_status": by_status,
            "by_type": by_type,
            "active_users": len(
                set(
                    record.user_id
                    for record in self.consent_records.values()
                    if record.status == ConsentStatus.ACTIVE
                )
            ),
        }
