"""Tooling for drafting creator-style sponsorship segments."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.llm.ollama_client import OllamaClient


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
    llm_used: bool
    success: bool
    error_message: str | None = None


def write_sponsorship_segment_tool(
    input_data: SponsorshipSegmentWriterInput,
) -> SponsorshipSegmentWriterOutput:
    """Generate a sponsorship segment from structured inputs.

    The tool prefers a local Ollama model and falls back to deterministic
    template generation if the LLM is unavailable.
    """

    talking_points = _select_talking_points(
        required_mentions=input_data.required_mentions,
        product_features=input_data.product_features,
        sponsor_summary=input_data.sponsor_summary,
    )
    llm_segment = _generate_with_ollama(input_data=input_data, talking_points=talking_points)
    if llm_segment:
        avoided_claims = [
            claim
            for claim in input_data.forbidden_claims
            if claim and claim.lower() not in llm_segment.lower()
        ]
        return SponsorshipSegmentWriterOutput(
            sponsorship_segment=llm_segment,
            opening_hook=llm_segment.splitlines()[0].strip() if llm_segment.splitlines() else "",
            talking_points_used=talking_points,
            avoided_claims=avoided_claims,
            llm_used=True,
            success=True,
            error_message=None,
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
        llm_used=False,
        success=bool(sponsorship_segment),
        error_message=None if sponsorship_segment else "Failed to generate segment.",
    )


def _generate_with_ollama(
    input_data: SponsorshipSegmentWriterInput,
    talking_points: list[str],
) -> str:
    """Use the local Ollama model to draft a natural sponsorship segment."""

    client = OllamaClient()
    if not client.health_check():
        return ""

    system_prompt = (
        "You write short YouTube sponsorship segments. "
        "Write natural spoken copy, not notes, not bullets, and not meta-instructions. "
        "Keep it concise, conversational, and usable as a spoken ad read. "
        "Do not mention internal writing instructions. "
        "Do not include markdown headings."
    )

    prompt = _build_ollama_prompt(input_data=input_data, talking_points=talking_points)
    try:
        response = client.generate(
            prompt=prompt,
            system=system_prompt,
            options={"temperature": 0.5},
        )
    except Exception:
        return ""

    cleaned = _clean_llm_output(response)
    return cleaned


def _build_ollama_prompt(
    input_data: SponsorshipSegmentWriterInput,
    talking_points: list[str],
) -> str:
    """Build the generation prompt for the local Ollama writer."""

    points_text = "\n".join(f"- {point}" for point in talking_points) or "- Use the sponsor summary."
    offers_text = "\n".join(f"- {item}" for item in input_data.offer_details[:3]) or "- No special offer details provided."
    forbidden_text = "\n".join(f"- {item}" for item in input_data.forbidden_claims[:5]) or "- No forbidden claims provided."
    vocab_text = ", ".join(input_data.vocabulary_patterns[:6]) or "none"
    avoid_text = "\n".join(f"- {item}" for item in input_data.do_not_mimic[:5]) or "- No extra restrictions provided."

    return (
        f"Write a YouTube sponsorship segment for {input_data.sponsor_name}.\n\n"
        f"Campaign topic: {input_data.campaign_topic}\n"
        f"Audience: {input_data.target_audience}\n"
        f"Desired tone: {input_data.tone_goal}\n"
        f"Creator tone profile: {input_data.tone}\n"
        f"Creator pacing: {input_data.pacing}\n"
        f"Humor level: {input_data.humor_level}\n"
        f"CTA style: {input_data.cta_style}\n"
        f"Transition style: {input_data.transition_style}\n"
        f"Vocabulary patterns to lightly echo: {vocab_text}\n\n"
        f"Sponsor summary:\n{input_data.sponsor_summary}\n\n"
        f"Required points to cover:\n{points_text}\n\n"
        f"Offer details:\n{offers_text}\n\n"
        f"Forbidden claims or phrasing:\n{forbidden_text}\n\n"
        f"Do not mimic:\n{avoid_text}\n\n"
        "Requirements:\n"
        "- Start with a clear sponsor transition.\n"
        "- Clearly disclose that it is a sponsor segment.\n"
        "- Make it sound like spoken creator copy.\n"
        "- Avoid bullet points.\n"
        "- Avoid meta-writing phrases like 'the vibe here should feel' or 'the short version is this'.\n"
        "- End with a short CTA and a return to the main topic.\n"
        "- Keep it under 170 words.\n"
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


def _clean_llm_output(text: str) -> str:
    """Remove common LLM formatting noise from generated output."""

    cleaned = text.strip()
    cleaned = cleaned.replace("```", "").strip()
    cleaned = cleaned.replace("Sponsorship Segment:", "").strip()
    return cleaned
