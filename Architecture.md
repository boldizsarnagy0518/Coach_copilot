# Coach Copilot

AI-powered Powerlifting Coach Assistant

## Architecture

```
src/
├── config.py        # Settings (Pydantic)
├── llm.py           # LLM providers (Ollama/Gemini)
├── rag.py           # Vector store (ChromaDB)
├── tools/           # LangChain tools
│   ├── calculators.py  # E1RM, IPF GL, Plates
│   ├── sheets.py       # Google Sheets read/write
│   ├── youtube.py      # YouTube transcripts
│   └── web_search.py   # DuckDuckGo search
├── agent/           # LangGraph agent
│   ├── graph.py     # State machine with tool calling
│   ├── nodes.py     # Plan, Retrieve, Grade, Generate
│   ├── state.py     # Pydantic state schema
│   └── runner.py    # Entry point
└── app.py           # NiceGUI web UI
```

## Tech Stack

| Component     | Technology                   |
| ------------- | ---------------------------- |
| Orchestration | LangGraph (ReAct pattern)    |
| LLM           | Ollama (dev) / Gemini (prod) |
| Embeddings    | Ollama / Gemini              |
| Vector Store  | ChromaDB                     |
| UI            | NiceGUI (includes FastAPI)   |
| Tools         | LangChain @tool decorators   |
| YouTube       | youtube-transcript-api       |
| Sheets        | gspread + google-auth        |

## Features

- **Agentic RAG** (Plan -> Retrieve -> Grade -> Tool/Generate)
- **10 LangChain Tools** with Pydantic schemas:
  - Calculators: E1RM, IPF GL, Plate loading
  - Sheets: Read, Update, List training data
  - YouTube: Load transcripts, channel info
  - Web: DuckDuckGo search
- Document upload (PDF, TXT, MD) per chat session
- Google Sheets integration with CnumberBnumber ordering
- Structured outputs with Pydantic models

## Architecture

### Safety Layer

- **Recursion Limit**: Max 3 tool calls per user turn (prevents infinite loops).
- **Tool Error Handling**: Auto-discovery for Sheets, resilient paths for credentials.
- **Input Classification**: Direct routing for greetings/commands (skips expensive RAG).

## Tool Calling Flow

```
User Question
    ↓
[Classify Node] → Greeting/Command? ──→ [Agent Node] (Fast Path)
    ↓ (Complex Question)
[Plan Node] → Creates retrieval strategy
    ↓
[Retrieve Node] → Searches vector store + uploads
    ↓
[Grade Node] → LLM evaluates relevance
    ↓
    ├── Relevant → [Generate Node] → Answer
    └── Not Relevant → [Agent Node] → Can call tools (Max 3 iterations)
                           ↓     ↑
                    [Tool Node] ─┘
```

## Run

```bash
uv sync --group dev
uv run coach
```

Opens at http://localhost:8080
