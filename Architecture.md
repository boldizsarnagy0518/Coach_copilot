# Coach Copilot

AI-powered Powerlifting Coach Assistant

## Architecture

```text
src/
├── config.py    # Settings (Pydantic)
├── llm.py       # LLM providers (Ollama/Gemini)
├── tools.py     # Calculators (E1RM, IPF GL, Plates)
├── rag.py       # Vector store (ChromaDB)
├── youtube.py   # YouTube transcript loader
├── sheets.py    # Google Sheets (CnumberBnumber logic)
├── agent/       # LangGraph agent
│   ├── graph.py # State machine
│   ├── nodes.py # Logic steps
│   └── state.py # Pydantic state
└── app.py       # NiceGUI web UI
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Ollama (dev) / Gemini (prod) |
| Embeddings | Ollama / Gemini |
| Vector Store | ChromaDB |
| UI | NiceGUI (includes FastAPI) |
| YouTube | youtube-transcript-api |
| Sheets | gspread + google-auth |

## Features

- **Agentic RAG** (Plan -> Retrieve -> Grade -> Generate)
- Web search fallback
- Document upload (PDF, TXT, MD) per chat session
- YouTube transcript indexing
- Google Sheets integration with CnumberBnumber ordering
- Calculators: E1RM, IPF GL Points, Plate loading

## CnumberBnumber Logic

For Google Sheets, newest sheet is determined by:

- C (cycle) > B (block)
- C3B1 is newer than C2B10
- C3B6 is newer than C3B4

## Run

```bash
uv sync --group dev
uv run coach
```

Opens at <http://localhost:8080>
