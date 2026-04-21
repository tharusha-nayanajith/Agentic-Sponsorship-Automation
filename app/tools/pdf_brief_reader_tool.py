"""Schemas and implementation for the sponsor PDF brief reader tool."""

from __future__ import annotations

from pathlib import Path
import re

from pydantic import BaseModel, Field

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - depends on local environment
    PdfReader = None


class PDFBriefReaderInput(BaseModel):
    """Inputs required to extract research data from a sponsor brief PDF."""

    pdf_path: str = Field(..., description="Local path to the sponsor brief PDF.")
    sponsor_name: str = Field(..., description="Name of the sponsor.")
    campaign_topic: str = Field(
        ...,
        description="Campaign or product topic to focus on while extracting details.",
    )
    max_passages: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of relevant passages to return.",
    )


class PDFBriefReaderOutput(BaseModel):
    """Structured result returned by the sponsor PDF brief reader tool."""

    pdf_path: str
    sponsor_name: str
    extracted_text_preview: str
    relevant_passages: list[str]
    required_mentions: list[str]
    forbidden_claims: list[str]
    offer_details: list[str]
    success: bool
    error_message: str | None = None


def read_pdf_brief_tool(input_data: PDFBriefReaderInput) -> PDFBriefReaderOutput:
    """Read a sponsor brief PDF and return campaign-relevant structured data.

    The tool extracts text, ranks relevant passages by topic overlap, and uses
    simple heuristics to identify required mentions, offer details, and risky
    claim restrictions from the document.
    """

    pdf_file = Path(input_data.pdf_path)
    if not pdf_file.exists():
        return PDFBriefReaderOutput(
            pdf_path=input_data.pdf_path,
            sponsor_name=input_data.sponsor_name,
            extracted_text_preview="",
            relevant_passages=[],
            required_mentions=[],
            forbidden_claims=[],
            offer_details=[],
            success=False,
            error_message="PDF file was not found.",
        )

    if pdf_file.suffix.lower() != ".pdf":
        return PDFBriefReaderOutput(
            pdf_path=input_data.pdf_path,
            sponsor_name=input_data.sponsor_name,
            extracted_text_preview="",
            relevant_passages=[],
            required_mentions=[],
            forbidden_claims=[],
            offer_details=[],
            success=False,
            error_message="Provided file is not a PDF.",
        )

    if PdfReader is None:
        return PDFBriefReaderOutput(
            pdf_path=input_data.pdf_path,
            sponsor_name=input_data.sponsor_name,
            extracted_text_preview="",
            relevant_passages=[],
            required_mentions=[],
            forbidden_claims=[],
            offer_details=[],
            success=False,
            error_message=(
                "pypdf is not installed. Install it before using the PDF research tool."
            ),
        )

    try:
        reader = PdfReader(str(pdf_file))
    except Exception as exc:  # pragma: no cover - depends on PDF data
        return PDFBriefReaderOutput(
            pdf_path=input_data.pdf_path,
            sponsor_name=input_data.sponsor_name,
            extracted_text_preview="",
            relevant_passages=[],
            required_mentions=[],
            forbidden_claims=[],
            offer_details=[],
            success=False,
            error_message=f"Failed to open PDF: {exc}",
        )

    page_texts = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            extracted = (page.extract_text() or "").strip()
        except Exception as exc:  # pragma: no cover - depends on PDF data
            extracted = f"[Page {page_number} extraction failed: {exc}]"

        if extracted:
            page_texts.append(f"Page {page_number}\n{extracted}")

    combined_text = "\n\n".join(page_texts).strip()
    if not combined_text:
        return PDFBriefReaderOutput(
            pdf_path=input_data.pdf_path,
            sponsor_name=input_data.sponsor_name,
            extracted_text_preview="",
            relevant_passages=[],
            required_mentions=[],
            forbidden_claims=[],
            offer_details=[],
            success=False,
            error_message="No readable text could be extracted from the PDF.",
        )

    passages = _split_into_passages(combined_text)
    ranked_passages = _rank_passages(
        passages=passages,
        sponsor_name=input_data.sponsor_name,
        campaign_topic=input_data.campaign_topic,
    )
    top_passages = ranked_passages[: input_data.max_passages]

    required_mentions = _extract_required_mentions(passages)
    forbidden_claims = _extract_forbidden_claims(passages)
    offer_details = _extract_offer_details(passages)

    return PDFBriefReaderOutput(
        pdf_path=input_data.pdf_path,
        sponsor_name=input_data.sponsor_name,
        extracted_text_preview=_preview_text(combined_text),
        relevant_passages=top_passages,
        required_mentions=required_mentions,
        forbidden_claims=forbidden_claims,
        offer_details=offer_details,
        success=True,
        error_message=None,
    )


def _split_into_passages(text: str) -> list[str]:
    """Split extracted text into passage-sized chunks for ranking."""

    normalized = re.sub(r"\r\n?", "\n", text)
    blocks = [
        block.strip()
        for block in re.split(r"\n\s*\n", normalized)
        if block.strip()
    ]

    passages: list[str] = []
    current = ""
    for block in blocks:
        candidate = block if not current else f"{current}\n\n{block}"
        if len(candidate) <= 700:
            current = candidate
            continue

        if current:
            passages.append(current.strip())
        current = block

    if current:
        passages.append(current.strip())

    return passages


