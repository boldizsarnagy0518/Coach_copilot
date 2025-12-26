# Coach Copilot

**AI-powered Powerlifting Coach Assistant** built with **LangGraph**, **RAG**, and **NiceGUI**.

An **agentic system** that acts as a personalized powerlifting coach. It classifies user input, retrieves knowledge from documents and YouTube, and uses specialized tools for calculations.

![Agent Graph](agent_graph.png)

## Key Features

- **Smart Input Classification**: LLM-powered routing (commands skip RAG, questions use full pipeline)
- **Multi-Athlete Support**: PIN-protected login, per-athlete Google Sheets access
- **Agentic Workflow (LangGraph)**:
  - Planning node for complex query analysis
  - Hybrid RAG with document grading
  - Web search fallback for current information
- **Powerlifting Tools**: E1RM calculator, IPF GL Points, Plate Loading
- **Dual LLM Support**: Ollama (local) or Gemini (API)
- **YouTube Integration**: Transcript extraction from coaching videos

## Quick Start

```bash
# Clone
git clone https://github.com/yourusername/coach-copilot.git
cd coach-copilot

# Install (using uv - fast Python package manager)
uv sync

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
uv run coach
```

Open [http://localhost:8080](http://localhost:8080)

## Configuration

Key settings in `.env`:

```env
# LLM Provider: "ollama" or "gemini"
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_FAST_MODEL=qwen2.5:0.5b

# For Gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-1.5-pro
GEMINI_FAST_MODEL=gemini-2.0-flash

# Multi-athlete PINs
ATHLETE_PINS={"Boldi": "1234", "John": "5678"}
```

## Project Structure

```
src/
├── agent/           # LangGraph workflow
│   ├── graph.py     # State machine with tool calling
│   ├── nodes.py     # Classify, Plan, Retrieve, Grade, Generate
│   └── state.py     # Pydantic state schema
├── tools/           # LangChain tools
│   ├── calculators.py
│   ├── sheets.py
│   ├── youtube.py
│   └── web_search.py
├── app.py           # NiceGUI frontend
├── config.py        # Settings
├── llm.py           # Provider abstraction
└── rag.py           # Vector store (ChromaDB)
```

## Tech Stack

| Component       | Technology      |
| --------------- | --------------- |
| Orchestration   | LangGraph       |
| LLM             | Ollama / Gemini |
| Embeddings      | Ollama / Gemini |
| Vector Store    | ChromaDB        |
| UI              | NiceGUI         |
| Package Manager | uv              |

## Development

```bash
# Run tests
uv run pytest

# Restart server
.\restart.ps1
```

---

_Built by [Boldizsár Nagy](https://www.linkedin.com/in/boldizsarnagy/)_
