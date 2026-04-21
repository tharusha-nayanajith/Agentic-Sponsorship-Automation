"""Schemas and starter implementation for the sponsor PDF brief reader tool."""

from pathlib import Path

from pydantic import BaseModel, Field


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

    This starter implementation only performs basic path validation.
    Replace the placeholder extraction logic with actual PDF parsing later.
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

    return PDFBriefReaderOutput(
        pdf_path=input_data.pdf_path,
        sponsor_name=input_data.sponsor_name,
        extracted_text_preview="PDF extraction not implemented yet.",
        relevant_passages=[],
        required_mentions=[],
        forbidden_claims=[],
        offer_details=[],
        success=True,
        error_message=None,
    )
