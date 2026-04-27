"""LangGraph workflow for the Creator Sponsorship Segment MAS."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.compliance_review_agent import run_compliance_review_agent
from app.agents.creator_style_agent import run_creator_style_agent
from app.agents.research_agent import run_research_agent
from app.agents.sponsorship_writer_agent import run_sponsorship_writer_agent
from app.graph.state import MASState

MAX_REVISIONS = 1


def build_workflow():
    """Build and compile the LangGraph workflow."""

    graph = StateGraph(MASState)
    graph.add_node("research_agent", run_research_agent)
    graph.add_node("creator_style_agent", run_creator_style_agent)
    graph.add_node("sponsorship_writer_agent", run_sponsorship_writer_agent)
    graph.add_node("compliance_review_agent", run_compliance_review_agent)

    graph.add_edge(START, "research_agent")
    graph.add_edge("research_agent", "creator_style_agent")
    graph.add_edge("creator_style_agent", "sponsorship_writer_agent")
    graph.add_edge("sponsorship_writer_agent", "compliance_review_agent")
    graph.add_conditional_edges(
        "compliance_review_agent",
        _route_after_compliance,
        {
            "rewrite": "sponsorship_writer_agent",
            "end": END,
        },
    )

    return graph.compile()


def run_langgraph_workflow(initial_state: MASState) -> MASState:
    """Execute the compiled LangGraph workflow."""

    app = build_workflow()
    return app.invoke(initial_state)


def _route_after_compliance(state: MASState) -> str:
    """Route back to the writer once if compliance fails."""

    report = state.get("compliance_report", {})
    if report.get("approved"):
        return "end"

    if state.get("revision_count", 0) <= MAX_REVISIONS:
        return "rewrite"

    return "end"
