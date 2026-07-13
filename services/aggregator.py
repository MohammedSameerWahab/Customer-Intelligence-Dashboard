"""Aggregate customer data into a single profile used by the dashboard."""

from __future__ import annotations

from typing import Any

from services.health_score import calculate_health_score
from services.timeline import build_timeline


def build_customer_profile(customer_data: dict[str, Any]) -> dict[str, Any]:
    """Create a unified customer object consumed by the UI and AI service."""

    crm = customer_data.get("crm", {})
    emails = customer_data.get("emails", [])
    support = customer_data.get("support", [])
    slack = customer_data.get("slack", [])
    usage = customer_data.get("usage", {})

    health = calculate_health_score(
        {
            "crm": crm,
            "emails": emails,
            "support": support,
            "slack": slack,
            "usage": usage,
        }
    )
    timeline = build_timeline(
        {
            "crm": crm,
            "emails": emails,
            "support": support,
            "slack": slack,
            "usage": usage,
        }
    )

    return {
        "customer_id": customer_data.get("customer_id"),
        "crm": crm,
        "emails": emails,
        "support_tickets": support,
        "slack_messages": slack,
        "usage": usage,
        "timeline": timeline,
        "health_score": health,
    }
