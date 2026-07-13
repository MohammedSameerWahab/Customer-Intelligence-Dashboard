"""Deterministic customer health scoring rules."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def _days_between(start_date: str | None, end_date: date | None = None) -> int:
    if not start_date:
        return 999
    try:
        current = date.fromisoformat(start_date)
    except ValueError:
        return 999
    if end_date is None:
        end_date = date.today()
    return (end_date - current).days


def calculate_health_score(customer_profile: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic business-health score with explainable contributors."""

    score = 100
    contributors: list[str] = []

    crm = customer_profile.get("crm", {})
    emails = customer_profile.get("emails", [])
    support = customer_profile.get("support", [])
    usage = customer_profile.get("usage", {})

    for ticket in support:
        if str(ticket.get("status", "")).lower() != "resolved":
            priority = str(ticket.get("priority", "")).lower()
            if priority == "high":
                score -= 25
                contributors.append("-25 High priority unresolved support ticket")
            elif priority == "medium":
                score -= 15
                contributors.append("-15 Medium priority unresolved support ticket")
            else:
                score -= 5
                contributors.append("-5 Low priority unresolved support ticket")

    if str(usage.get("usage_trend", "")).lower() == "declining":
        score -= 20
        contributors.append("-20 Declining usage trend")

    last_login_days = _days_between(usage.get("last_login"))
    if last_login_days >= 30:
        score -= 20
        contributors.append("-20 No login for 30+ days")

    renewal_days = _days_between(crm.get("renewal_date"))
    if renewal_days <= 30:
        score -= 10
        contributors.append("-10 Renewal due within 30 days")

    if any(str(email.get("sentiment", "")).lower() == "negative" for email in emails):
        score -= 10
        contributors.append("-10 Negative customer email sentiment")

    if any("billing" in str(email.get("body", "")).lower() or "payment" in str(email.get("body", "")).lower() for email in emails):
        score -= 15
        contributors.append("-15 Payment concern indicated in emails")

    if any("upgrade" in str(item.get("body", "")).lower() or "expand" in str(item.get("body", "")).lower() for item in customer_profile.get("slack", [])):
        score += 10
        contributors.append("+10 Expansion interest in Slack")

    if int(usage.get("active_users", 0) or 0) >= 100:
        score += 10
        contributors.append("+10 Heavy product usage")

    if any(str(email.get("sentiment", "")).lower() == "positive" for email in emails):
        score += 10
        contributors.append("+10 Positive customer feedback")

    customer_since_days = _days_between(crm.get("customer_since"))
    if customer_since_days >= 365:
        score += 5
        contributors.append("+5 Long-term customer")

    score = max(0, min(100, score))

    if score >= 85:
        urgency = "Healthy"
    elif score >= 65:
        urgency = "Monitor"
    elif score >= 40:
        urgency = "Needs Attention"
    else:
        urgency = "Immediate Action"

    return {
        "score": score,
        "urgency": urgency,
        "contributors": contributors,
    }
