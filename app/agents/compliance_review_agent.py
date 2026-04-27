"""Compliance and Review Agent node for validating sponsorship drafts."""

from __future__ import annotations

from app.graph.state import AgentLog, ComplianceReport, MASState, ToolTrace
from app.tools.compliance_review_tool import (
    ComplianceReviewInput,
    review_sponsorship_segment_tool,
)


COMPLIANCE_REVIEW_AGENT_NAME = "ComplianceReviewAgent"


def run_compliance_review_agent(state: MASState) -> MASState:
    """Review the sponsorship draft and write final approval state."""

    logs = list(state.get("logs", []))
    tool_traces = list(state.get("tool_traces", []))
    draft = state.get("sponsorship_draft", "")

    logs.append(
        _log(
            step="start",
            status="started",
            message="Compliance Review Agent started validating the draft.",
        )
    )

    if not draft:
        logs.append(
            _log(
                step="skip",
                status="skipped",
                message="No sponsorship draft was available, so review was skipped.",
            )
        )
        updated_state = dict(state)
        updated_state["logs"] = logs
        updated_state["tool_traces"] = tool_traces
        return updated_state

    sponsor_research = state.get("sponsor_research", {})
    creator_style_profile = state.get("creator_style_profile", {})
    result = review_sponsorship_segment_tool(
        ComplianceReviewInput(
            sponsor_name=state["sponsor_name"],
            sponsorship_draft=draft,
            required_mentions=sponsor_research.get("required_mentions", []),
            forbidden_claims=sponsor_research.get("forbidden_claims", []),
            tone=creator_style_profile.get("tone", "conversational and direct"),
            transition_style=creator_style_profile.get(
                "transition_style",
                "blended conversational transition",
            ),
            do_not_mimic=creator_style_profile.get("do_not_mimic", []),
        )
    )
    tool_traces.append(
        _tool_trace(
            step="review",
            tool_name="review_sponsorship_segment_tool",
            status="success" if result.success else "failed",
            input_summary=(
                f"draft_chars={len(draft)}; required_mentions={len(sponsor_research.get('required_mentions', []))}"
            ),
            output_summary=(
                f"approved={result.approved}; "
                f"tone_mismatches={len(result.tone_mismatches)}; "
                f"disclosure_issues={len(result.disclosure_issues)}"
                if result.success
                else (result.error_message or "Compliance review failed.")
            ),
        )
    )

    logs.append(
        _log(
            step="review",
            tool_used="review_sponsorship_segment_tool",
            status="success" if result.success else "failed",
            message=(
                "Compliance review completed successfully."
                if result.success
                else "Compliance review failed."
            ),
        )
    )

    updated_state = dict(state)
    updated_state["logs"] = logs
    updated_state["tool_traces"] = tool_traces

    if not result.success:
        logs.append(
            _log(
                step="complete",
                status="completed",
                message="Compliance Review Agent finished without a valid review result.",
            )
        )
        return updated_state

    compliance_report: ComplianceReport = {
        "approved": result.approved,
        "missing_requirements": result.missing_requirements,
        "risky_claims": result.risky_claims,
        "tone_mismatches": result.tone_mismatches,
        "disclosure_issues": result.disclosure_issues,
        "revision_notes": result.revision_notes,
    }

    updated_state["compliance_report"] = compliance_report
    updated_state["final_sponsorship_segment"] = result.cleaned_segment
    if not result.approved:
        updated_state["revision_count"] = state.get("revision_count", 0) + 1

    logs.append(
        _log(
            step="complete",
            status="completed",
            message="Compliance Review Agent finished and wrote final review state.",
        )
    )
    return updated_state


def _log(
    step: str,
    status: str,
    message: str,
    tool_used: str | None = None,
) -> AgentLog:
    """Create a consistent Compliance Review Agent log entry."""

    entry: AgentLog = {
        "agent_name": COMPLIANCE_REVIEW_AGENT_NAME,
        "step": step,
        "status": status,
        "message": message,
    }
    if tool_used:
        entry["tool_used"] = tool_used
    return entry


def _tool_trace(
    step: str,
    tool_name: str,
    status: str,
    input_summary: str,
    output_summary: str,
) -> ToolTrace:
    """Create a consistent Compliance Review Agent tool trace entry."""

    return {
        "agent_name": COMPLIANCE_REVIEW_AGENT_NAME,
        "step": step,
        "tool_name": tool_name,
        "status": status,
        "input_summary": input_summary,
        "output_summary": output_summary,
    }