def _rank_passages(
    passages: list[str],
    sponsor_name: str,
    campaign_topic: str,
) -> list[str]:
    """Rank passages by overlap with sponsor/topic keywords and brief cues."""

    keywords = _keyword_set(f"{sponsor_name} {campaign_topic}")
    ranked = sorted(
        passages,
        key=lambda passage: _passage_score(passage, keywords),
        reverse=True,
    )
    return [passage for passage in ranked if _passage_score(passage, keywords) > 0] or ranked


def _passage_score(passage: str, keywords: set[str]) -> int:
    """Score a passage based on keyword overlap and instruction-like cues."""

    words = _keyword_set(passage)
    overlap = len(words & keywords)
    lowered = passage.lower()
    cue_bonus = sum(
        1
        for cue in (
            "must mention",
            "key message",
            "talking point",
            "do not",
            "discount",
            "promo code",
            "call to action",
            "offer",
            "required",
        )
        if cue in lowered
    )
    return overlap + cue_bonus


def _extract_required_mentions(passages: list[str]) -> list[str]:
    """Extract likely campaign requirements from imperative brief language."""

    results: list[str] = []
    patterns = (
        r"(?:must mention|mention|include|highlight|emphasize|required(?: talking points?)?)[:\-\s]+(.+)",
        r"(?:key messages?|talking points?)[:\-\s]+(.+)",
    )

    for passage in passages:
        for line in _candidate_lines(passage):
            lowered = line.lower()
            for pattern in patterns:
                match = re.search(pattern, lowered, re.IGNORECASE)
                if match:
                    extracted = _clean_extracted_item(line[match.start(1) :])
                    if _is_meaningful_item(extracted):
                        results.extend(_split_list_like_text(extracted))
                    break
            else:
                if any(token in lowered for token in ("must mention", "be sure to mention")):
                    extracted = _clean_extracted_item(line)
                    if _is_meaningful_item(extracted):
                        results.append(extracted)

    return _dedupe_preserve_order(results)


def _extract_forbidden_claims(passages: list[str]) -> list[str]:
    """Extract restrictions and risky claim guidance from the brief."""

    results: list[str] = []
    patterns = (
        r"(?:do not|don't|avoid|never say|must not)[:\-\s]+(.+)",
        r"(?:prohibited|forbidden|not allowed)[:\-\s]+(.+)",
    )

    for passage in passages:
        for line in _candidate_lines(passage):
            lowered = line.lower()
            for pattern in patterns:
                match = re.search(pattern, lowered, re.IGNORECASE)
                if match:
                    extracted = _clean_extracted_item(line[match.start(1) :])
                    if _is_meaningful_item(extracted):
                        results.extend(_split_list_like_text(extracted))
                    break

    return _dedupe_preserve_order(results)


def _extract_offer_details(passages: list[str]) -> list[str]:
    """Extract likely offer, pricing, and CTA details from the brief."""

    results: list[str] = []
    offer_keywords = (
        "discount",
        "promo code",
        "offer",
        "free trial",
        "coupon",
        "save",
        "pricing",
        "cta",
        "call to action",
        "link in description",
        "use code",
        "use the code",
        "limited time",
    )

    for passage in passages:
        for line in _candidate_lines(passage):
            lowered = line.lower()
            if any(keyword in lowered for keyword in offer_keywords):
                extracted = _clean_extracted_item(line)
                if _is_meaningful_item(extracted):
                    results.append(extracted)

    return _dedupe_preserve_order(results)


def _candidate_lines(passage: str) -> list[str]:
    """Yield useful line fragments from a passage for heuristic parsing."""

    normalized = re.sub(r"[ \t]+", " ", passage)
    lines = [line.strip(" -\t") for line in normalized.splitlines()]
    return [line for line in lines if line]


def _split_list_like_text(text: str) -> list[str]:
    """Split bullet-like text fragments into distinct items when possible."""

    parts = re.split(r"\s*(?:;|,|\u2022|\||/)\s*", text)
    cleaned_parts = [_clean_extracted_item(part) for part in parts]
    return [part for part in cleaned_parts if _is_meaningful_item(part)]


def _clean_extracted_item(text: str) -> str:
    """Normalize extracted list items into short, readable strings."""

    cleaned = re.sub(r"\s+", " ", text).strip(" -:;,.")
    return cleaned[:240]


def _is_meaningful_item(text: str) -> bool:
    """Filter out noisy or overly short fragments from heuristic extraction."""

    cleaned = text.strip()
    if len(cleaned) < 8:
        return False

    alpha_tokens = re.findall(r"[A-Za-z]{3,}", cleaned)
    if len(alpha_tokens) < 2:
        return False

    useless_phrases = {
        "to",
        "or",
        "and",
        "for this assignment",
        "go above 8",
        "handoffs",
    }
    return cleaned.lower() not in useless_phrases


def _keyword_set(text: str) -> set[str]:
    """Build a normalized keyword set for lightweight passage ranking."""

    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "your",
        "into",
        "about",
        "have",
        "will",
        "they",
        "them",
        "their",
        "you",
    }
    tokens = re.findall(r"[a-zA-Z0-9]{3,}", text.lower())
    return {token for token in tokens if token not in stop_words}


def _preview_text(text: str, max_chars: int = 500) -> str:
    """Create a compact preview of extracted document text."""

    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[: max_chars - 3].rstrip()}..."


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    """Return unique non-empty strings while preserving order."""

    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        cleaned = value.strip()
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)
    return deduped
