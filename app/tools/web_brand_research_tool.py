"""Schemas and starter implementation for the sponsor web research tool."""

from pydantic import BaseModel, Field


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
    """Collect sponsor facts from web sources.

    This starter implementation defines the contract only.
    Replace the placeholder result with real search and scraping logic later.
    """

    return WebBrandResearchOutput(
        sponsor_name=input_data.sponsor_name,
        query=input_data.query,
        summaries=[],
        verified_facts=[],
        source_snippets=[],
        source_links=input_data.website_urls,
        success=True,
        error_message=None,
    )
