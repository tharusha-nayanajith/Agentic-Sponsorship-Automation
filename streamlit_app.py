"""Streamlit demo UI for the Creator Sponsorship Segment MAS."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import streamlit as st

from app.graph.state import MASState
from app.graph.workflow import run_research_workflow


UPLOAD_DIR = Path(".streamlit_uploads")


def main() -> None:
    """Render the demo UI and run the workflow from form inputs."""

    st.set_page_config(
        page_title="Agentic Sponsorship Automation",
        page_icon=":material/auto_awesome:",
        layout="wide",
    )
    st.title("Agentic Sponsorship Automation")
    st.caption(
        "Demo UI for the CTSE multi-agent sponsorship segment pipeline."
    )

    with st.sidebar:
        st.subheader("Workflow")
        st.markdown(
            "\n".join(
                [
                    "1. Research Agent",
                    "2. Creator Style Agent",
                    "3. Sponsorship Writer Agent",
                    "4. Compliance Review Agent",
                ]
            )
        )
        st.divider()
        st.write("Use this page to run a full end-to-end demo for the viva.")

    with st.form("mas_demo_form"):
        col1, col2 = st.columns(2)
        with col1:
            sponsor_name = st.text_input("Sponsor Name", value="Clerk")
            campaign_topic = st.text_input(
                "Campaign Topic",
                value="authentication developer platform",
            )
            product_name = st.text_input("Product Name", value="")
            target_audience = st.text_input(
                "Target Audience",
                value="general developer audience",
            )

        with col2:
            tone_goal = st.text_input(
                "Tone Goal",
                value="creator-style sponsorship segment",
            )
            website_urls_text = st.text_area(
                "Website URLs",
                value="https://clerk.com",
                help="One URL per line.",
                height=120,
            )
            talking_points_text = st.text_area(
                "Required Talking Points",
                value="",
                help="Optional. One talking point per line.",
                height=120,
            )

        creator_samples_text = st.text_area(
            "Creator Sample Transcript",
            value=(
                "I was excited to stop talking about Anthropic. I really was. "
                "But they dropped something new. This is actually a really "
                "exciting product launch for me because designing good user "
                "interfaces with these models is possible, but it takes a lot "
                "of effort. We're going to do a quick break for today's sponsor. "
                "Let's get straight to it. I think this is cool and useful."
            ),
            height=180,
        )

        uploaded_pdfs = st.file_uploader(
            "Sponsor Brief PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            help="Optional. Upload one or more sponsor brief PDFs.",
        )

        submitted = st.form_submit_button("Run Workflow", use_container_width=True)

    if not submitted:
        return

    pdf_paths = _persist_uploaded_pdfs(uploaded_pdfs)
    initial_state = _build_initial_state(
        sponsor_name=sponsor_name,
        campaign_topic=campaign_topic,
        product_name=product_name,
        target_audience=target_audience,
        tone_goal=tone_goal,
        website_urls_text=website_urls_text,
        talking_points_text=talking_points_text,
        creator_samples_text=creator_samples_text,
        pdf_paths=pdf_paths,
    )

    with st.spinner("Running MAS workflow..."):
        final_state = run_research_workflow(initial_state)

    _render_results(final_state)


def _build_initial_state(
    sponsor_name: str,
    campaign_topic: str,
    product_name: str,
    target_audience: str,
    tone_goal: str,
    website_urls_text: str,
    talking_points_text: str,
    creator_samples_text: str,
    pdf_paths: list[str],
) -> MASState:
    """Build workflow state from UI form inputs."""

    return {
        "sponsor_name": sponsor_name.strip(),
        "campaign_topic": campaign_topic.strip(),
        "product_name": product_name.strip(),
        "target_audience": target_audience.strip(),
        "tone_goal": tone_goal.strip(),
        "pdf_paths": pdf_paths,
        "website_urls": _split_lines(website_urls_text),
        "creator_samples": [creator_samples_text.strip()] if creator_samples_text.strip() else [],
        "required_talking_points": _split_lines(talking_points_text),
        "logs": [],
    }


def _split_lines(text: str) -> list[str]:
    """Split textarea text into non-empty trimmed lines."""

    return [line.strip() for line in text.splitlines() if line.strip()]


def _persist_uploaded_pdfs(uploaded_pdfs: list | None) -> list[str]:
    """Persist uploaded PDFs to a temporary workspace directory."""

    if not uploaded_pdfs:
        return []

    UPLOAD_DIR.mkdir(exist_ok=True)
    saved_paths: list[str] = []
    for uploaded_file in uploaded_pdfs:
        safe_name = f"{uuid4().hex}_{uploaded_file.name}"
        target = UPLOAD_DIR / safe_name
        target.write_bytes(uploaded_file.getbuffer())
        saved_paths.append(str(target.resolve()))
    return saved_paths


def _render_results(final_state: MASState) -> None:
    """Render workflow results in a demo-friendly layout."""

    st.success("Workflow completed.")

    top_col1, top_col2, top_col3 = st.columns(3)
    with top_col1:
        st.metric("Logs", len(final_state.get("logs", [])))
    with top_col2:
        report = final_state.get("compliance_report", {})
        st.metric("Approved", "Yes" if report.get("approved") else "No")
    with top_col3:
        st.metric(
            "Sources",
            len(final_state.get("sponsor_research", {}).get("source_links", [])),
        )

    st.subheader("Final Sponsorship Segment")
    st.write(final_state.get("final_sponsorship_segment", ""))

    tabs = st.tabs(
        [
            "Compliance Report",
            "Sponsorship Draft",
            "Research",
            "Creator Style",
            "Logs",
            "Raw JSON",
        ]
    )

    with tabs[0]:
        st.json(final_state.get("compliance_report", {}))

    with tabs[1]:
        st.write(final_state.get("sponsorship_draft", ""))

    with tabs[2]:
        st.json(final_state.get("sponsor_research", {}))

    with tabs[3]:
        st.json(final_state.get("creator_style_profile", {}))

    with tabs[4]:
        st.json(final_state.get("logs", []))

    with tabs[5]:
        st.code(json.dumps(final_state, indent=2), language="json")


if __name__ == "__main__":
    main()
