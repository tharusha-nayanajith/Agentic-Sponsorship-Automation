"""Minimal workflow helpers for running the current MAS pipeline."""

from app.agents.compliance_review_agent import run_compliance_review_agent
from app.agents.creator_style_agent import run_creator_style_agent
from app.agents.research_agent import run_research_agent
from app.agents.sponsorship_writer_agent import run_sponsorship_writer_agent
from app.graph.state import MASState


def run_research_workflow(initial_state: MASState) -> MASState:
    """Run the currently implemented portion of the MAS workflow.

    Right now the workflow includes the Research Agent, Creator Style Agent,
    Sponsorship Writer Agent, and Compliance Review Agent. This wrapper keeps
    the execution entry point stable while the rest of the agents are added.
    """

    state_after_research = run_research_agent(initial_state)
    state_after_style = run_creator_style_agent(state_after_research)
    state_after_draft = run_sponsorship_writer_agent(state_after_style)
    return run_compliance_review_agent(state_after_draft)
