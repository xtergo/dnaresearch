"""Enhanced webhook API endpoints"""

from enhanced_webhook_handler import WebhookStatus
from fastapi import HTTPException


def get_enhanced_webhook_event(event_id: str, enhanced_webhook_handler):
    """Get enhanced webhook event details"""
    event = enhanced_webhook_handler.get_event(event_id)
    if event:
        return {
            "id": event.id,
            "partner_id": event.partner_id,
            "event_type": event.event_type.value,
            "status": event.status.value,
            "timestamp": event.timestamp,
            "data": event.data,
            "retry_count": event.retry_count,
            "max_retries": event.max_retries,
            "next_retry": event.next_retry,
            "error_message": event.error_message,
            "processed_at": event.processed_at,
        }
    return None


def get_enhanced_partner_events(partner: str, limit: int, enhanced_webhook_handler):
    """Get enhanced partner events"""
    enhanced_events = enhanced_webhook_handler.get_partner_events(partner, limit)

    formatted_events = [
        {
            "id": event.id,
            "event_type": event.event_type.value,
            "status": event.status.value,
            "timestamp": event.timestamp,
            "retry_count": event.retry_count,
            "processed_at": event.processed_at,
            "data": event.data,
        }
        for event in enhanced_events
    ]

    partner_info = enhanced_webhook_handler.get_partner_info(partner)

    return {
        "partner_id": partner,
        "count": len(formatted_events),
        "events": formatted_events,
        "partner_info": {
            "name": partner_info.name if partner_info else "Unknown",
            "active": partner_info.active if partner_info else False,
        },
    }


def get_webhook_statistics(enhanced_webhook_handler):
    """Get webhook processing statistics"""
    return enhanced_webhook_handler.get_webhook_stats()


def list_webhook_partners(enhanced_webhook_handler):
    """List all webhook partners"""
    partners = []
    for partner_id, partner in enhanced_webhook_handler.partners.items():
        partners.append(
            {
                "id": partner.id,
                "name": partner.name,
                "active": partner.active,
                "supported_events": [event.value for event in partner.supported_events],
                "webhook_url": partner.webhook_url,
                "timeout_seconds": partner.timeout_seconds,
                "max_retries": partner.max_retries,
            }
        )

    return {
        "partners": partners,
        "count": len(partners),
        "active_count": len([p for p in partners if p["active"]]),
    }


def list_webhook_events(
    status: str, partner: str, limit: int, enhanced_webhook_handler
):
    """List webhook events with filtering"""
    events = list(enhanced_webhook_handler.events.values())

    # Apply filters
    if status:
        try:
            status_enum = WebhookStatus(status)
            events = [e for e in events if e.status == status_enum]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    if partner:
        events = [e for e in events if e.partner_id == partner]

    # Sort by timestamp (newest first) and limit
    events = sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]

    formatted_events = [
        {
            "id": event.id,
            "partner_id": event.partner_id,
            "event_type": event.event_type.value,
            "status": event.status.value,
            "timestamp": event.timestamp,
            "retry_count": event.retry_count,
            "processed_at": event.processed_at,
        }
        for event in events
    ]

    return {
        "events": formatted_events,
        "count": len(formatted_events),
        "total_events": len(enhanced_webhook_handler.events),
    }
