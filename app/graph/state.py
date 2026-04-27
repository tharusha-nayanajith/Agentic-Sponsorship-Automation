"""Shared state definitions for the Creator Sponsorship Segment MAS."""

from typing import NotRequired, TypedDict


class SourceSnippet(TypedDict):
    """A short extract tied to a specific source."""

    type: str
    source: str
    snippet: str


class SponsorResearch(TypedDict):
    """Structured sponsor information collected by the Research Agent."""

    sponsor_summary: str
    product_features: list[str]
    offer_details: list[str]
    required_mentions: list[str]
    forbidden_claims: list[str]
    verified_facts: list[str]
    uncertain_points: list[str]
    source_snippets: list[SourceSnippet]
    source_links: list[str]
    research_gaps: list[str]


class CreatorStyleProfile(TypedDict):
    """Stylistic traits extracted from creator transcript samples."""

    tone: str
    pacing: str
    humor_level: str
    cta_style: str
    transition_style: str
    vocabulary_patterns: list[str]
    do_not_mimic: list[str]


class ComplianceReport(TypedDict):
    """Validation results produced by the Compliance Agent."""

    approved: bool
    missing_requirements: list[str]
    risky_claims: list[str]
    tone_mismatches: list[str]
    disclosure_issues: list[str]
    revision_notes: list[str]


class AgentLog(TypedDict):
    """A traceable log entry for agent execution and tool usage."""

    agent_name: str
    step: str
    tool_used: NotRequired[str]
    status: str
    message: str


class ToolTrace(TypedDict):
    """Structured trace entry for a single tool invocation."""

    agent_name: str
    step: str
    tool_name: str
    status: str
    input_summary: str
    output_summary: str


class MASState(TypedDict):
    """Global state passed across the full multi-agent workflow."""

    sponsor_name: str
    campaign_topic: str
    product_name: str
    target_audience: str
    tone_goal: str
    pdf_paths: list[str]
    website_urls: list[str]
    creator_samples: list[str]
    required_talking_points: list[str]
    sponsor_research: NotRequired[SponsorResearch]
    creator_style_profile: NotRequired[CreatorStyleProfile]
    sponsorship_draft: NotRequired[str]
    compliance_report: NotRequired[ComplianceReport]
    final_sponsorship_segment: NotRequired[str]
    logs: list[AgentLog]
    tool_traces: list[ToolTrace]
