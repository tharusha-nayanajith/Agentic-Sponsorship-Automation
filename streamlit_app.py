"""Streamlit demo UI for the Creator Sponsorship Segment MAS."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import streamlit as st

from app.agents.compliance_review_agent import run_compliance_review_agent
from app.agents.creator_style_agent import run_creator_style_agent
from app.agents.research_agent import run_research_agent
from app.agents.sponsorship_writer_agent import run_sponsorship_writer_agent
from app.graph.state import MASState


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

    final_state = _run_demo_workflow(initial_state)

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
        "tool_traces": [],
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


def _run_demo_workflow(initial_state: MASState) -> MASState:
    """Run the workflow step by step with visible Streamlit progress."""

    status = st.status("Running workflow...", expanded=True)
    current_state = initial_state

    stages = [
        ("Research Agent", run_research_agent),
        ("Creator Style Agent", run_creator_style_agent),
        ("Sponsorship Writer Agent", run_sponsorship_writer_agent),
        ("Compliance Review Agent", run_compliance_review_agent),
    ]

    for label, runner in stages:
        status.write(f"Running {label}...")
        current_state = runner(current_state)
        status.write(f"Completed {label}.")

    status.update(label="Workflow complete", state="complete", expanded=False)
    return current_state


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
            "Execution Trace",
            "Compliance Report",
            "Sponsorship Draft",
            "Research",
            "Creator Style",
            "Logs",
            "Raw JSON",
        ]
    )

    with tabs[0]:
        _render_tool_trace(final_state.get("tool_traces", []))

    with tabs[1]:
        st.json(final_state.get("compliance_report", {}))

    with tabs[2]:
        st.write(final_state.get("sponsorship_draft", ""))

    with tabs[3]:
        st.json(final_state.get("sponsor_research", {}))

    with tabs[4]:
        st.json(final_state.get("creator_style_profile", {}))

    with tabs[5]:
        st.json(final_state.get("logs", []))

    with tabs[6]:
        st.code(json.dumps(final_state, indent=2), language="json")


def _render_tool_trace(tool_traces: list[dict]) -> None:
    """Render tool traces in an agent-tool style presentation."""

    if not tool_traces:
        st.info("No tool traces captured.")
        return

    for index, trace in enumerate(tool_traces, start=1):
        title = (
            f"{index}. {trace['agent_name']} -> {trace['tool_name']} "
            f"[{trace['status']}]"
        )
        with st.expander(title, expanded=index <= 2):
            st.write(f"**Step:** {trace['step']}")
            st.write(f"**Input Summary:** {trace['input_summary']}")
            st.write(f"**Output Summary:** {trace['output_summary']}")


if __name__ == "__main__":
    main()
