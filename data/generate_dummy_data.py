"""Generate realistic dummy customer datasets for the dashboard.

This module is intentionally lightweight and keeps data relationships consistent
across CRM, emails, support, Slack, and usage sources.
"""

from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from faker import Faker

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

fake = Faker()


def _customer_id(index: int) -> str:
    return f"CUST-{index:03d}"


def _iso_date(days_ago: int = 0) -> str:
    return (date.today() - timedelta(days=days_ago)).isoformat()


def _usage_trend_for_scenario(scenario: str) -> str:
    mapping = {
        "healthy": "Growing",
        "risk": "Declining",
        "support": "Stable",
        "payment": "Declining",
        "upsell": "Growing",
        "onboarding": "Stable",
        "inactive": "Inactive",
    }
    return mapping.get(scenario, "Stable")


def _sentiment_mix(scenario: str) -> list[str]:
    mapping = {
        "healthy": ["Positive", "Positive", "Neutral"],
        "risk": ["Negative", "Neutral", "Neutral"],
        "support": ["Neutral", "Negative", "Neutral"],
        "payment": ["Negative", "Neutral", "Negative"],
        "upsell": ["Positive", "Positive", "Neutral"],
        "onboarding": ["Positive", "Neutral", "Positive"],
        "inactive": ["Neutral", "Negative", "Neutral"],
    }
    return mapping.get(scenario, ["Neutral", "Neutral", "Positive"])


def _priority_for_scenario(scenario: str) -> str:
    if scenario in {"support", "risk", "payment"}:
        return "High"
    if scenario in {"upsell", "healthy"}:
        return "Low"
    return "Medium"


def _build_crm_record(index: int, scenario: str) -> dict[str, Any]:
    industry = random.choice([
        "SaaS",
        "Fintech",
        "Healthcare",
        "Retail",
        "Logistics",
        "Manufacturing",
        "Enterprise Software",
    ])
    plan = random.choice(["Growth", "Scale", "Enterprise", "Professional"])
    mrr = random.randint(4500, 28000)
    arr = mrr * 12
    renewal_date = date.today() + timedelta(days=random.randint(10, 120))
    company_size = random.choice(["1-10", "11-50", "51-200", "201-500", "500+"])
    account_status = "Active" if scenario != "inactive" else "Inactive"
    renewal_risk = "Low" if scenario in {"healthy", "upsell", "onboarding"} else "Medium"
    if scenario in {"risk", "payment"}:
        renewal_risk = "High"
    expansion_potential = "High" if scenario in {"upsell", "healthy"} else "Medium"

    return {
        "customer_id": _customer_id(index),
        "company_name": fake.company(),
        "industry": industry,
        "plan": plan,
        "mrr": mrr,
        "arr": arr,
        "renewal_date": renewal_date.isoformat(),
        "account_owner": fake.name(),
        "customer_since": (date.today() - timedelta(days=random.randint(180, 2500))).isoformat(),
        "country": fake.country(),
        "lifecycle_stage": random.choice(["Prospect", "Onboarding", "Expansion", "Renewal", "Retained"]),
        "company_size": company_size,
        "account_status": account_status,
        "renewal_risk": renewal_risk,
        "expansion_potential": expansion_potential,
    }


def _build_email_records(index: int, scenario: str, company_name: str) -> list[dict[str, Any]]:
    sentiments = _sentiment_mix(scenario)
    email_bodies = {
        "Positive": [
            f"The team at {company_name} is very happy with the onboarding experience and wants more product training.",
            f"Thank you for the support on our rollout. The dashboard reports are already saving our team time.",
        ],
        "Neutral": [
            f"We are reviewing the current usage and may discuss additional seats during the next planning meeting.",
            f"Our internal team is still evaluating whether to expand into more regions.",
        ],
        "Negative": [
            f"We have ongoing concerns about billing accuracy and need clearer visibility into our account status.",
            f"Several support tickets remain open and our team is frustrated with response times.",
        ],
    }

    emails: list[dict[str, Any]] = []
    count = random.randint(3, 8)
    for offset in range(count):
        sentiment = sentiments[offset % len(sentiments)]
        emails.append(
            {
                "customer_id": _customer_id(index),
                "date": _iso_date(random.randint(2, 120)),
                "subject": random.choice([
                    "Renewal discussion",
                    "Feature request",
                    "Pricing follow-up",
                    "Support follow-up",
                    "Positive feedback",
                    "Billing concern",
                    "Usage review",
                ]),
                "sender": fake.email(),
                "body": random.choice(email_bodies[sentiment]),
                "sentiment": sentiment,
            }
        )
    return emails


def _build_support_records(index: int, scenario: str) -> list[dict[str, Any]]:
    ticket_count = random.randint(0, 5)
    records: list[dict[str, Any]] = []
    for ticket_number in range(1, ticket_count + 1):
        priority = random.choice(["High", "Medium", "Low"])
        if scenario in {"risk", "payment", "support"}:
            priority = "High" if random.random() > 0.3 else "Medium"
        status = "Open" if priority == "High" else random.choice(["Open", "Pending", "Resolved"])
        category = random.choice(["Login issue", "Billing issue", "API issue", "Feature request", "Bug report", "Performance issue"])
        records.append(
            {
                "customer_id": _customer_id(index),
                "ticket_id": f"TKT-{index:03d}-{ticket_number:02d}",
                "priority": priority,
                "status": status,
                "created_date": _iso_date(random.randint(1, 90)),
                "category": category,
                "summary": f"{category} reported by customer contact.",
                "resolution_notes": "Awaiting customer confirmation." if status == "Open" else "Issue addressed and closed.",
            }
        )
    return records


