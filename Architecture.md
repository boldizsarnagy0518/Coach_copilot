# Coach Copilot - Main Architecture (Living Document)

This is the "Single Source of Truth" for the project. The Agent is required to update this file after every significant structural or logical change.

## 1. System Objective

To create an autonomous Powerlifting Coach Agent that operates at the intersection of biomechanical laws (math), official federation regulations (RAG), and individualized training data (Google Sheets).

## 2. Modern Tech Stack (2025/2026)

Orchestration: LangGraph (State-based Agentic Workflows).

Primary LLM: Gemini 2.0 Pro/Flash (for Google Ecosystem synergy & massive context).

Package Management: uv (Fast, Rust-based Python manager).

Environment: Documentation-Driven Development (Context provided via .md files).

Integrations: Google Sheets API, YouTube Transcript Loader, Multi-source Vector Store.

## 3. Agentic Workflow (The Loop)

[Analyzer Node]: Parses user intent (Instructional, Mathematical, or Administrative).

[Context Fetcher]: Loads relevant context_*.md files and external API data.

[Reasoner/Expert Node]: Processes data based on the "Coach Persona" and domain knowledge.

[Action/Tool Node]: Executes Python code (1RM Calc) or API writes (G-Sheets updates).

[Documenter Node]: Synchronizes changes back to the Markdown architecture files.

## 4. Context Map

context_sheets.md: Mapping of the Spreadsheet schema and cell logic.

context_rag.md: Status of vector indices (IPF rules, coaching notes).

context_youtube.md: Index of video tutorials and transcript embeddings.
