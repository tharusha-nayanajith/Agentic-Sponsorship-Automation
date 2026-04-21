"""Sponsorship Writer Agent node for drafting sponsor segments."""

from __future__ import annotations

from app.graph.state import AgentLog, MASState
from app.tools.sponsorship_segment_writer_tool import (
    SponsorshipSegmentWriterInput,
    write_sponsorship_segment_tool,
)


SPONSORSHIP_WRITER_AGENT_NAME = "SponsorshipWriterAgent"


def run_sponsorship_writer_agent(state: MASState) -> MASState:
    """Generate a sponsorship segment draft from research and creator style."""

    logs = list(state.get("logs", []))
    sponsor_research = state.get("sponsor_research")

    logs.append(
        _log(
            step="start",
            status="started",
            message="Sponsorship Writer Agent started drafting the segment.",
        )
    )

    if not sponsor_research:
        logs.append(
            _log(
                step="skip",
                status="skipped",
                message="No sponsor research was available, so drafting was skipped.",
            )
        )
        updated_state = dict(state)
        updated_state["logs"] = logs
        return updated_state

    style_profile = state.get("creator_style_profile", {})
    result = write_sponsorship_segment_tool(
        SponsorshipSegmentWriterInput(
            sponsor_name=state["sponsor_name"],
            campaign_topic=state["campaign_topic"],
            target_audience=state["target_audience"],
            tone_goal=state["tone_goal"],
            sponsor_summary=sponsor_research["sponsor_summary"],
            product_features=sponsor_research["product_features"],
            offer_details=sponsor_research["offer_details"],
            required_mentions=sponsor_research["required_mentions"],
            forbidden_claims=sponsor_research["forbidden_claims"],
            tone=style_profile.get("tone", "conversational and direct"),
            pacing=style_profile.get("pacing", "moderate with clear transitions"),
            humor_level=style_profile.get("humor_level", "low"),
            cta_style=style_profile.get("cta_style", "soft recommendation"),
            transition_style=style_profile.get(
                "transition_style",
                "blended conversational transition",
            ),
            vocabulary_patterns=style_profile.get("vocabulary_patterns", []),
            do_not_mimic=style_profile.get("do_not_mimic", []),
        )
    )

    logs.append(
        _log(
            step="draft_generation",
            tool_used="write_sponsorship_segment_tool",
            status="success" if result.success else "failed",
            message=(
                "Sponsorship draft generated successfully."
                if result.success
                else "Sponsorship draft generation failed."
            ),
        )
    )

    updated_state = dict(state)
    updated_state["logs"] = logs
    if result.success:
        updated_state["sponsorship_draft"] = result.sponsorship_segment

    logs.append(
        _log(
            step="complete",
            status="completed",
            message="Sponsorship Writer Agent finished processing.",
        )
    )
    return updated_state


def _log(
    step: str,
    status: str,
    message: str,
    tool_used: str | None = None,
) -> AgentLog:
    """Create a consistent Sponsorship Writer Agent log entry."""

    entry: AgentLog = {
        "agent_name": SPONSORSHIP_WRITER_AGENT_NAME,
        "step": step,
        "status": status,
        "message": message,
    }
    if tool_used:
        entry["tool_used"] = tool_used
    return entry
