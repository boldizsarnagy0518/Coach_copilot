import pytest
from unittest.mock import MagicMock, patch
from src.agent.state import AgentState
from src.agent.nodes import classify_input, reformulate_query, grade_documents
from src.agent.reformulate_agent import ReformulationResult


@pytest.fixture
def mock_state():
    return AgentState(input="test input")


def test_classify_heuristic_greeting(mock_state):
    """Test fast path for greetings."""
    mock_state.input = "Hello there"
    result = classify_input(mock_state)
    assert result["input_type"] == "small_talk"


@patch("src.agent.nodes.get_instructor_client")
def test_classify_llm_call(mock_client_getter, mock_state):
    """Test LLM classification (Instructor) fallback."""
    mock_state.input = "Calculate 1RM"

    # Mock the client.chat.completions.create return value
    mock_client = MagicMock()
    mock_client_getter.return_value = mock_client

    mock_response = MagicMock()
    # The return value from Instructor is a Pydantic model instance, we mimic it
    mock_response.input_type = "command"
    mock_client.chat.completions.create.return_value = mock_response

    result = classify_input(mock_state)
    assert result["input_type"] == "command"


@patch("src.agent.nodes.reformulate_agent")
def test_reformulate_query(mock_agent, mock_state):
    """Test reformulation agent call (PydanticAI)."""
    mock_state.input = "that thing"

    # Mock PydanticAI RunResult
    mock_result = MagicMock()
    mock_result.data = ReformulationResult(reformulated="bench press", was_changed=True)
    mock_agent.run_sync.return_value = mock_result

    result = reformulate_query(mock_state)
    assert result["reformulated_input"] == "bench press"


@patch("src.agent.nodes.get_instructor_client")
def test_grade_documents_relevant(mock_client_getter, mock_state):
    """Test grading relevant docs (Instructor)."""
    mock_state.context = "Squat depth rules..."
    mock_state.input = "How deep to squat?"

    mock_client = MagicMock()
    mock_client_getter.return_value = mock_client

    # Mock Grade response
    mock_response = MagicMock()
    mock_response.score = "yes"
    mock_client.chat.completions.create.return_value = mock_response

    result = grade_documents(mock_state)
    assert result["web_search_needed"] is False


@patch("src.agent.nodes.get_instructor_client")
def test_grade_documents_irrelevant(mock_client_getter, mock_state):
    """Test grading irrelevant docs."""
    mock_state.context = "Soup recipes..."
    mock_state.input = "How deep to squat?"

    mock_client = MagicMock()
    mock_client_getter.return_value = mock_client

    mock_response = MagicMock()
    mock_response.score = "no"
    mock_client.chat.completions.create.return_value = mock_response

    result = grade_documents(mock_state)
    assert result["web_search_needed"] is True
