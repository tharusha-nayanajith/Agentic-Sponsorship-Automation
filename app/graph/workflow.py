"""Workflow helpers for running the current MAS pipeline."""

from app.graph.state import MASState
from app.graph.langgraph_workflow import run_langgraph_workflow


def run_research_workflow(initial_state: MASState) -> MASState:
    """Run the MAS workflow through LangGraph."""

    return run_langgraph_workflow(initial_state)
