"""Customer Intelligence Dashboard application entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from data.generate_dummy_data import ensure_data_files_exist
from services.aggregator import build_customer_profile
from services.ai_summary import generate_customer_brief
from services.evidence import build_evidence
from services.loader import get_customer_by_id, load_customer_data

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env", override=False)


def _render_urgency_badge(urgency: str) -> None:
    """Render a simple urgency badge with a color-coded label."""

    palette = {
        "Healthy": "#40a316",
        "Monitor": "#d9c006",
        "Needs Attention": "#ea820c",
        "Immediate Action": "#dc2626",
    }
    color = palette.get(urgency, "#475569")
    st.markdown(
        f"<div style='display:inline-block;padding:8px 14px;border-radius:999px;background:{color};color:white;font-weight:700;'>"
        f"{urgency}</div>",
        unsafe_allow_html=True,
    )


def _render_timeline(events: list[dict[str, Any]]) -> None:
    """Visualize event history in a lightweight Plotly timeline."""

    if not events:
        st.info("No timeline events are available for this customer.")
        return

    timeline_df = pd.DataFrame(events)
    timeline_df["date"] = pd.to_datetime(timeline_df["date"], errors="coerce")
    timeline_df = timeline_df.dropna(subset=["date"]).sort_values("date", ascending=False)
    timeline_df = timeline_df.reset_index(drop=True)
    timeline_df["label"] = timeline_df.apply(lambda row: f"{row['icon']} {row['event_type']}", axis=1)
    timeline_df["y"] = list(range(len(timeline_df)))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=timeline_df["date"],
            y=timeline_df["y"],
            mode="markers+text",
            text=timeline_df["label"],
            textposition="middle right",
            marker={"size": 12, "color": "#2563eb"},
            hovertemplate="<b>%{text}</b><br>%{customdata}<extra></extra>",
            customdata=timeline_df["description"],
        )
    )
    fig.update_yaxes(visible=False, showgrid=False, autorange="reversed")
    fig.update_xaxes(title="Date", type="date")
    fig.update_layout(
        height=max(320, len(timeline_df) * 55),
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        paper_bgcolor="white",
        plot_bgcolor="#f8fafc",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


st.set_page_config(page_title="Customer Intelligence Dashboard", page_icon="📊", layout="wide")

st.title("Customer Intelligence Dashboard")
st.caption("AI-powered account briefing for Sales and Customer Success teams")

ensure_data_files_exist()
raw_data = load_customer_data()
customer_ids = [customer.get("customer_id", "") for customer in raw_data.get("customers", [])]
customer_ids = [customer_id for customer_id in customer_ids if customer_id]

if not customer_ids:
    st.warning("No customer records were found. The dummy data generator will create them on the next run.")
    st.stop()

with st.sidebar:
    st.header("Controls")
    selected_customer = st.selectbox("Customer selector", customer_ids, index=0)
    refresh_ai = st.button("Refresh AI analysis")
    regenerate_data = st.button("Regenerate dummy dataset")

    if regenerate_data:
        ensure_data_files_exist()
        st.rerun()

    st.markdown("---")
    st.caption("Project information")
    st.write("This dashboard blends CRM, email, support, Slack, and usage signals into a single customer brief.")

customer_payload = get_customer_by_id(selected_customer, raw_data)
customer_profile = build_customer_profile(customer_payload)
health = customer_profile.get("health_score", {})
score = int(health.get("score", 0))
urgency = health.get("urgency", "Monitor")

brief_cache = st.session_state.setdefault("brief_cache", {})
if refresh_ai:
    with st.spinner("Generating AI customer brief..."):
        brief_cache[selected_customer] = generate_customer_brief(customer_profile)
elif selected_customer not in brief_cache:
    with st.spinner("Generating AI customer brief..."):
        brief_cache[selected_customer] = generate_customer_brief(customer_profile)

ai_brief = brief_cache[selected_customer]

crm = customer_profile.get("crm", {})
account_name = crm.get("company_name", selected_customer)
industry = crm.get("industry", "Unknown")
plan = crm.get("plan", "Unknown")
mrr = crm.get("mrr", 0)
renewal_date = crm.get("renewal_date", "Unknown")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Health Score", score)
with col2:
    st.metric("Urgency", urgency)
with col3:
    st.metric("Sentiment", ai_brief.get("sentiment", "Neutral"))
with col4:
    st.metric("Confidence", ai_brief.get("confidence", 0))

st.progress(score / 100)

st.subheader("Account Overview")
overview_cols = st.columns(5)
with overview_cols[0]:
    st.markdown(f"**Customer**\n{account_name}")
with overview_cols[1]:
    st.markdown(f"**Industry**\n{industry}")
with overview_cols[2]:
    st.markdown(f"**Plan**\n{plan}")
with overview_cols[3]:
    st.markdown(f"**MRR**\n${mrr:,.0f}")
with overview_cols[4]:
    st.markdown(f"**Renewal Date**\n{renewal_date}")

st.markdown("---")

st.subheader("Executive Summary")
st.write(ai_brief.get("summary", "No summary available."))

risk_col, opportunity_col = st.columns(2)
with risk_col:
    st.subheader("Risks")
    for risk in ai_brief.get("risks", []):
        st.markdown(f"- {risk}")
with opportunity_col:
    st.subheader("Opportunities")
    for opportunity in ai_brief.get("opportunities", []):
        st.markdown(f"- {opportunity}")

st.markdown("---")

st.subheader("Recommended Next Action")
st.write(ai_brief.get("recommendation", "No recommendation available."))

st.subheader("Evidence")
evidence_items = ai_brief.get("evidence") or build_evidence(customer_profile)
for item in evidence_items:
    st.markdown(f"- {item}")

st.markdown("---")

st.subheader("Customer Health")
health_col, reason_col = st.columns([1, 2])
with health_col:
    _render_urgency_badge(urgency)
with reason_col:
    st.caption("Reasons for score")
    for reason in health.get("contributors", []):
        st.write(reason)

st.markdown("---")

st.subheader("Timeline")
_render_timeline(customer_profile.get("timeline", []))

st.markdown("---")

with st.expander("Expandable Raw Data"):
    raw_data_col1, raw_data_col2, raw_data_col3, raw_data_col4, raw_data_col5 = st.columns(5)
    with raw_data_col1:
        st.subheader("CRM Data")
        st.json(crm)
    with raw_data_col2:
        st.subheader("Emails")
        st.json(customer_profile.get("emails", []))
    with raw_data_col3:
        st.subheader("Support Tickets")
        st.json(customer_profile.get("support_tickets", []))
    with raw_data_col4:
        st.subheader("Slack Notes")
        st.json(customer_profile.get("slack_messages", []))
    with raw_data_col5:
        st.subheader("Usage Statistics")
        st.json(customer_profile.get("usage", {}))
