"""CLI entry point for the Creator Sponsorship Segment MAS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.graph.state import MASState
from app.graph.workflow import run_research_workflow


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the current workflow."""

    parser = argparse.ArgumentParser(
        description="Run the current Creator Sponsorship Segment MAS workflow."
    )
    parser.add_argument("--sponsor-name", required=True, help="Sponsor brand name.")
    parser.add_argument(
        "--campaign-topic",
        required=True,
        help="Campaign topic or product focus for research.",
    )
    parser.add_argument(
        "--product-name",
        default="",
        help="Optional product name to refine the research query.",
    )
    parser.add_argument(
        "--target-audience",
        default="general developer audience",
        help="Audience context for downstream agents.",
    )
    parser.add_argument(
        "--tone-goal",
        default="creator-style sponsorship segment",
        help="Tone goal for downstream agents.",
    )
    parser.add_argument(
        "--pdf-path",
        dest="pdf_paths",
        action="append",
        default=[],
        help="Path to a sponsor brief PDF. Repeat for multiple PDFs.",
    )
    parser.add_argument(
        "--website-url",
        dest="website_urls",
        action="append",
        default=[],
        help="Preferred website URL to research. Repeat for multiple URLs.",
    )
    parser.add_argument(
        "--talking-point",
        dest="required_talking_points",
        action="append",
        default=[],
        help="Required sponsor talking point. Repeat for multiple items.",
    )
    parser.add_argument(
        "--creator-sample",
        dest="creator_samples",
        action="append",
        default=[],
        help="Optional creator transcript sample text or file path.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional file path to save the full resulting state as JSON.",
    )
    return parser.parse_args()


def build_initial_state(args: argparse.Namespace) -> MASState:
    """Build the initial typed state for the current workflow."""

    creator_samples = [_resolve_creator_sample(sample) for sample in args.creator_samples]

    return {
        "sponsor_name": args.sponsor_name,
        "campaign_topic": args.campaign_topic,
        "product_name": args.product_name,
        "target_audience": args.target_audience,
        "tone_goal": args.tone_goal,
        "pdf_paths": args.pdf_paths,
        "website_urls": args.website_urls,
        "creator_samples": creator_samples,
        "required_talking_points": args.required_talking_points,
        "revision_count": 0,
        "logs": [],
        "tool_traces": [],
    }


def _resolve_creator_sample(value: str) -> str:
    """Treat creator sample inputs as text unless they point to a real file."""

    path = Path(value)
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8")
    return value


def main() -> None:
    """Run the current workflow and print the resulting state."""

    args = parse_args()
    initial_state = build_initial_state(args)
    final_state = run_research_workflow(initial_state)

    json_output = json.dumps(final_state, indent=2)
    print(json_output)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json_output, encoding="utf-8")


if __name__ == "__main__":
    main()
