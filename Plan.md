# Coach Copilot: Strategic Plan & Technical Roadmap

This document outlines the architectural and functional development of Coach Copilot, an AI assistant for powerlifting coaches and athletes.

## 1. Project Vision

To create a "Digital Twin" of a Powerlifting Coach that combines the precision of Data Engineering with specialized domain expertise. The system bridges the gap between static training plans (Google Sheets) and dynamic expert guidance (YouTube/Coaching Docs).

## 2. Tech Stack

- **Orchestration:** LangGraph (State-based Agentic Workflows)
- **Agent Pattern:** ReAct (Reasoning + Acting)
- **RAG Engine:** Multi-modal & Semantic RAG
- **Environment:** uv for package management, FastAPI backend
- **Data Storage:** ChromaDB (vector), Google Sheets API (structured)

## 3. Development Phases

### Phase 1: The Informed Observer (Read-Only)

Establish trust by accurately retrieving data.

- "What is my workout today?" → Reads Google Sheets and summarizes
- "What are the IPF rules for the bench press?" → Retrieves from technical rulebooks via RAG
- Basic LangGraph implementation with SearchTool and SheetsReaderTool

### Phase 2: The Domain Expert (Calculators & Multimedia)

Add specialized math and personal coaching voice.

- Mathematical Precision: Custom tools for E1RM, IPF GL scores, Plate Loading
- Visual Integration: Linking YouTube tutorials with summaries
- Tool-calling optimization and YouTube Transcript RAG

### Phase 3: The Adaptive Strategist (Agentic Writing)

Intelligent rescheduling and plan modification.

- Plan Rescheduling: Agent condenses training blocks and updates Google Sheet
- Injury Management: Cross-references injury protocols and suggests load reductions
- Advanced LangGraph nodes for "Plan Logic" and Google Sheets Write-access tools

## 4. System Architecture

1. **Plan Node:** Creates retrieval strategy based on user intent
2. **Retrieve Node:** Searches vector store + uploaded documents
3. **Grade Node:** LLM evaluates document relevance
4. **Agent Node:** Calls registered tools via LangGraph ToolNode
5. **Generate Node:** Produces final coaching response

## 5. Future Enhancements

- Multi-athlete support with PIN authentication
- Vision analysis for form check videos
- Competition prep countdown scheduler
- Integration with wearables (RPE auto-detection)
