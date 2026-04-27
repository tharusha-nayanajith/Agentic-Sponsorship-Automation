"""Tooling for reviewing sponsorship segment drafts."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field


class ComplianceReviewInput(BaseModel):
    """Inputs required to review a sponsorship segment draft."""

    sponsor_name: str = Field(..., description="Sponsor brand name.")
    sponsorship_draft: str = Field(..., description="Draft segment to review.")
    required_mentions: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)
    tone: str = Field(default="conversational and direct")
    transition_style: str = Field(default="blended conversational transition")
    do_not_mimic: list[str] = Field(default_factory=list)


class ComplianceReviewOutput(BaseModel):
    """Structured result returned by the compliance review tool."""

    approved: bool
    missing_requirements: list[str]
    risky_claims: list[str]
    tone_mismatches: list[str]
    disclosure_issues: list[str]
    revision_notes: list[str]
    cleaned_segment: str
    success: bool
    error_message: str | None = None


def review_sponsorship_segment_tool(
    input_data: ComplianceReviewInput,
) -> ComplianceReviewOutput:
    """Review a sponsorship segment for requirement, tone, and disclosure issues."""

    draft = input_data.sponsorship_draft.strip()
    if not draft:
        return ComplianceReviewOutput(
            approved=False,
            missing_requirements=[],
            risky_claims=[],
            tone_mismatches=[],
            disclosure_issues=["Draft is empty."],
            revision_notes=["Generate a sponsorship draft before running review."],
            cleaned_segment="",
            success=False,
            error_message="No sponsorship draft was provided.",
        )

    cleaned_segment = _clean_segment(draft)
    lowered = cleaned_segment.lower()

    missing_requirements = [
        requirement
        for requirement in input_data.required_mentions
        if requirement and not _loosely_present(requirement, lowered)
    ]
    risky_claims = [
        claim
        for claim in input_data.forbidden_claims
        if claim and claim.lower() in lowered
    ]
    tone_mismatches = _detect_tone_mismatches(
        cleaned_segment=cleaned_segment,
        expected_tone=input_data.tone,
        transition_style=input_data.transition_style,
        do_not_mimic=input_data.do_not_mimic,
    )
    disclosure_issues = _detect_disclosure_issues(
        sponsor_name=input_data.sponsor_name,
        cleaned_segment=cleaned_segment,
    )
    revision_notes = _build_revision_notes(
        missing_requirements=missing_requirements,
        risky_claims=risky_claims,
        tone_mismatches=tone_mismatches,
        disclosure_issues=disclosure_issues,
    )

    approved = not any(
        [missing_requirements, risky_claims, tone_mismatches, disclosure_issues]
    )

    return ComplianceReviewOutput(
        approved=approved,
        missing_requirements=missing_requirements,
        risky_claims=risky_claims,
        tone_mismatches=tone_mismatches,
        disclosure_issues=disclosure_issues,
        revision_notes=revision_notes,
        cleaned_segment=cleaned_segment,
        success=True,
        error_message=None,
    )


def _clean_segment(text: str) -> str:
    """Apply lightweight cleanup to make the segment more presentable."""

    cleaned = re.sub(r"\s+\n", "\n", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def _loosely_present(requirement: str, lowered_text: str) -> bool:
    """Check whether a requirement is loosely represented in the draft."""

    words = re.findall(r"[a-zA-Z0-9]{4,}", requirement.lower())
    if not words:
        return requirement.lower() in lowered_text
    matched_words = sum(1 for word in words if word in lowered_text)
    return matched_words >= max(1, min(2, len(words)))


def _detect_tone_mismatches(
    cleaned_segment: str,
    expected_tone: str,
    transition_style: str,
    do_not_mimic: list[str],
) -> list[str]:
    """Flag obvious tone mismatches and style issues."""

    mismatches: list[str] = []
    lowered = cleaned_segment.lower()

    if "conversational" in expected_tone and len(cleaned_segment.splitlines()) <= 1:
        mismatches.append("Draft feels too compressed to sound conversational.")
    if transition_style == "explicit sponsor segue" and "sponsor" not in lowered:
        mismatches.append("Draft does not clearly signal the sponsor transition.")
    if any(
        phrase.lower() in lowered
        for phrase in ("the vibe here should feel", "short version is this")
    ):
        mismatches.append("Draft still contains meta-writing language instead of natural script wording.")
    if any(
        phrase in lowered
        for phrase in ("hey there devs", "no-brainer", "actually, i think", "let's straight to it")
    ):
        mismatches.append("Draft still contains generic or awkward generated phrasing.")
    if any("profanity" in item.lower() for item in do_not_mimic) and any(
        token in lowered for token in ("fuck", "shit", "[ __ ]")
    ):
        mismatches.append("Draft copied profanity-like phrasing that should be avoided.")

    return mismatches


def _detect_disclosure_issues(sponsor_name: str, cleaned_segment: str) -> list[str]:
    """Ensure the segment clearly identifies itself as sponsored content."""

    lowered = cleaned_segment.lower()
    sponsor_markers = (
        "sponsor",
        "sponsored",
        "today's sponsor",
        sponsor_name.lower(),
    )
    if any(marker in lowered for marker in sponsor_markers):
        return []
    return ["Draft does not clearly disclose the sponsorship segment."]


def _build_revision_notes(
    missing_requirements: list[str],
    risky_claims: list[str],
    tone_mismatches: list[str],
    disclosure_issues: list[str],
) -> list[str]:
    """Turn validation findings into concrete revision notes."""

    notes: list[str] = []
    if missing_requirements:
        notes.append("Add the missing sponsor talking points.")
    if risky_claims:
        notes.append("Remove or rewrite disallowed claims from the segment.")
    if tone_mismatches:
        notes.append("Rewrite the draft so it sounds like natural spoken creator copy.")
    if disclosure_issues:
        notes.append("Add an explicit sponsor disclosure near the start of the segment.")
    if not notes:
        notes.append("Draft is ready for the next stage.")
    return notes
