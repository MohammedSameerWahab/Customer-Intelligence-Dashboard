"""Create a chronological timeline of recent customer activity."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def build_timeline(customer_profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Merge CRM, email, support, Slack, and usage signals into one timeline."""

    events: list[dict[str, Any]] = []

    # Use `or {}` to prevent AttributeError if the key exists but its value is explicitly None
    crm = customer_profile.get("crm") or {}
    if crm.get("renewal_date"):
        events.append(
            {
                "date": crm.get("renewal_date"),
                "event_type": "CRM Update",
                "description": f"Renewal on {crm.get('renewal_date')}",
                "icon": "📄",
            }
        )

    # Use `or []` to prevent TypeError when iterating if the value is explicitly None
    for email in customer_profile.get("emails") or []:
        event_date = email.get("date")
        if event_date:
            events.append(
                {
                    "date": event_date,
                    "event_type": "Email",
                    "description": f"{email.get('sentiment', 'Neutral').title()} email: {email.get('subject', 'No subject')}",
                    "icon": "📧",
                }
            )

    for ticket in customer_profile.get("support") or []:
        event_date = ticket.get("created_date")
        if event_date:
            events.append(
                {
                    "date": event_date,
                    "event_type": "Support Ticket",
                    "description": f"{ticket.get('priority', 'Unknown').title()} ticket: {ticket.get('summary', 'No summary')}",
                    "icon": "🎫",
                }
            )

    for message in customer_profile.get("slack") or []:
        event_date = message.get("date")
        if event_date:
            events.append(
                {
                    "date": event_date,
                    "event_type": "Slack",
                    "description": message.get("body", "No message body"),
                    "icon": "💬",
                }
            )

    usage = customer_profile.get("usage") or {}
    if usage.get("last_login"):
        events.append(
            {
                "date": usage.get("last_login"),
                "event_type": "Usage",
                "description": f"Last login on {usage.get('last_login')} with {usage.get('active_users', 0)} active users",
                "icon": "📈",
            }
        )

    def sort_key(item: dict[str, Any]) -> tuple[float, str]:
        parsed = _parse_date(item.get("date"))
        # Using a float preserves fractional seconds for highly accurate chronological sorting
        return (parsed.timestamp() if parsed else 0.0, item.get("event_type", ""))

    # Note: reverse=True will return the newest events first. 
    # Change to reverse=False if you want oldest events first.
    events.sort(key=sort_key, reverse=True)
    return events