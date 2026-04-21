"""Tooling for extracting a creator style profile from transcript samples."""

from __future__ import annotations

from collections import Counter
import re

from pydantic import BaseModel, Field


class CreatorStyleAnalysisInput(BaseModel):
    """Inputs required to analyze creator transcript samples."""

    creator_samples: list[str] = Field(
        ...,
        min_length=1,
        description="Transcript samples or transcript text snippets from the creator.",
    )
    tone_goal: str = Field(
        default="creator-style sponsorship segment",
        description="High-level tone target for the final sponsored segment.",
    )


class CreatorStyleAnalysisOutput(BaseModel):
    """Structured style profile extracted from creator samples."""

    tone: str
    pacing: str
    humor_level: str
    cta_style: str
    transition_style: str
    vocabulary_patterns: list[str]
    do_not_mimic: list[str]
    supporting_observations: list[str]
    success: bool
    error_message: str | None = None


def analyze_creator_style_tool(
    input_data: CreatorStyleAnalysisInput,
) -> CreatorStyleAnalysisOutput:
    """Analyze transcript samples and return a heuristic creator style profile."""

    combined_text = "\n\n".join(sample.strip() for sample in input_data.creator_samples).strip()
    if not combined_text:
        return CreatorStyleAnalysisOutput(
            tone="unknown",
            pacing="unknown",
            humor_level="unknown",
            cta_style="unknown",
            transition_style="unknown",
            vocabulary_patterns=[],
            do_not_mimic=[],
            supporting_observations=[],
            success=False,
            error_message="No creator sample text was provided.",
        )

    sentences = _split_sentences(combined_text)
    tone = _infer_tone(combined_text)
    pacing = _infer_pacing(sentences)
    humor_level = _infer_humor_level(combined_text)
    cta_style = _infer_cta_style(combined_text)
    transition_style = _infer_transition_style(combined_text)
    vocabulary_patterns = _extract_vocabulary_patterns(combined_text)
    do_not_mimic = _extract_do_not_mimic(combined_text)
    observations = _build_supporting_observations(
        combined_text=combined_text,
        tone=tone,
        pacing=pacing,
        humor_level=humor_level,
        cta_style=cta_style,
        transition_style=transition_style,
    )

    return CreatorStyleAnalysisOutput(
        tone=tone,
        pacing=pacing,
        humor_level=humor_level,
        cta_style=cta_style,
        transition_style=transition_style,
        vocabulary_patterns=vocabulary_patterns,
        do_not_mimic=do_not_mimic,
        supporting_observations=observations,
        success=True,
        error_message=None,
    )


def _split_sentences(text: str) -> list[str]:
    """Split transcript text into rough sentence-like units."""

    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _infer_tone(text: str) -> str:
    """Infer the creator's dominant tone from lexical cues."""

    lowered = text.lower()
    energetic_markers = ("excited", "awesome", "amazing", "crazy", "cool", "hyped")
    analytical_markers = ("because", "actually", "historically", "reason", "problem")
    conversational_markers = ("you guys", "i want", "let's", "we're going to", "i think")

    energetic_score = sum(lowered.count(marker) for marker in energetic_markers)
    analytical_score = sum(lowered.count(marker) for marker in analytical_markers)
    conversational_score = sum(lowered.count(marker) for marker in conversational_markers)

    if energetic_score >= analytical_score and energetic_score >= conversational_score:
        return "energetic and opinionated"
    if analytical_score >= conversational_score:
        return "analytical and explanatory"
    return "conversational and direct"


def _infer_pacing(sentences: list[str]) -> str:
    """Infer pacing from sentence lengths and transcript cadence."""

    if not sentences:
        return "unknown"

    average_words = sum(len(sentence.split()) for sentence in sentences) / len(sentences)
    if average_words <= 10:
        return "fast and punchy"
    if average_words <= 20:
        return "moderate with clear transitions"
    return "long-form and exploratory"


def _infer_humor_level(text: str) -> str:
    """Estimate humor level from informal emphasis and joke-like markers."""

    lowered = text.lower()
    humor_markers = (
        "cringe",
        "funny",
        "joking",
        "laugh",
        "what the",
        "god damn",
        "brutal",
        "hilarious",
    )
    marker_count = sum(lowered.count(marker) for marker in humor_markers)
    if marker_count >= 4:
        return "high"
    if marker_count >= 2:
        return "medium"
    return "low"


def _infer_cta_style(text: str) -> str:
    """Infer how the creator usually prompts the audience to act."""

    lowered = text.lower()
    if any(marker in lowered for marker in ("check it out", "give it a try", "use my link", "go to ")):
        return "direct and action-oriented"
    if any(marker in lowered for marker in ("let me know", "tell me what you think", "curious what you think")):
        return "community-oriented"
    return "soft recommendation"


def _infer_transition_style(text: str) -> str:
    """Infer how the creator moves between main content and sponsor content."""

    lowered = text.lower()
    if any(marker in lowered for marker in ("quick break for today's sponsor", "today's sponsor", "sponsor")):
        return "explicit sponsor segue"
    if any(marker in lowered for marker in ("let's get back to it", "straight to it", "now back")):
        return "clear break-and-return structure"
    return "blended conversational transition"


def _extract_vocabulary_patterns(text: str, limit: int = 8) -> list[str]:
    """Extract repeated creator phrases and keywords worth mirroring lightly."""

    lowered = text.lower()
    phrases = (
        "i think",
        "you guys",
        "let's",
        "actually",
        "really",
        "very excited",
        "straight to it",
        "for sure",
        "i love",
        "i like",
    )
    found_phrases = [phrase for phrase in phrases if phrase in lowered]
    if found_phrases:
        return found_phrases[:limit]

    tokens = re.findall(r"[a-zA-Z']{4,}", lowered)
    stop_words = {
        "that",
        "this",
        "with",
        "have",
        "from",
        "they",
        "their",
        "would",
        "there",
        "because",
        "about",
    }
    counts = Counter(token for token in tokens if token not in stop_words)
    return [word for word, _ in counts.most_common(limit)]


def _extract_do_not_mimic(text: str) -> list[str]:
    """Capture risky elements we should not reproduce too literally."""

    lowered = text.lower()
    warnings: list[str] = []
    if "[ __ ]" in text or "fuck" in lowered or "shit" in lowered:
        warnings.append("Avoid copying profanity or censored swear phrasing directly.")
    if "harsh" in lowered or "crash out" in lowered:
        warnings.append("Avoid over-copying combative or overly negative commentary.")
    if "sponsor" in lowered:
        warnings.append("Do not mimic sponsor copy word-for-word from samples.")
    return warnings


def _build_supporting_observations(
    combined_text: str,
    tone: str,
    pacing: str,
    humor_level: str,
    cta_style: str,
    transition_style: str,
) -> list[str]:
    """Produce concise evidence notes for the style profile."""

    exclamation_count = combined_text.count("!")
    first_person_count = len(re.findall(r"\b(i|i'm|i've|i'll)\b", combined_text.lower()))
    return [
        f"Detected tone: {tone}.",
        f"Detected pacing: {pacing}.",
        f"Humor level appears {humor_level}.",
        f"CTA style appears {cta_style}.",
        f"Transition style appears {transition_style}.",
        f"Transcript includes {exclamation_count} exclamation marks and {first_person_count} first-person references.",
    ]
