"""Generate a structured customer brief using a single LLM request."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT_DIR / "prompts" / "account_summary.txt"

load_dotenv(ROOT_DIR / ".env", override=False)


def _load_prompt() -> str:
    """Load the reusable AI prompt template from disk."""

    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "Return valid JSON only."


def _prepare_payload(customer_profile: dict[str, Any]) -> dict[str, Any]:
    """Flatten the aggregated customer profile into a compact prompt payload."""

    return {
        "customer_id": customer_profile.get("customer_id"),
        "crm": customer_profile.get("crm", {}),
        "emails": customer_profile.get("emails", []),
        "support": customer_profile.get("support_tickets", []),
        "slack": customer_profile.get("slack_messages", []),
        "usage": customer_profile.get("usage", {}),
        "health_score": customer_profile.get("health_score", {}),
        "timeline": customer_profile.get("timeline", []),
    }


def _extract_json_text(text: str) -> str:
    """Strip any markdown code fences to recover a raw JSON payload."""

    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()
    return cleaned


def _normalise_brief(parsed: dict[str, Any]) -> dict[str, Any]:
    """Coerce the parsed AI payload into the dashboard-safe structure."""

    confidence = parsed.get("confidence", 0)
    try:
        confidence_value = max(0, min(100, int(confidence)))
    except (TypeError, ValueError):
        confidence_value = 0

    return {
        "summary": str(parsed.get("summary", "No summary provided.")),
        "sentiment": str(parsed.get("sentiment", "Neutral")),
        "risks": parsed.get("risks", []) if isinstance(parsed.get("risks", []), list) else [str(parsed.get("risks", []))],
        "opportunities": parsed.get("opportunities", []) if isinstance(parsed.get("opportunities", []), list) else [str(parsed.get("opportunities", []))],
        "recommendation": str(parsed.get("recommendation", "No recommendation provided.")),
        "evidence": parsed.get("evidence", []) if isinstance(parsed.get("evidence", []), list) else [str(parsed.get("evidence", []))],
        "confidence": confidence_value,
    }


def generate_customer_brief(customer_profile: dict[str, Any]) -> dict[str, Any]:
    """Return a structured Python dictionary with customer summary, sentiment, and evidence."""

    api_key = os.getenv("OPENAI_API_KEY", "") or os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        return {
            "summary": "AI analysis is unavailable because no OpenAI API key is configured.",
            "sentiment": "Neutral",
            "risks": ["AI analysis unavailable"],
            "opportunities": ["Manual review required"],
            "recommendation": "Add an OpenAI-compatible API key to continue AI analysis.",
            "evidence": ["No API key configured in environment."],
            "confidence": 0,
        }

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", None),
    )

    prompt = _load_prompt()
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": json.dumps(_prepare_payload(customer_profile), indent=2),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        message = response.choices[0].message
        content = message.content
        if isinstance(content, list):
            text_output = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        else:
            text_output = str(content or "")
        text_output = _extract_json_text(text_output)
    except Exception:
        return {
            "summary": "AI analysis is temporarily unavailable.",
            "sentiment": "Neutral",
            "risks": ["Model request failed"],
            "opportunities": ["Manual review required"],
            "recommendation": "Retry the AI analysis after confirming the OpenRouter endpoint and credentials.",
            "evidence": ["The AI request could not be completed at this time."],
            "confidence": 0,
        }

    try:
        parsed = json.loads(text_output)
    except json.JSONDecodeError:
        return {
            "summary": "AI analysis returned an invalid response format.",
            "sentiment": "Neutral",
            "risks": ["Invalid JSON response"],
            "opportunities": ["Manual review required"],
            "recommendation": "Retry the AI analysis to produce a structured customer brief.",
            "evidence": ["AI response could not be parsed as JSON."],
            "confidence": 0,
        }

    return _normalise_brief(parsed)
