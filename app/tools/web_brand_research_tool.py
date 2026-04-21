"""Schemas and implementation for the sponsor web research tool."""

from __future__ import annotations

from html import unescape
from urllib.parse import parse_qs, quote_plus, urlparse
import re

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
import requests


REQUEST_TIMEOUT_SECONDS = 12
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


class WebSourceSnippet(BaseModel):
    """A concise web finding tied to a specific page."""

    url: str = Field(..., description="Source URL.")
    title: str = Field(..., description="Title of the source page.")
    snippet: str = Field(..., description="Relevant summary extracted from the page.")


class WebBrandResearchInput(BaseModel):
    """Inputs required for web research about a sponsor or campaign."""

    sponsor_name: str = Field(..., description="Name of the sponsor to research.")
    query: str = Field(..., description="Search query for sponsor web research.")
    website_urls: list[str] = Field(
        default_factory=list,
        description="Optional preferred URLs to inspect before general search.",
    )
    max_results: int = Field(
        5,
        ge=1,
        le=10,
        description="Maximum number of web pages to process.",
    )


class WebBrandResearchOutput(BaseModel):
    """Structured result returned by the sponsor web research tool."""

    sponsor_name: str
    query: str
    summaries: list[str]
    verified_facts: list[str]
    source_snippets: list[WebSourceSnippet]
    source_links: list[str]
    success: bool
    error_message: str | None = None


def web_brand_research_tool(
    input_data: WebBrandResearchInput,
) -> WebBrandResearchOutput:
    """Collect sponsor facts from preferred URLs and live web search results."""

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    preferred_urls = _dedupe_preserve_order(
        [_canonicalize_url(url) for url in input_data.website_urls]
    )
    candidate_urls = list(preferred_urls)

    if len(candidate_urls) < input_data.max_results:
        search_urls = _search_web(
            session=session,
            query=input_data.query,
            max_results=input_data.max_results,
            preferred_domains=_extract_domains(preferred_urls),
        )
        candidate_urls.extend(search_urls)

    candidate_urls = _dedupe_preserve_order(
        [_canonicalize_url(url) for url in candidate_urls]
    )[: input_data.max_results]
    if not candidate_urls:
        return WebBrandResearchOutput(
            sponsor_name=input_data.sponsor_name,
            query=input_data.query,
            summaries=[],
            verified_facts=[],
            source_snippets=[],
            source_links=[],
            success=False,
            error_message="No candidate URLs were found for web research.",
        )

    summaries: list[str] = []
    verified_facts: list[str] = []
    source_snippets: list[WebSourceSnippet] = []
    source_links: list[str] = []
    errors: list[str] = []
    keywords = _keyword_set(f"{input_data.sponsor_name} {input_data.query}")

    for url in candidate_urls:
        page_result = _fetch_and_extract_page(
            session=session,
            url=url,
            keywords=keywords,
        )
        if page_result is None:
            errors.append(f"Failed to extract useful content from {url}")
            continue

        title, summary, facts, snippet = page_result
        summaries.append(summary)
        verified_facts.extend(facts)
        source_snippets.append(
            WebSourceSnippet(url=url, title=title, snippet=snippet)
        )
        source_links.append(url)

    success = bool(source_links)
    error_message = None
    if not success:
        error_message = (
            "; ".join(errors[:3]) if errors else "Web research did not return usable pages."
        )

    return WebBrandResearchOutput(
        sponsor_name=input_data.sponsor_name,
        query=input_data.query,
        summaries=_dedupe_preserve_order(summaries),
        verified_facts=_dedupe_preserve_order(verified_facts),
        source_snippets=source_snippets,
        source_links=_dedupe_preserve_order(source_links),
        success=success,
        error_message=error_message,
    )


