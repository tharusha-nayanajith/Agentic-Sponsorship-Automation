"""Tooling for drafting creator-style sponsorship segments."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SponsorshipSegmentWriterInput(BaseModel):
    """Inputs required to generate a sponsorship segment draft."""

    sponsor_name: str = Field(..., description="Sponsor brand name.")
    campaign_topic: str = Field(..., description="Campaign or product topic.")
    target_audience: str = Field(..., description="Target audience for the segment.")
    tone_goal: str = Field(..., description="Desired tone for the generated segment.")
    sponsor_summary: str = Field(..., description="Compact sponsor summary.")
    product_features: list[str] = Field(
        default_factory=list,
        description="Structured sponsor/product feature highlights.",
    )
    offer_details: list[str] = Field(
        default_factory=list,
        description="Offer details such as discounts, trials, or links.",
    )
    required_mentions: list[str] = Field(
        default_factory=list,
        description="Required sponsor talking points from briefs or research.",
    )
    forbidden_claims: list[str] = Field(
        default_factory=list,
        description="Claims or phrasings the final segment should avoid.",
    )
    tone: str = Field(default="conversational and direct")
    pacing: str = Field(default="moderate with clear transitions")
    humor_level: str = Field(default="low")
    cta_style: str = Field(default="soft recommendation")
    transition_style: str = Field(default="blended conversational transition")
    vocabulary_patterns: list[str] = Field(default_factory=list)
    do_not_mimic: list[str] = Field(default_factory=list)


class SponsorshipSegmentWriterOutput(BaseModel):
    """Structured result returned by the sponsorship segment writer tool."""

    sponsorship_segment: str
    opening_hook: str
    talking_points_used: list[str]
    avoided_claims: list[str]
    success: bool
    error_message: str | None = None


def write_sponsorship_segment_tool(
    input_data: SponsorshipSegmentWriterInput,
) -> SponsorshipSegmentWriterOutput:
    """Generate a first-pass sponsorship segment from structured inputs."""

    talking_points = _select_talking_points(
        required_mentions=input_data.required_mentions,
        product_features=input_data.product_features,
        sponsor_summary=input_data.sponsor_summary,
    )
    opening_hook = _build_opening_hook(
        sponsor_name=input_data.sponsor_name,
        transition_style=input_data.transition_style,
        vocabulary_patterns=input_data.vocabulary_patterns,
    )
    body = _build_body(
        sponsor_name=input_data.sponsor_name,
        target_audience=input_data.target_audience,
        tone=input_data.tone,
        pacing=input_data.pacing,
        humor_level=input_data.humor_level,
        talking_points=talking_points,
        sponsor_summary=input_data.sponsor_summary,
    )
    cta = _build_cta(
        sponsor_name=input_data.sponsor_name,
        cta_style=input_data.cta_style,
        offer_details=input_data.offer_details,
    )
    return_transition = _build_return_transition(
        vocabulary_patterns=input_data.vocabulary_patterns
    )

    segment_parts = [opening_hook, body, cta, return_transition]
    sponsorship_segment = "\n\n".join(part for part in segment_parts if part).strip()

    avoided_claims = [
        claim
        for claim in input_data.forbidden_claims
        if claim and claim.lower() not in sponsorship_segment.lower()
    ]

    return SponsorshipSegmentWriterOutput(
        sponsorship_segment=sponsorship_segment,
        opening_hook=opening_hook,
        talking_points_used=talking_points,
        avoided_claims=avoided_claims,
        success=bool(sponsorship_segment),
        error_message=None if sponsorship_segment else "Failed to generate segment.",
    )


def _select_talking_points(
    required_mentions: list[str],
    product_features: list[str],
    sponsor_summary: str,
) -> list[str]:
    """Pick a compact set of points for the first draft."""

    points: list[str] = []
    points.extend(required_mentions[:3])
    if len(points) < 3:
        points.extend(feature for feature in product_features[:5] if feature not in points)
    if not points and sponsor_summary:
        points.append(sponsor_summary)
    return points[:3]


def _build_opening_hook(
    sponsor_name: str,
    transition_style: str,
    vocabulary_patterns: list[str],
) -> str:
    """Create the sponsor segue line."""

    if transition_style == "explicit sponsor segue":
        return (
            f"Quick break for today's sponsor, {sponsor_name}, because this one is"
            " actually relevant to what we're talking about."
        )
    if "let's" in vocabulary_patterns:
        return f"Let's do a quick sponsor break, because {sponsor_name} fits this topic really well."
    return f"Before we keep going, I want to quickly shout out {sponsor_name}."


def _build_body(
    sponsor_name: str,
    target_audience: str,
    tone: str,
    pacing: str,
    humor_level: str,
    talking_points: list[str],
    sponsor_summary: str,
) -> str:
    """Create the main explanatory body of the sponsorship segment."""

    intro = (
        f"If you're in that {target_audience} bucket, {sponsor_name} is worth a look. "
        f"The short version is this: {sponsor_summary}"
    )

    point_lines = []
    for point in talking_points:
        point_lines.append(f"- {point}")

    style_line = (
        f"The vibe here should feel {tone}, with {pacing} delivery"
        f" and {humor_level} humor."
    )

    lines = [intro]
    if point_lines:
        lines.append("A few things that stand out:")
        lines.extend(point_lines)
    lines.append(style_line)
    return "\n".join(lines)


def _build_cta(
    sponsor_name: str,
    cta_style: str,
    offer_details: list[str],
) -> str:
    """Build the call to action block."""

    if offer_details:
        offer_line = f"Offer details: {offer_details[0]}"
    else:
        offer_line = f"If {sponsor_name} sounds useful, check them out from the link below."

    if cta_style == "direct and action-oriented":
        return f"{offer_line} If you've been meaning to fix this problem properly, now's a good time to do it."
    if cta_style == "community-oriented":
        return f"{offer_line} If you end up trying it, I'd be curious what you think."
    return offer_line


def _build_return_transition(vocabulary_patterns: list[str]) -> str:
    """Return the script back to the main video content."""

    if "straight to it" in vocabulary_patterns:
        return "With that out of the way, let's get straight back to it."
    return "Now, back to the main topic."
