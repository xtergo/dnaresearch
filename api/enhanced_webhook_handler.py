"""Enhanced webhook handler with retry, queuing, and partner management"""

import asyncio
import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class WebhookStatus(Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class EventType(Enum):
    SEQUENCING_COMPLETE = "sequencing_complete"
    QC_COMPLETE = "qc_complete"
    ANALYSIS_COMPLETE = "analysis_complete"
    UPLOAD_COMPLETE = "upload_complete"
    ERROR_NOTIFICATION = "error_notification"


@dataclass
class WebhookEvent:
    id: str
    partner_id: str
    event_type: EventType
    data: Dict[str, Any]
    timestamp: str
    status: WebhookStatus
    signature: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    next_retry: Optional[str] = None
    error_message: Optional[str] = None
    processed_at: Optional[str] = None


@dataclass
class Partner:
    id: str
    name: str
    secret: str
    active: bool = True
    supported_events: List[EventType] = field(default_factory=list)
    webhook_url: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 3


class EnhancedWebhookHandler:
    """Enhanced webhook handler with retry, queuing, and partner management"""

    def __init__(self):
        self.partners = {
            "illumina": Partner(
                id="illumina",
                name="Illumina Inc.",
                secret="illumina_webhook_secret_key_2025",
                supported_events=[EventType.SEQUENCING_COMPLETE, EventType.QC_COMPLETE],
                webhook_url="https://api.illumina.com/webhooks/dna-research",
            ),
            "oxford": Partner(
                id="oxford",
                name="Oxford Nanopore Technologies",
                secret="oxford_webhook_secret_key_2025",
                supported_events=[EventType.SEQUENCING_COMPLETE, EventType.ANALYSIS_COMPLETE],
                webhook_url="https://api.nanoporetech.com/webhooks/dna-research",
            ),
            "pacbio": Partner(
                id="pacbio",
                name="Pacific Biosciences",
                secret="pacbio_webhook_secret_key_2025",
                supported_events=[EventType.SEQUENCING_COMPLETE, EventType.ANALYSIS_COMPLETE],
                webhook_url="https://api.pacb.com/webhooks/dna-research",
            ),
        }
        self.events = {}
        self.event_queue = asyncio.Queue()
        self.processing = False

    def validate_signature(self, payload: str, signature: str, partner_id: str) -> bool:
        """Validate webhook signature with enhanced security"""
        if partner_id not in self.partners:
            return False

        partner = self.partners[partner_id]
        if not partner.active:
            return False

        expected_signature = hmac.new(
            partner.secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected_signature}", signature)

    async def process_webhook(
        self, partner_id: str, event_data: Dict[str, Any], signature: str = None
    ) -> WebhookEvent:
        """Process incoming webhook with enhanced validation"""
        # Validate partner
        if partner_id not in self.partners:
            raise ValueError(f"Unknown partner: {partner_id}")

        partner = self.partners[partner_id]
        if not partner.active:
            raise ValueError(f"Partner {partner_id} is inactive")

        # Validate event type
        try:
            event_type = EventType(event_data.get("event_type", "unknown"))
        except ValueError:
            raise ValueError(f"Unsupported event type: {event_data.get('event_type')}")

        if event_type not in partner.supported_events:
            raise ValueError(f"Event type {event_type.value} not supported by {partner_id}")

        # Create event
        event_id = f"{partner_id}_{uuid4().hex[:8]}_{int(datetime.utcnow().timestamp())}"
        event = WebhookEvent(
            id=event_id,
            partner_id=partner_id,
            event_type=event_type,
            data=event_data,
            timestamp=datetime.utcnow().isoformat() + "Z",
            status=WebhookStatus.RECEIVED,
            signature=signature,
            max_retries=partner.max_retries,
        )

        # Store event
        self.events[event_id] = event

        # Queue for processing
        await self.event_queue.put(event)

        # Start processing if not already running
        if not self.processing:
            asyncio.create_task(self._process_event_queue())

        return event

    async def _process_event_queue(self):
        """Process events from the queue"""
        self.processing = True
        try:
            while not self.event_queue.empty():
                event = await self.event_queue.get()
                await self._process_single_event(event)
        finally:
            self.processing = False

    async def _process_single_event(self, event: WebhookEvent):
        """Process a single webhook event"""
        try:
            event.status = WebhookStatus.PROCESSING

            if event.event_type == EventType.SEQUENCING_COMPLETE:
                await self._handle_sequencing_complete(event)
            elif event.event_type == EventType.QC_COMPLETE:
                await self._handle_qc_complete(event)
            elif event.event_type == EventType.ANALYSIS_COMPLETE:
                await self._handle_analysis_complete(event)
            elif event.event_type == EventType.UPLOAD_COMPLETE:
                await self._handle_upload_complete(event)
            elif event.event_type == EventType.ERROR_NOTIFICATION:
                await self._handle_error_notification(event)

            event.status = WebhookStatus.COMPLETED
            event.processed_at = datetime.utcnow().isoformat() + "Z"

        except Exception as e:
            event.error_message = str(e)
            if event.retry_count < event.max_retries:
                await self._schedule_retry(event)
            else:
                event.status = WebhookStatus.FAILED

    async def _handle_sequencing_complete(self, event: WebhookEvent):
        """Handle sequencing completion with enhanced processing"""
        data = event.data
        
        # Extract and validate required fields
        sample_id = data.get("sample_id")
        if not sample_id:
            raise ValueError("Missing required field: sample_id")

        file_urls = data.get("file_urls", [])
        run_id = data.get("run_id")
        metadata = data.get("metadata", {})

        # Process files
        processed_files = []
        for url in file_urls:
            file_info = {
                "url": url,
                "processed_at": datetime.utcnow().isoformat() + "Z",
                "status": "ready_for_analysis"
            }
            processed_files.append(file_info)

        # Update event data
        event.data.update({
            "processed_files": processed_files,
            "file_count": len(file_urls),
            "processing_completed_at": datetime.utcnow().isoformat() + "Z",
            "next_step": "quality_control"
        })

    async def _handle_qc_complete(self, event: WebhookEvent):
        """Handle QC completion with enhanced metrics"""
        data = event.data
        qc_metrics = data.get("qc_metrics", {})
        
        # Enhanced QC processing
        quality_score = qc_metrics.get("quality_score", 0)
        coverage = qc_metrics.get("coverage", "0x")
        passed = qc_metrics.get("passed", False)

        # Determine next steps based on QC results
        next_step = "variant_calling" if passed else "resequencing_required"
        
        event.data.update({
            "qc_passed": passed,
            "quality_assessment": {
                "score": quality_score,
                "coverage": coverage,
                "recommendation": "proceed" if passed else "review_required"
            },
            "qc_processed_at": datetime.utcnow().isoformat() + "Z",
            "next_step": next_step
        })

    async def _handle_analysis_complete(self, event: WebhookEvent):
        """Handle analysis completion with enhanced results"""
        data = event.data
        results = data.get("analysis_results", {})
        
        variant_count = results.get("variant_count", 0)
        analysis_type = results.get("analysis_type", "unknown")
        reference = results.get("reference", "unknown")

        # Enhanced analysis processing
        event.data.update({
            "variants_found": variant_count,
            "analysis_summary": {
                "type": analysis_type,
                "reference_genome": reference,
                "variant_count": variant_count,
                "analysis_quality": "high" if variant_count > 1000 else "standard"
            },
            "analysis_processed_at": datetime.utcnow().isoformat() + "Z",
            "next_step": "report_generation"
        })

    async def _handle_upload_complete(self, event: WebhookEvent):
        """Handle file upload completion"""
        data = event.data
        file_info = data.get("file_info", {})
        
        event.data.update({
            "upload_verified": True,
            "file_size_mb": file_info.get("size_mb", 0),
            "checksum_verified": file_info.get("checksum_valid", False),
            "upload_processed_at": datetime.utcnow().isoformat() + "Z",
            "next_step": "file_processing"
        })

    async def _handle_error_notification(self, event: WebhookEvent):
        """Handle error notifications from partners"""
        data = event.data
        error_info = data.get("error", {})
        
        event.data.update({
            "error_processed": True,
            "error_severity": error_info.get("severity", "unknown"),
            "error_code": error_info.get("code", "unknown"),
            "error_processed_at": datetime.utcnow().isoformat() + "Z",
            "requires_attention": error_info.get("severity") in ["high", "critical"]
        })

    async def _schedule_retry(self, event: WebhookEvent):
        """Schedule event for retry with exponential backoff"""
        event.retry_count += 1
        event.status = WebhookStatus.RETRYING
        
        # Exponential backoff: 2^retry_count minutes
        delay_minutes = 2 ** event.retry_count
        next_retry = datetime.utcnow() + timedelta(minutes=delay_minutes)
        event.next_retry = next_retry.isoformat() + "Z"
        
        # In a real implementation, this would use a task scheduler
        await asyncio.sleep(delay_minutes * 60)
        await self.event_queue.put(event)

    def get_event(self, event_id: str) -> Optional[WebhookEvent]:
        """Get webhook event by ID"""
        return self.events.get(event_id)

    def get_partner_events(self, partner_id: str, limit: int = 50) -> List[WebhookEvent]:
        """Get events for a specific partner"""
        partner_events = [
            event for event in self.events.values() 
            if event.partner_id == partner_id
        ]
        return sorted(partner_events, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_events_by_status(self, status: WebhookStatus) -> List[WebhookEvent]:
        """Get events by status"""
        return [event for event in self.events.values() if event.status == status]

    def get_partner_info(self, partner_id: str) -> Optional[Partner]:
        """Get partner information"""
        return self.partners.get(partner_id)

    def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook processing statistics"""
        total_events = len(self.events)
        status_counts = {}
        partner_counts = {}
        
        for event in self.events.values():
            status_counts[event.status.value] = status_counts.get(event.status.value, 0) + 1
            partner_counts[event.partner_id] = partner_counts.get(event.partner_id, 0) + 1
        
        return {
            "total_events": total_events,
            "status_distribution": status_counts,
            "partner_distribution": partner_counts,
            "active_partners": len([p for p in self.partners.values() if p.active]),
            "queue_size": self.event_queue.qsize() if hasattr(self.event_queue, 'qsize') else 0
        }