def _search_web(
    session: requests.Session,
    query: str,
    max_results: int,
    preferred_domains: set[str],
) -> list[str]:
    """Search the web using DuckDuckGo's HTML results page."""

    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        response = session.get(search_url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    urls: list[str] = []
    for anchor in soup.select("a.result__a"):
        href = anchor.get("href", "").strip()
        normalized = _normalize_search_result_url(href)
        if not normalized or _is_low_value_url(normalized):
            continue
        urls.append(normalized)

    ranked_urls = sorted(
        _dedupe_preserve_order(urls),
        key=lambda url: _url_priority(url, preferred_domains),
    )
    return ranked_urls[:max_results]


def _fetch_and_extract_page(
    session: requests.Session,
    url: str,
    keywords: set[str],
) -> tuple[str, str, list[str], str] | None:
    """Fetch a page and extract a short structured research summary."""

    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException:
        return None

    content_type = response.headers.get("Content-Type", "").lower()
    if "html" not in content_type:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    for tag_name in ("script", "style", "noscript", "svg", "form", "nav", "footer"):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    title = _clean_text(soup.title.get_text(" ", strip=True) if soup.title else url)
    text_blocks = _extract_text_blocks(soup)
    ranked_blocks = _rank_text_blocks(text_blocks, keywords)
    if not ranked_blocks:
        return None

    top_blocks = ranked_blocks[:3]
    summary = _build_summary(title=title, blocks=top_blocks)
    facts = _extract_verified_facts(top_blocks, keywords)
    snippet = _build_snippet(top_blocks[0])

    return title, summary, facts, snippet


def _extract_text_blocks(soup: BeautifulSoup) -> list[str]:
    """Extract readable content blocks from a page."""

    blocks: list[str] = []
    selectors = ("h1", "h2", "h3", "p", "li")
    for element in soup.find_all(selectors):
        text = _clean_text(element.get_text(" ", strip=True))
        if _is_meaningful_block(text):
            blocks.append(text)
    return _dedupe_preserve_order(blocks)


def _rank_text_blocks(blocks: list[str], keywords: set[str]) -> list[str]:
    """Rank page blocks by keyword overlap and likely factual value."""

    return sorted(blocks, key=lambda block: _block_score(block, keywords), reverse=True)


def _block_score(block: str, keywords: set[str]) -> int:
    """Score a block for likely sponsor relevance."""

    block_keywords = _keyword_set(block)
    overlap = len(block_keywords & keywords)
    bonus = 0
    lowered = block.lower()
    if any(token in lowered for token in ("features", "pricing", "developer", "platform", "product", "built for")):
        bonus += 1
    if len(block) < 240:
        bonus += 1
    return overlap + bonus


def _build_summary(title: str, blocks: list[str]) -> str:
    """Build a compact summary line for downstream use."""

    lead = blocks[0]
    return _build_snippet(f"{title}: {lead}", max_chars=220)


def _extract_verified_facts(blocks: list[str], keywords: set[str]) -> list[str]:
    """Turn top-ranked blocks into short factual statements."""

    facts: list[str] = []
    for block in blocks:
        if _block_score(block, keywords) <= 0:
            continue
        facts.extend(_sentence_candidates(block))
    return _dedupe_preserve_order(facts[:5])


def _sentence_candidates(block: str) -> list[str]:
    """Split a text block into concise candidate facts."""

    sentences = re.split(r"(?<=[.!?])\s+", block)
    cleaned = [_build_snippet(sentence, max_chars=180) for sentence in sentences]
    return [
        sentence
        for sentence in cleaned
        if _is_meaningful_block(sentence)
        and not _looks_like_testimonial_metadata(sentence)
    ]


def _normalize_search_result_url(url: str) -> str:
    """Resolve DuckDuckGo redirect URLs into direct target URLs."""

    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        query = parse_qs(parsed.query)
        target = query.get("uddg", [""])[0]
        if target:
            return _canonicalize_url(unescape(target))
    return _canonicalize_url(url)


def _extract_domains(urls: list[str]) -> set[str]:
    """Collect domains from explicit preferred URLs."""

    domains: set[str] = set()
    for url in urls:
        parsed = urlparse(_canonicalize_url(url))
        if parsed.netloc:
            domains.add(parsed.netloc.lower())
    return domains


def _url_priority(url: str, preferred_domains: set[str]) -> tuple[int, str]:
    """Prefer official domains and shorter URLs in ranked results."""

    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    preferred = 0 if domain in preferred_domains else 1
    return preferred, url


def _is_low_value_url(url: str) -> bool:
    """Filter out obvious junk results."""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return True
    blocked_domains = {
        "duckduckgo.com",
        "youtube.com",
        "www.youtube.com",
        "facebook.com",
        "www.facebook.com",
        "instagram.com",
        "www.instagram.com",
    }
    return parsed.netloc.lower() in blocked_domains


def _clean_text(text: str) -> str:
    """Normalize whitespace and HTML entities."""

    normalized = unescape(text)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _canonicalize_url(url: str) -> str:
    """Normalize obvious duplicate URL forms such as trailing slashes."""

    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return url.strip()

    path = parsed.path or ""
    if path == "/":
        path = ""

    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        path=path,
        params="",
        query="",
        fragment="",
    )
    return normalized.geturl()


def _build_snippet(text: str, max_chars: int = 260) -> str:
    """Create a short readable snippet."""

    cleaned = _clean_text(text)
    if len(cleaned) <= max_chars:
        return cleaned
    return f"{cleaned[: max_chars - 3].rstrip()}..."


def _is_meaningful_block(text: str) -> bool:
    """Reject tiny or noisy extracted blocks."""

    if len(text) < 30:
        return False
    alpha_words = re.findall(r"[A-Za-z]{3,}", text)
    return len(alpha_words) >= 4


def _looks_like_testimonial_metadata(text: str) -> bool:
    """Filter out role/name metadata that is not useful as a sponsor fact."""

    lowered = text.lower()
    noisy_markers = (" role ", " company ", " name ", " ceo ", " founder ")
    return any(marker in f" {lowered} " for marker in noisy_markers)


def _keyword_set(text: str) -> set[str]:
    """Build a normalized keyword set for lightweight relevance scoring."""

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
