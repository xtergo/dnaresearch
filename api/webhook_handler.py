"""Webhook handler for sequencing partner integration"""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class WebhookStatus(Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WebhookEvent:
    id: str
    partner_id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: str
    status: WebhookStatus
    signature: Optional[str] = None


class WebhookHandler:
    """Handle sequencing partner webhooks"""

    def __init__(self):
        self.partners = {
            "illumina": {"secret": "illumina_webhook_secret_key"},
            "oxford": {"secret": "oxford_webhook_secret_key"},
            "pacbio": {"secret": "pacbio_webhook_secret_key"},
        }
        self.events = {}  # In production, this would be a database

    def validate_signature(self, payload: str, signature: str, partner_id: str) -> bool:
        """Validate webhook signature"""
        if partner_id not in self.partners:
            return False

        secret = self.partners[partner_id]["secret"]
        expected_signature = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected_signature}", signature)

    def process_webhook(
        self, partner_id: str, event_data: Dict[str, Any], signature: str = None
    ) -> WebhookEvent:
        """Process incoming webhook"""
        event_id = f"{partner_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"

        event = WebhookEvent(
            id=event_id,
            partner_id=partner_id,
            event_type=event_data.get("event_type", "unknown"),
            data=event_data,
            timestamp=datetime.utcnow().isoformat() + "Z",
            status=WebhookStatus.RECEIVED,
            signature=signature,
        )

        # Store event
        self.events[event_id] = event

        # Process based on event type
        if event.event_type == "sequencing_complete":
            self._handle_sequencing_complete(event)
        elif event.event_type == "qc_complete":
            self._handle_qc_complete(event)
        elif event.event_type == "analysis_complete":
            self._handle_analysis_complete(event)

        return event

    def _handle_sequencing_complete(self, event: WebhookEvent):
        """Handle sequencing completion"""
        event.status = WebhookStatus.PROCESSING

        # Extract key data
        file_urls = event.data.get("file_urls", [])

        # Simulate processing
        event.data["processed_files"] = len(file_urls)
        event.data["processing_started"] = datetime.utcnow().isoformat() + "Z"

        event.status = WebhookStatus.COMPLETED

    def _handle_qc_complete(self, event: WebhookEvent):
        """Handle QC completion"""
        event.status = WebhookStatus.PROCESSING

        qc_metrics = event.data.get("qc_metrics", {})
        passed = qc_metrics.get("passed", False)

        event.data["qc_passed"] = passed
        event.data["qc_processed"] = datetime.utcnow().isoformat() + "Z"

        event.status = WebhookStatus.COMPLETED

    def _handle_analysis_complete(self, event: WebhookEvent):
        """Handle analysis completion"""
        event.status = WebhookStatus.PROCESSING

        results = event.data.get("analysis_results", {})
        variant_count = results.get("variant_count", 0)

        event.data["variants_found"] = variant_count
        event.data["analysis_processed"] = datetime.utcnow().isoformat() + "Z"

        event.status = WebhookStatus.COMPLETED

    def get_event(self, event_id: str) -> Optional[WebhookEvent]:
        """Get webhook event by ID"""
        return self.events.get(event_id)

    def get_partner_events(self, partner_id: str) -> list:
        """Get all events for a partner"""
        return [
            event for event in self.events.values() if event.partner_id == partner_id
        ]
