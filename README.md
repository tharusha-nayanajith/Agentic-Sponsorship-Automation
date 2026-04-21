# Agentic Sponsorship Automation

Creator Sponsorship Segment MAS is a locally hosted multi-agent system for generating creator-style sponsorship segments for YouTube videos. The current implementation includes the Research Agent, a typed shared state model, a PDF sponsor brief reader, a web brand research tool, and a runnable CLI workflow.

## Current Scope

- Research Agent that gathers sponsor information from PDFs and the web
- Shared `MASState` structure for multi-agent handoff
- `read_pdf_brief_tool` for extracting relevant passages from sponsor briefs
- `web_brand_research_tool` for collecting structured facts from preferred URLs and web search
- CLI entry point for running the current research workflow end to end

## Project Structure

```text
app/
  agents/
    research_agent.py
  graph/
    state.py
    workflow.py
  tools/
    pdf_brief_reader_tool.py
    web_brand_research_tool.py
main.py
requirements.txt
```

## Requirements

- Python 3.10+
- Internet access for live web research
- Optional sponsor brief PDFs for document-based research

## Setup

### 1. Create a virtual environment

```powershell
uv venv .venv
```

### 2. Install dependencies

```powershell
uv pip install --python .\.venv\Scripts\python.exe -r requirements.txt
```

If you already have a preferred Python environment, you can install the same dependencies there instead.

## Run the Research Workflow

Basic example:

```powershell
.\.venv\Scripts\python.exe main.py `
  --sponsor-name Clerk `
  --campaign-topic "authentication developer platform" `
  --product-name Clerk `
  --website-url https://clerk.com
```

Example with a PDF brief:

```powershell
.\.venv\Scripts\python.exe main.py `
  --sponsor-name Clerk `
  --campaign-topic "authentication developer platform" `
  --product-name Clerk `
  --website-url https://clerk.com `
  --pdf-path "C:\path\to\sponsor-brief.pdf"
```

Example with multiple inputs:

```powershell
.\.venv\Scripts\python.exe main.py `
  --sponsor-name Clerk `
  --campaign-topic "authentication developer platform" `
  --product-name Clerk `
  --website-url https://clerk.com `
  --website-url https://github.com/clerk/clerk-docs `
  --pdf-path "C:\path\to\brief-1.pdf" `
  --pdf-path "C:\path\to\brief-2.pdf" `
  --talking-point "developer-friendly integration" `
  --talking-point "secure authentication"
```

## Optional Output File

You can save the resulting JSON state to a file:

```powershell
.\.venv\Scripts\python.exe main.py `
  --sponsor-name Clerk `
  --campaign-topic "authentication developer platform" `
  --website-url https://clerk.com `
  --output research-output.json
```

## What the CLI Returns

The command prints the full workflow state as JSON, including:

- input fields such as sponsor name and campaign topic
- Research Agent execution logs
- structured `sponsor_research` output
- source snippets and source links
- identified research gaps

## Current Limitations

- Only the Research Agent is implemented so far
- PDF extraction uses heuristics and works best on text-based PDFs
- Web research currently uses lightweight scraping and heuristic fact extraction
- Search results may include non-official pages if they appear relevant

## Next Planned Components

- Creator Style Agent
- Sponsorship Writer Agent
- Compliance and Review Agent
- Full LangGraph orchestration
- automated tests and evaluation scripts

## Notes for the Assignment

This repository is being built toward the CTSE Assignment 2 requirement for a locally hosted Multi-Agent System using:

- multiple collaborating agents
- custom Python tools
- explicit shared state management
- observability through agent logs

