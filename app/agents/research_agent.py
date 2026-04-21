"""Research Agent node for collecting sponsor information."""

from __future__ import annotations

from typing import Iterable

from app.graph.state import AgentLog, MASState, SourceSnippet, SponsorResearch
from app.tools.pdf_brief_reader_tool import PDFBriefReaderInput, read_pdf_brief_tool
from app.tools.web_brand_research_tool import (
    WebBrandResearchInput,
    web_brand_research_tool,
)


RESEARCH_AGENT_NAME = "ResearchAgent"


def run_research_agent(state: MASState) -> MASState:
    """Build sponsor research from uploaded PDFs and optional web sources."""

    logs = list(state.get("logs", []))
    pdf_outputs = []
    web_output = None

    logs.append(
        _log(
            step="start",
            status="started",
            message="Research Agent started sponsor information gathering.",
        )
    )

    for pdf_path in state.get("pdf_paths", []):
        pdf_result = read_pdf_brief_tool(
            PDFBriefReaderInput(
                pdf_path=pdf_path,
                sponsor_name=state["sponsor_name"],
                campaign_topic=state["campaign_topic"],
            )
        )
        pdf_outputs.append(pdf_result)
        logs.append(
            _log(
                step="pdf_read",
                tool_used="read_pdf_brief_tool",
                status="success" if pdf_result.success else "failed",
                message=(
                    f"Processed PDF brief: {pdf_path}"
                    if pdf_result.success
                    else f"Failed to process PDF brief: {pdf_path}"
                ),
            )
        )

    needs_web_research = bool(state.get("website_urls")) or not _has_enough_pdf_data(
        pdf_outputs
    )

    if needs_web_research:
        query = _build_research_query(state)
        web_output = web_brand_research_tool(
            WebBrandResearchInput(
                sponsor_name=state["sponsor_name"],
                query=query,
                website_urls=state.get("website_urls", []),
            )
        )
        logs.append(
            _log(
                step="web_search",
                tool_used="web_brand_research_tool",
                status="success" if web_output.success else "failed",
                message=(
                    f"Completed web research for query: {query}"
                    if web_output.success
                    else f"Web research failed for query: {query}"
                ),
            )
        )

    sponsor_research = _merge_research_outputs(
        sponsor_name=state["sponsor_name"],
        required_talking_points=state.get("required_talking_points", []),
        pdf_outputs=pdf_outputs,
        web_output=web_output,
    )

    logs.append(
        _log(
            step="complete",
            status="completed",
            message="Research Agent finished building sponsor research state.",
        )
    )

    updated_state = dict(state)
    updated_state["sponsor_research"] = sponsor_research
    updated_state["logs"] = logs
    return updated_state


def _build_research_query(state: MASState) -> str:
    """Create a compact query for sponsor web research."""

    parts = [state["sponsor_name"], state["campaign_topic"]]
    product_name = state.get("product_name", "").strip()
    if product_name:
        parts.append(product_name)
    return " ".join(part for part in parts if part).strip()


def _has_enough_pdf_data(pdf_outputs: Iterable) -> bool:
    """Decide whether PDF results are sufficient without web backup."""

    successful = [output for output in pdf_outputs if output.success]
    if not successful:
        return False

    has_mentions = any(output.required_mentions for output in successful)
    has_offers = any(output.offer_details for output in successful)
    return has_mentions or has_offers


def _merge_research_outputs(
    sponsor_name: str,
    required_talking_points: list[str],
    pdf_outputs: list,
    web_output,
) -> SponsorResearch:
    """Combine tool outputs into a single structured sponsor research object."""

    product_features: list[str] = []
    offer_details: list[str] = []
    required_mentions: list[str] = list(required_talking_points)
    forbidden_claims: list[str] = []
    verified_facts: list[str] = []
    uncertain_points: list[str] = []
    source_snippets: list[SourceSnippet] = []
    source_links: list[str] = []
    research_gaps: list[str] = []

    for output in pdf_outputs:
        if output.success:
            required_mentions.extend(output.required_mentions)
            forbidden_claims.extend(output.forbidden_claims)
            offer_details.extend(output.offer_details)

            if output.extracted_text_preview:
                source_snippets.append(
                    {
                        "type": "pdf",
                        "source": output.pdf_path,
                        "snippet": output.extracted_text_preview,
                    }
                )

            for passage in output.relevant_passages:
                source_snippets.append(
                    {
                        "type": "pdf",
                        "source": output.pdf_path,
                        "snippet": passage,
                    }
                )
        elif output.error_message:
            uncertain_points.append(output.error_message)

    if web_output and web_output.success:
        verified_facts.extend(web_output.verified_facts)
        product_features.extend(web_output.summaries)
        source_links.extend(web_output.source_links)
        for snippet in web_output.source_snippets:
            source_snippets.append(
                {
                    "type": "web",
                    "source": snippet.url,
                    "snippet": snippet.snippet,
                }
            )
    elif web_output and web_output.error_message:
        uncertain_points.append(web_output.error_message)

    if not source_snippets:
        research_gaps.append("No usable research snippets were collected yet.")
    if not verified_facts:
        research_gaps.append("No verified sponsor facts were collected yet.")
    if not offer_details:
        research_gaps.append("No sponsor offer details were found.")
    if not required_mentions:
        research_gaps.append("No required talking points were identified.")

    sponsor_summary = _build_summary(
        sponsor_name=sponsor_name,
        verified_facts=verified_facts,
        product_features=product_features,
    )

    return {
        "sponsor_summary": sponsor_summary,
        "product_features": _dedupe_preserve_order(product_features),
        "offer_details": _dedupe_preserve_order(offer_details),
        "required_mentions": _dedupe_preserve_order(required_mentions),
        "forbidden_claims": _dedupe_preserve_order(forbidden_claims),
        "verified_facts": _dedupe_preserve_order(verified_facts),
        "uncertain_points": _dedupe_preserve_order(uncertain_points),
        "source_snippets": source_snippets,
        "source_links": _dedupe_preserve_order(source_links),
        "research_gaps": _dedupe_preserve_order(research_gaps),
    }


def _build_summary(
    sponsor_name: str,
    verified_facts: list[str],
    product_features: list[str],
) -> str:
    """Create a compact summary for downstream agents."""

    if verified_facts:
        return verified_facts[0]

    if product_features:
        return f"{sponsor_name} research collected around: {product_features[0]}."

    return f"No verified summary is available yet for {sponsor_name}."


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    """Return unique non-empty strings while preserving input order."""

    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        deduped.append(cleaned)
    return deduped


def _log(
    step: str,
    status: str,
    message: str,
    tool_used: str | None = None,
) -> AgentLog:
    """Create a consistent Research Agent log entry."""

    entry: AgentLog = {
        "agent_name": RESEARCH_AGENT_NAME,
        "step": step,
        "status": status,
        "message": message,
    }
    if tool_used:
        entry["tool_used"] = tool_used
    return entry
