"""Tests for the Compliance Review Agent."""

from app.agents.compliance_review_agent import run_compliance_review_agent


def test_compliance_review_agent_flags_bad_draft():
    """Compliance Agent should reject awkward sponsor drafts."""

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
        "sponsorship_draft": "Hey there devs, let's straight to it with Clerk.",
        "sponsor_research": {
            "sponsor_summary": "Clerk provides authentication.",
            "product_features": [],
            "offer_details": [],
            "required_mentions": [],
            "forbidden_claims": [],
            "verified_facts": [],
            "uncertain_points": [],
            "source_snippets": [],
            "source_links": [],
            "research_gaps": [],
        },
        "creator_style_profile": {
            "tone": "conversational and direct",
            "pacing": "fast and punchy",
            "humor_level": "low",
            "cta_style": "soft recommendation",
            "transition_style": "explicit sponsor segue",
            "vocabulary_patterns": [],
            "do_not_mimic": [],
        },
    }

    result = run_compliance_review_agent(state)

    assert "compliance_report" in result
    assert result["compliance_report"]["approved"] is False
    assert result["compliance_report"]["tone_mismatches"]
    assert result["logs"]
    assert result["tool_traces"]
