"""Derive simple, traceable evidence strings for customer recommendations."""

from __future__ import annotations

from datetime import date
from typing import Any


def _days_until(target_date: str | None) -> int | None:
    if not target_date:
        return None
    try:
        target = date.fromisoformat(target_date)
    except ValueError:
        return None
    return max(0, (target - date.today()).days)


def build_evidence(customer_profile: dict[str, Any]) -> list[str]:
    """Create a concise evidence list from aggregated customer signals."""

    crm = customer_profile.get("crm", {})
    usage = customer_profile.get("usage", {})
    support = customer_profile.get("support_tickets", [])
    emails = customer_profile.get("emails", [])
    slack = customer_profile.get("slack_messages", [])

    evidence: list[str] = []

    renewal_days = _days_until(crm.get("renewal_date"))
    if renewal_days is not None:
        evidence.append(f"Renewal due in {renewal_days} days.")

    if usage.get("usage_trend") == "Declining":
        evidence.append("Usage trend is declining.")
    elif usage.get("usage_trend") == "Growing":
        evidence.append("Usage trend is growing.")

    if support:
        unresolved = [ticket for ticket in support if str(ticket.get("status", "")).lower() != "resolved"]
        if unresolved:
            ticket = unresolved[0]
            evidence.append(
                f"Open support ticket {ticket.get('ticket_id', 'unknown')} remains unresolved with {ticket.get('priority', 'unknown').lower()} priority."
            )

    if emails:
        negative_emails = [email for email in emails if str(email.get("sentiment", "")).lower() == "negative"]
        if negative_emails:
            evidence.append("A recent email contains negative sentiment about billing or support.")

    if slack:
        expansion_mentions = [message for message in slack if "expand" in str(message.get("body", "")).lower() or "upgrade" in str(message.get("body", "")).lower()]
        if expansion_mentions:
            evidence.append("Slack notes mention expansion or upgrade interest.")

    if usage.get("active_users"):
        evidence.append(f"Current active users are {usage.get('active_users')}.")

    return evidence[:5]
