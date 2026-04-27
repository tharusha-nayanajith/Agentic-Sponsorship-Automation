"""Tests for the Research Agent."""

from app.agents.research_agent import run_research_agent


def test_research_agent_collects_web_research(monkeypatch):
    """Research Agent should write structured sponsor research into state."""

    class DummyWebOutput:
        success = True
        verified_facts = [
            "Clerk provides authentication and user management for developers."
        ]
        summaries = ["Clerk helps developers add auth quickly."]
        source_links = ["https://clerk.com"]
        source_snippets = []
        error_message = None

    def fake_web_tool(_input_data):
        return DummyWebOutput()

    monkeypatch.setattr(
        "app.agents.research_agent.web_brand_research_tool",
        fake_web_tool,
    )

    state = {
        "sponsor_name": "Clerk",
        "campaign_topic": "authentication",
        "product_name": "",
        "target_audience": "developers",
        "tone_goal": "creator-style sponsorship segment",
        "pdf_paths": [],
        "website_urls": ["https://clerk.com"],
        "creator_samples": [],
        "required_talking_points": [],
        "revision_count": 0,
        "logs": [],
        "tool_traces": [],
    }

    result = run_research_agent(state)

    assert "sponsor_research" in result
    assert result["sponsor_research"]["verified_facts"]
    assert result["sponsor_research"]["source_links"] == ["https://clerk.com"]
    assert result["logs"]
    assert result["tool_traces"]
