"""Load and normalize the generated customer datasets."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def _safe_load_json(path: Path) -> list[dict[str, Any]]:
    """Load JSON content from disk and return a cleaned list of dictionaries."""

    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file_handle:
            payload = json.load(file_handle)
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def load_customer_data() -> dict[str, Any]:
    """Load all JSON datasets and group records by customer ID."""

    crm = _safe_load_json(DATA_DIR / "crm.json")
    emails = _safe_load_json(DATA_DIR / "emails.json")
    support = _safe_load_json(DATA_DIR / "support.json")
    slack = _safe_load_json(DATA_DIR / "slack.json")
    usage = _safe_load_json(DATA_DIR / "usage.json")

    grouped_crm: dict[str, dict[str, Any]] = {}
    grouped_emails: dict[str, list[dict[str, Any]]] = defaultdict(list)
    grouped_support: dict[str, list[dict[str, Any]]] = defaultdict(list)
    grouped_slack: dict[str, list[dict[str, Any]]] = defaultdict(list)
    grouped_usage: dict[str, dict[str, Any]] = {}

    for record in crm:
        customer_id = str(record.get("customer_id", "")).strip()
        if customer_id:
            grouped_crm[customer_id] = record

    for record in emails:
        customer_id = str(record.get("customer_id", "")).strip()
        if customer_id:
            grouped_emails[customer_id].append(record)

    for record in support:
        customer_id = str(record.get("customer_id", "")).strip()
        if customer_id:
            grouped_support[customer_id].append(record)

    for record in slack:
        customer_id = str(record.get("customer_id", "")).strip()
        if customer_id:
            grouped_slack[customer_id].append(record)

    for record in usage:
        customer_id = str(record.get("customer_id", "")).strip()
        if customer_id:
            grouped_usage[customer_id] = record

    customer_ids = sorted(
        set(grouped_crm)
        | set(grouped_emails)
        | set(grouped_support)
        | set(grouped_slack)
        | set(grouped_usage)
    )

    customers: list[dict[str, Any]] = []
    for customer_id in customer_ids:
        customers.append(
            {
                "customer_id": customer_id,
                "crm": grouped_crm.get(customer_id, {}),
                "emails": grouped_emails.get(customer_id, []),
                "support": grouped_support.get(customer_id, []),
                "slack": grouped_slack.get(customer_id, []),
                "usage": grouped_usage.get(customer_id, {}),
            }
        )

    return {
        "customers": customers,
        "crm": grouped_crm,
        "emails": grouped_emails,
        "support": grouped_support,
        "slack": grouped_slack,
        "usage": grouped_usage,
    }


def get_customer_by_id(customer_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Return a single normalized customer payload."""

    for customer in data.get("customers", []):
        if customer.get("customer_id") == customer_id:
            return customer
    return {}
