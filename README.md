# Coach Copilot 🏋️

AI-powered Powerlifting Coach Assistant with RAG and LangGraph.

## Features

- **E1RM Calculator**: Estimate your 1 rep max using multiple formulas (Epley, Brzycki, etc.)
- **Wilks & IPF GL Scoring**: Compare lifters across weight classes
- **Plate Calculator**: Know exactly what plates to load
- **RAG-powered Knowledge**: Access IPF rules and coaching notes
- **YouTube Integration**: Search your tutorial transcripts
- **Google Sheets**: Read and write training logs

## Tech Stack

| Component | Technology |
|-----------|------------|
| Package Manager | UV |
| Orchestration | LangGraph |
| Vector Store | ChromaDB |
| LLM (Local) | Ollama |
| LLM (API) | Gemini 2.0 |
| Frontend | NiceGUI + FastAPI |

## Quick Start

### Prerequisites

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) (package manager)
- [Ollama](https://ollama.ai) (for local LLM)

### Installation

```bash
# Install dependencies
uv sync

# Copy environment template
cp .env.example .env

# Pull Ollama model (for development)
ollama pull llama3.2
```

### Configuration

Edit `.env` to configure your LLM provider:

```bash
# Development (local, free)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2

# Production (API)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Running the Application

```bash
# Start the UI
uv run coach
```

## Project Structure

```
Coach_copilot/
├── src/
│   ├── core/       # Configuration & settings
│   ├── llm/        # LLM provider abstraction
│   ├── tools/      # Powerlifting calculators
│   ├── rag/        # RAG system (ChromaDB)
│   ├── agents/     # LangGraph workflows
│   └── ui/         # NiceGUI frontend
├── tests/          # Unit & integration tests
├── data/           # PDFs, notes, vector store
└── docs/           # Documentation
```

## Calculator Examples

```python
from src.tools import calculate_e1rm, calculate_wilks, calculate_plates

# E1RM from 5 reps
result = calculate_e1rm(weight=140, reps=5)
print(result)  # E1RM: 163.33kg

# Wilks score
wilks = calculate_wilks(total=600, bodyweight=83, gender="male")
print(wilks)  # Wilks: 388.xx

# Plate loading
plates = calculate_plates(target_weight=180)
print(plates)  # Load: 2×20kg, 1×10kg, 1×5kg per side
```

## Documentation

See the `Architecture.md` for detailed system design and the `context.md` files in each module for implementation details.

## License

MIT
