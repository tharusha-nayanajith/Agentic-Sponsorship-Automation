"""Tests for the Sponsorship Writer Agent."""

from app.agents.sponsorship_writer_agent import run_sponsorship_writer_agent


def test_sponsorship_writer_agent_produces_draft(monkeypatch):
    """Writer Agent should store a non-empty draft in state."""

    class DummyWriterOutput:
        sponsorship_segment = "Quick break for today's sponsor, Clerk. Try it out below."
        opening_hook = "Quick break for today's sponsor, Clerk."
        talking_points_used = ["Clerk provides authentication."]
        avoided_claims = []
        llm_used = False
        success = True
        error_message = None

    def fake_writer_tool(_input_data):
        return DummyWriterOutput()

    monkeypatch.setattr(
        "app.agents.sponsorship_writer_agent.write_sponsorship_segment_tool",
        fake_writer_tool,
    )

    state = {
        "sponsor_name": "Clerk",
        "campaign_topic": "authentication",
        "product_name": "",
        "target_audience": "developers",
        "tone_goal": "creator-style sponsorship segment",
        "pdf_paths": [],
        "website_urls": [],
        "creator_samples": [],
        "required_talking_points": [],
        "revision_count": 0,
        "logs": [],
        "tool_traces": [],
        "sponsor_research": {
            "sponsor_summary": "Clerk provides authentication.",
            "product_features": ["Clerk provides authentication."],
            "offer_details": [],
            "required_mentions": [],
            "forbidden_claims": [],
            "verified_facts": ["Clerk provides authentication."],
            "uncertain_points": [],
            "source_snippets": [],
            "source_links": ["https://clerk.com"],
            "research_gaps": [],
        },
        "creator_style_profile": {
            "tone": "conversational and direct",
            "pacing": "fast and punchy",
            "humor_level": "low",
            "cta_style": "soft recommendation",
            "transition_style": "explicit sponsor segue",
            "vocabulary_patterns": ["let's"],
            "do_not_mimic": [],
        },
    }

    result = run_sponsorship_writer_agent(state)

    assert "sponsorship_draft" in result
    assert "Clerk" in result["sponsorship_draft"]
    assert result["logs"]
    assert result["tool_traces"]
