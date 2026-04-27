"""Tests for the Creator Style Agent."""

from app.agents.creator_style_agent import run_creator_style_agent


def test_creator_style_agent_generates_profile():
    """Creator Style Agent should derive a structured style profile."""

    state = {
        "sponsor_name": "Clerk",
        "campaign_topic": "authentication",
        "product_name": "",
        "target_audience": "developers",
        "tone_goal": "creator-style sponsorship segment",
        "pdf_paths": [],
        "website_urls": [],
        "creator_samples": [
            "We're going to do a quick break for today's sponsor. "
            "Let's get straight to it. I think this is cool and useful."
        ],
        "required_talking_points": [],
        "revision_count": 0,
        "logs": [],
        "tool_traces": [],
    }

    result = run_creator_style_agent(state)

    assert "creator_style_profile" in result
    profile = result["creator_style_profile"]
    assert profile["tone"]
    assert profile["transition_style"]
    assert isinstance(profile["vocabulary_patterns"], list)
    assert result["logs"]
    assert result["tool_traces"]
