"""Creator Style Agent node for building creator voice profiles."""

from __future__ import annotations

from app.graph.state import AgentLog, CreatorStyleProfile, MASState, ToolTrace
from app.tools.creator_style_analysis_tool import (
    CreatorStyleAnalysisInput,
    analyze_creator_style_tool,
)


CREATOR_STYLE_AGENT_NAME = "CreatorStyleAgent"


def run_creator_style_agent(state: MASState) -> MASState:
    """Analyze creator samples and write a structured creator style profile."""

    logs = list(state.get("logs", []))
    tool_traces = list(state.get("tool_traces", []))
    creator_samples = state.get("creator_samples", [])

    logs.append(
        _log(
            step="start",
            status="started",
            message="Creator Style Agent started analyzing creator samples.",
        )
    )

    if not creator_samples:
        logs.append(
            _log(
                step="skip",
                status="skipped",
                message="No creator samples were provided, so style analysis was skipped.",
            )
        )
        updated_state = dict(state)
        updated_state["logs"] = logs
        updated_state["tool_traces"] = tool_traces
        return updated_state

    result = analyze_creator_style_tool(
        CreatorStyleAnalysisInput(
            creator_samples=creator_samples,
            tone_goal=state.get("tone_goal", "creator-style sponsorship segment"),
        )
    )
    tool_traces.append(
        _tool_trace(
            step="style_analysis",
            tool_name="analyze_creator_style_tool",
            status="success" if result.success else "failed",
            input_summary=f"samples={len(creator_samples)}; tone_goal={state.get('tone_goal', '')}",
            output_summary=(
                f"tone={result.tone}; pacing={result.pacing}; cta_style={result.cta_style}"
                if result.success
                else (result.error_message or "Style analysis failed.")
            ),
        )
    )

    logs.append(
        _log(
            step="style_analysis",
            tool_used="analyze_creator_style_tool",
            status="success" if result.success else "failed",
            message=(
                "Creator style analysis completed successfully."
                if result.success
                else "Creator style analysis failed."
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
                message="Creator Style Agent finished without producing a style profile.",
            )
        )
        return updated_state

    creator_style_profile: CreatorStyleProfile = {
        "tone": result.tone,
        "pacing": result.pacing,
        "humor_level": result.humor_level,
        "cta_style": result.cta_style,
        "transition_style": result.transition_style,
        "vocabulary_patterns": result.vocabulary_patterns,
        "do_not_mimic": result.do_not_mimic,
    }
    updated_state["creator_style_profile"] = creator_style_profile

    logs.append(
        _log(
            step="complete",
            status="completed",
            message="Creator Style Agent finished building the creator style profile.",
        )
    )
    return updated_state


def _log(
    step: str,
    status: str,
    message: str,
    tool_used: str | None = None,
) -> AgentLog:
    """Create a consistent Creator Style Agent log entry."""

    entry: AgentLog = {
        "agent_name": CREATOR_STYLE_AGENT_NAME,
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
    """Create a consistent Creator Style Agent tool trace entry."""

    return {
        "agent_name": CREATOR_STYLE_AGENT_NAME,
        "step": step,
        "tool_name": tool_name,
        "status": status,
        "input_summary": input_summary,
        "output_summary": output_summary,
    }
