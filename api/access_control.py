from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from consent_manager import ConsentManager, ConsentType


class AccessAction(Enum):
    """Types of data access actions"""

    READ_GENOMIC_DATA = "read_genomic_data"
    ANALYZE_VARIANTS = "analyze_variants"
    SHARE_DATA = "share_data"
    GENERATE_REPORTS = "generate_reports"
    EXECUTE_THEORY = "execute_theory"


@dataclass
class AccessRequest:
    """Data access request"""

    user_id: str
    action: AccessAction
    resource_id: str
    timestamp: str
    ip_address: str
    metadata: Dict


@dataclass
class AccessResult:
    """Result of access control check"""

    granted: bool
    reason: str
    consent_types_checked: List[ConsentType]
    audit_id: str


class AccessControlManager:
    """Manages consent-aware data access control"""

    def __init__(self, consent_manager: ConsentManager):
        self.consent_manager = consent_manager
        self.access_log: List[Dict] = []
        self.access_counter = 0

        # Define required consent types for each action
        self.action_consent_mapping = {
            AccessAction.READ_GENOMIC_DATA: [ConsentType.GENOMIC_ANALYSIS],
            AccessAction.ANALYZE_VARIANTS: [ConsentType.GENOMIC_ANALYSIS],
            AccessAction.SHARE_DATA: [ConsentType.DATA_SHARING],
            AccessAction.GENERATE_REPORTS: [ConsentType.GENOMIC_ANALYSIS],
            AccessAction.EXECUTE_THEORY: [
                ConsentType.GENOMIC_ANALYSIS,
                ConsentType.RESEARCH_PARTICIPATION,
            ],
        }

    def check_access(self, request: AccessRequest) -> AccessResult:
        """Check if access should be granted based on consent"""
        self.access_counter += 1
        audit_id = f"access_{self.access_counter:06d}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Get required consent types for this action
        required_consents = self.action_consent_mapping.get(request.action, [])

        if not required_consents:
            # No consent required for this action
            result = AccessResult(
                granted=True,
                reason="No consent required",
                consent_types_checked=[],
                audit_id=audit_id,
            )
        else:
            # Check all required consents
            missing_consents = []
            for consent_type in required_consents:
                if not self.consent_manager.check_consent(
                    request.user_id, consent_type, request.action.value
                ):
                    missing_consents.append(consent_type.value)

            if missing_consents:
                result = AccessResult(
                    granted=False,
                    reason=f"Missing consent: {', '.join(missing_consents)}",
                    consent_types_checked=required_consents,
                    audit_id=audit_id,
                )
            else:
                result = AccessResult(
                    granted=True,
                    reason="All required consents valid",
                    consent_types_checked=required_consents,
                    audit_id=audit_id,
                )

        # Log access attempt
        self._log_access_attempt(request, result)
        return result

    def _log_access_attempt(self, request: AccessRequest, result: AccessResult):
        """Log access attempt for audit trail"""
        log_entry = {
            "audit_id": result.audit_id,
            "user_id": request.user_id,
            "action": request.action.value,
            "resource_id": request.resource_id,
            "granted": result.granted,
            "reason": result.reason,
            "consent_types_checked": [ct.value for ct in result.consent_types_checked],
            "timestamp": request.timestamp,
            "ip_address": request.ip_address,
            "metadata": request.metadata,
        }
        self.access_log.append(log_entry)

    def get_access_log(
        self, user_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """Get access log entries"""
        if user_id:
            filtered_log = [
                entry for entry in self.access_log if entry["user_id"] == user_id
            ]
        else:
            filtered_log = self.access_log

        # Return most recent entries first
        return sorted(filtered_log, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_access_stats(self) -> Dict:
        """Get access control statistics"""
        total_requests = len(self.access_log)
        granted_requests = sum(1 for entry in self.access_log if entry["granted"])
        denied_requests = total_requests - granted_requests

        # Count by action
        by_action = {}
        for entry in self.access_log:
            action = entry["action"]
            by_action[action] = by_action.get(action, 0) + 1

        # Count unique users
        unique_users = len(set(entry["user_id"] for entry in self.access_log))

        return {
            "total_requests": total_requests,
            "granted_requests": granted_requests,
            "denied_requests": denied_requests,
            "grant_rate": (
                granted_requests / total_requests if total_requests > 0 else 0
            ),
            "by_action": by_action,
            "unique_users": unique_users,
        }
