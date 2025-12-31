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

### Implemented

- Multi-athlete support with PIN authentication
- Structured output classification for smart routing
- Configurable fast/main models for both Ollama and Gemini
- **Query Reformulation Agent**: Clarifies ambiguous user input before classification, passes clear input unchanged
- **Smart Error Handling**: Targeted error handling with graceful fallbacks throughout the agent pipeline
- **RAG Scoring**: Document relevance scoring (0-1 scale), using only top 5 documents for response generation
- **Prompt Improvements**: Refined classify prompt, renamed greeting → small_talk for better semantic clarity
- **LangFuse Monitoring**: Full observability with tracing, latency, token usage, and cost tracking
- **Prompt Management**: Prompts organized in `src/prompts/` directory with `load_prompt()` loader
- **Clickable Links**: Document sources included in context for LLM to reference
- **Thinking Display**: Chain-of-thought display showing agent reasoning steps (collapsible 🧠 Thinking)
- **Chat Sessions**: Session sidebar with new/switch/delete, persisted per-user (last 10 sessions)
- **Advanced Search**: `crawl_url` tool for deep page extraction using WebBaseLoader
- **Competition Countdown**: `competition_countdown` tool with weeks/days + peaking advice

### Planned

- Integration with wearables (RPE auto-detection)

### Optional Extensions

- **YouTube Data API**: Enable channel search, video listing, metadata access

## Framework Considerations

The following frameworks are being evaluated for future iterations to enhance structure and reliability:

- **PydanticAI**:

  - **Why**: Provides a strongly-typed framework for building agents where every input/output is validated by Pydantic schemas.
  - **Use Case**: Could replace or augment the current node logic to ensure strictly typed state transitions and reduce runtime errors in the agent graph. Useful for complex multi-agent handoffs.

- **Instructor**:
  - **Why**: A specialized library that patches OpenAI-compatible clients (like Ollama) to enforce structured outputs using Pydantic models.
  - **Use Case**: Superior for smaller local models (like `qwen2.5:3b`) compared to standard JSON modes. Would significantly improve reliability of the `classify_input` and `grade_documents` nodes by guaranteeing valid JSON schemas and automatically retrying on validation failures.
