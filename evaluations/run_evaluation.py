"""Simple end-to-end evaluation harness for the MAS workflow."""

from __future__ import annotations

import json

from app.graph.workflow import run_research_workflow


def main() -> None:
    """Run a compact end-to-end evaluation and print pass/fail checks."""

    initial_state = {
        "sponsor_name": "Clerk",
        "campaign_topic": "authentication developer platform",
        "product_name": "",
        "target_audience": "general developer audience",
        "tone_goal": "creator-style sponsorship segment",
        "pdf_paths": [],
        "website_urls": ["https://clerk.com"],
        "creator_samples": [
            "We're going to do a quick break for today's sponsor. "
            "Let's get straight to it. I think this is cool and useful."
        ],
        "required_talking_points": [],
        "revision_count": 0,
        "logs": [],
        "tool_traces": [],
    }

    final_state = run_research_workflow(initial_state)
    report = final_state.get("compliance_report", {})

    checks = {
        "has_research": bool(final_state.get("sponsor_research")),
        "has_style_profile": bool(final_state.get("creator_style_profile")),
        "has_draft": bool(final_state.get("sponsorship_draft")),
        "has_compliance_report": bool(report),
        "has_logs": bool(final_state.get("logs")),
        "has_tool_traces": bool(final_state.get("tool_traces")),
    }

    print("Evaluation Checks")
    for key, value in checks.items():
        print(f"- {key}: {'PASS' if value else 'FAIL'}")

    print("\nCompliance Report")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
