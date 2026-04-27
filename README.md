# Agentic Sponsorship Automation

Creator Sponsorship Segment MAS is a locally hosted multi-agent system for generating creator-style sponsorship segments for YouTube videos. The current implementation includes the Research Agent, Creator Style Agent, Sponsorship Writer Agent, Compliance Review Agent, a typed shared state model, custom tools, LangGraph orchestration, and a runnable CLI workflow.

## Current Scope

- Research Agent that gathers sponsor information from PDFs and the web
- Creator Style Agent that analyzes creator transcript samples
- Sponsorship Writer Agent that drafts a creator-style sponsorship segment
- Compliance Review Agent that validates the draft and produces a final reviewed segment
- Shared `MASState` structure for multi-agent handoff
- LangGraph orchestration for agent sequencing
- LangGraph conditional routing for one compliance-driven rewrite pass
- `read_pdf_brief_tool` for extracting relevant passages from sponsor briefs
- `web_brand_research_tool` for collecting structured facts from preferred URLs and web search
- CLI entry point for running the current research workflow end to end

## Project Structure

```text
app/
  agents/
    compliance_review_agent.py
    creator_style_agent.py
    research_agent.py
    sponsorship_writer_agent.py
  graph/
    langgraph_workflow.py
    state.py
    workflow.py
  tools/
    compliance_review_tool.py
    creator_style_analysis_tool.py
    pdf_brief_reader_tool.py
    sponsorship_segment_writer_tool.py
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

## Run the Streamlit Demo

You can also run a simple demo UI for the viva:

```bash
./.venv/Scripts/python.exe -m streamlit run streamlit_app.py
```

The Streamlit UI lets you:

- enter sponsor name, topic, URLs, and creator sample
- upload sponsor brief PDFs
- run the full workflow
- present the final segment, logs, compliance report, and raw state in separate tabs
- show an execution trace for each tool call with summarized input and output details

## What the CLI Returns

The command prints the full workflow state as JSON, including:

- input fields such as sponsor name and campaign topic
- Research Agent execution logs
- Creator Style Agent execution logs
- Sponsorship Writer Agent execution logs
- Compliance Review Agent execution logs
- structured `sponsor_research` output
- structured `creator_style_profile` output when samples are provided
- structured `sponsorship_draft` output
- structured `compliance_report` output
- structured `final_sponsorship_segment` output
- source snippets and source links
- identified research gaps

## Current Limitations

- The current workflow includes Research, Creator Style analysis, draft writing, and compliance review
- PDF extraction uses heuristics and works best on text-based PDFs
- Web research currently uses lightweight scraping and heuristic fact extraction
- Search results may include non-official pages if they appear relevant

## Next Planned Components

- Full LangGraph orchestration
- automated tests and evaluation scripts

## Notes for the Assignment

This repository is being built toward the CTSE Assignment 2 requirement for a locally hosted Multi-Agent System using:

- multiple collaborating agents
- LangGraph for orchestration
- custom Python tools
- explicit shared state management
- observability through agent logs

## Ollama Integration

The Sponsorship Writer Agent now prefers a local Ollama model and falls back to the deterministic writer if Ollama is unavailable.

Recommended local model:

- `qwen2.5:3b` for lightweight testing
- `qwen2.5:7b` later if you want stronger writing quality

Example environment setup in Git Bash:

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="qwen2.5:3b"
```

Example environment setup in PowerShell:

```powershell
$env:OLLAMA_BASE_URL="http://localhost:11434"
$env:OLLAMA_MODEL="qwen2.5:3b"
```

Quick Ollama client smoke test:

```bash
./.venv/Scripts/python.exe -c "from app.llm.ollama_client import OllamaClient; c = OllamaClient(); print(c.health_check()); print(c.list_models()); print(c.generate('Write one short sponsor intro for Clerk.'))"
```
