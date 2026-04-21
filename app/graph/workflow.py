"""Minimal workflow helpers for running the current MAS pipeline."""

from app.agents.research_agent import run_research_agent
from app.graph.state import MASState


def run_research_workflow(initial_state: MASState) -> MASState:
    """Run the currently implemented portion of the MAS workflow.

    Right now the workflow contains only the Research Agent. This wrapper keeps
    the execution entry point stable while the rest of the agents are added.
    """

    return run_research_agent(initial_state)