def _build_slack_records(index: int, scenario: str) -> list[dict[str, Any]]:
    discussion_templates = {
        "healthy": [
            "Customer requested a follow-up to discuss an expansion into a second team.",
            "Customer praised onboarding and wants a training session for new users.",
        ],
        "risk": [
            "Renewal concern flagged by account team.",
            "Customer escalated visibility issues and asked for an executive check-in.",
        ],
        "support": [
            "Engineering investigating a high-priority login issue.",
            "Customer asked for a timeline on the bug fix.",
        ],
        "payment": [
            "Finance is waiting on invoice clarification from the customer.",
            "Customer raised a payment concern and is reviewing the latest invoice.",
        ],
        "upsell": [
            "Possible discount conversation for a premium plan upgrade.",
            "Revenue team flagged a strong expansion opportunity for the next quarter.",
        ],
        "onboarding": [
            "Customer is very happy after a smooth rollout and wants a feature walkthrough.",
            "Customer success team is aligning on training next week.",
        ],
        "inactive": [
            "Usage has dropped and the account appears to be at risk of churn.",
            "Account team is trying to re-engage the customer.",
        ],
    }
    messages = discussion_templates[scenario]
    slack_records: list[dict[str, Any]] = []
    for offset, body in enumerate(messages):
        slack_records.append(
            {
                "customer_id": _customer_id(index),
                "date": _iso_date(random.randint(1, 60) + offset),
                "author": fake.name(),
                "channel": random.choice(["#cs-success", "#sales", "#support", "#finance"]),
                "body": body,
            }
        )
    return slack_records[: random.randint(2, 6)]


def _build_usage_record(index: int, scenario: str) -> dict[str, Any]:
    trend = _usage_trend_for_scenario(scenario)
    active_users = random.randint(18, 260)
    logins = random.randint(70, 500)
    feature_usage = random.randint(120, 900)
    storage_used = random.randint(15, 520)
    projects_created = random.randint(5, 110)
    api_calls = random.randint(300, 18000)
    last_login = _iso_date(random.randint(2, 40))

    if trend == "Declining":
        active_users = max(6, active_users - random.randint(20, 150))
        logins = max(20, logins - random.randint(15, 220))
        feature_usage = max(20, feature_usage - random.randint(25, 350))
    elif trend == "Growing":
        active_users = active_users + random.randint(20, 120)
        logins = logins + random.randint(40, 220)
        feature_usage = feature_usage + random.randint(80, 380)
    elif trend == "Inactive":
        active_users = random.randint(2, 15)
        logins = random.randint(2, 40)
        feature_usage = random.randint(5, 55)
        last_login = _iso_date(random.randint(45, 120))

    return {
        "customer_id": _customer_id(index),
        "active_users": active_users,
        "logins": logins,
        "feature_usage": feature_usage,
        "storage_used": storage_used,
        "projects_created": projects_created,
        "api_calls": api_calls,
        "last_login": last_login,
        "usage_trend": trend,
    }


def generate_all_data() -> None:
    """Create the JSON fixtures if they do not already exist."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    scenarios = [
        "healthy",
        "risk",
        "support",
        "payment",
        "upsell",
        "onboarding",
        "inactive",
    ]

    crm_records: list[dict[str, Any]] = []
    email_records: list[dict[str, Any]] = []
    support_records: list[dict[str, Any]] = []
    slack_records: list[dict[str, Any]] = []
    usage_records: list[dict[str, Any]] = []

    for index in range(1, 21):
        scenario = scenarios[(index - 1) % len(scenarios)]
        crm_record = _build_crm_record(index, scenario)
        crm_records.append(crm_record)

        company_name = crm_record["company_name"]
        email_records.extend(_build_email_records(index, scenario, company_name))
        support_records.extend(_build_support_records(index, scenario))
        slack_records.extend(_build_slack_records(index, scenario))
        usage_records.append(_build_usage_record(index, scenario))

    _write_json(DATA_DIR / "crm.json", crm_records)
    _write_json(DATA_DIR / "emails.json", email_records)
    _write_json(DATA_DIR / "support.json", support_records)
    _write_json(DATA_DIR / "slack.json", slack_records)
    _write_json(DATA_DIR / "usage.json", usage_records)


def _write_json(path: Path, payload: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, indent=2)


def ensure_data_files_exist() -> None:
    """Ensure the JSON data files exist. If missing, generate them."""

    files = [
        DATA_DIR / "crm.json",
        DATA_DIR / "emails.json",
        DATA_DIR / "support.json",
        DATA_DIR / "slack.json",
        DATA_DIR / "usage.json",
    ]
    if any(not file_path.exists() for file_path in files):
        generate_all_data()


if __name__ == "__main__":
    generate_all_data()
