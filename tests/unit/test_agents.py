"""
Unit tests for the LangGraph agent system.

Tests intent classification, node functions, and graph flow.
"""


from src.agents.state import AgentState, IntentType, create_initial_state
from src.agents.nodes.analyzer import analyze_intent, classify_intent
from src.agents.nodes.action import (
    execute_tools,
    parse_e1rm_request,
    parse_plates_request,
    parse_wilks_request,
)


class TestIntentClassification:
    """Tests for intent classification."""

    def test_classify_e1rm_keywords(self):
        """E1RM related queries should be mathematical."""
        assert classify_intent("Calculate my E1RM") == IntentType.MATHEMATICAL
        assert classify_intent("What's my 1RM?") == IntentType.MATHEMATICAL
        assert classify_intent("one rep max for 100kg") == IntentType.MATHEMATICAL

    def test_classify_weight_with_reps(self):
        """Weight x reps patterns should be mathematical."""
        assert classify_intent("140kg for 5 reps") == IntentType.MATHEMATICAL
        assert classify_intent("5x100kg") == IntentType.MATHEMATICAL
        assert classify_intent("100 x 5") == IntentType.MATHEMATICAL

    def test_classify_wilks(self):
        """Wilks queries should be mathematical."""
        assert classify_intent("Calculate my Wilks score") == IntentType.MATHEMATICAL
        assert classify_intent("What's my Wilks?") == IntentType.MATHEMATICAL

    def test_classify_plates(self):
        """Plate loading queries should be mathematical."""
        assert classify_intent("What plates for 140kg?") == IntentType.MATHEMATICAL
        assert classify_intent("Load the bar to 180kg") == IntentType.MATHEMATICAL

    def test_classify_ipf_rules(self):
        """IPF rule questions should be instructional."""
        assert classify_intent("What is the IPF squat depth rule?") == IntentType.INSTRUCTIONAL
        assert classify_intent("Is this lift legal?") == IntentType.INSTRUCTIONAL

    def test_classify_technique(self):
        """Technique questions should be instructional."""
        assert classify_intent("How do I fix squat depth?") == IntentType.INSTRUCTIONAL
        assert classify_intent("What cue should I use for bench?") == IntentType.INSTRUCTIONAL

    def test_classify_schedule(self):
        """Schedule questions should be administrative."""
        assert classify_intent("Reschedule my training") == IntentType.ADMINISTRATIVE
        assert classify_intent("Update my plan for next week") == IntentType.ADMINISTRATIVE

    def test_classify_greetings(self):
        """Greetings should be conversational."""
        assert classify_intent("Hello!") == IntentType.CONVERSATIONAL
        assert classify_intent("Hi coach") == IntentType.CONVERSATIONAL
        assert classify_intent("Thanks for the help") == IntentType.CONVERSATIONAL


class TestAnalyzerNode:
    """Tests for the analyzer node."""

    def test_analyzer_returns_intent(self):
        """Analyzer should return intent in state update."""
        state: AgentState = create_initial_state("Calculate E1RM for 100kg x 5")
        result = analyze_intent(state)

        assert "intent" in result
        assert result["intent"] == IntentType.MATHEMATICAL

    def test_analyzer_handles_empty_input(self):
        """Analyzer should handle empty input gracefully."""
        state: AgentState = {
            "messages": [],
            "user_input": "",
            "intent": None,
            "context": None,
            "context_sources": None,
            "tool_results": None,
            "response": None,
            "error": None,
        }
        result = analyze_intent(state)

        assert result["intent"] == IntentType.UNKNOWN
        assert "error" in result


class TestParameterParsing:
    """Tests for parameter parsing functions."""

    def test_parse_e1rm_weight_for_reps(self):
        """Parse 'weight for reps' format."""
        result = parse_e1rm_request("100kg for 5 reps")
        assert result == {"weight": 100.0, "reps": 5}

    def test_parse_e1rm_weight_x_reps(self):
        """Parse 'weight x reps' format."""
        result = parse_e1rm_request("140 x 3")
        assert result == {"weight": 140.0, "reps": 3}

    def test_parse_e1rm_reps_at_weight(self):
        """Parse 'reps @ weight' format."""
        result = parse_e1rm_request("5 reps @ 120kg")
        assert result == {"weight": 120.0, "reps": 5}

    def test_parse_wilks_with_total_and_bw(self):
        """Parse Wilks request with total and bodyweight."""
        result = parse_wilks_request("Wilks for 600kg total at 83kg male")
        assert result is not None
        assert result["total"] == 600.0
        assert result["bodyweight"] == 83.0
        assert result["gender"] == "male"

    def test_parse_plates_basic(self):
        """Parse basic plate request."""
        result = parse_plates_request("What plates for 140kg?")
        assert result == {"target_weight": 140.0}

    def test_parse_plates_load_format(self):
        """Parse 'load X' format."""
        result = parse_plates_request("Load 180kg on the bar")
        assert result == {"target_weight": 180.0}


class TestActionNode:
    """Tests for the action (tool execution) node."""

    def test_execute_e1rm_tool(self):
        """Action node should execute E1RM calculation."""
        state: AgentState = {
            "messages": [],
            "user_input": "Calculate E1RM for 140kg x 5",
            "intent": IntentType.MATHEMATICAL,
            "context": None,
            "context_sources": None,
            "tool_results": None,
            "response": None,
            "error": None,
        }
        result = execute_tools(state)

        assert "tool_results" in result
        assert result["tool_results"] is not None
        assert len(result["tool_results"]) > 0
        assert result["tool_results"][0]["tool"] == "e1rm"

    def test_execute_plates_tool(self):
        """Action node should execute plate calculation."""
        state: AgentState = {
            "messages": [],
            "user_input": "What plates for 180kg?",
            "intent": IntentType.MATHEMATICAL,
            "context": None,
            "context_sources": None,
            "tool_results": None,
            "response": None,
            "error": None,
        }
        result = execute_tools(state)

        assert "tool_results" in result
        assert result["tool_results"] is not None
        assert result["tool_results"][0]["tool"] == "plates"

    def test_skip_tools_for_non_math_intent(self):
        """Action node should skip tools for non-mathematical intents."""
        state: AgentState = {
            "messages": [],
            "user_input": "What is the squat depth rule?",
            "intent": IntentType.INSTRUCTIONAL,
            "context": None,
            "context_sources": None,
            "tool_results": None,
            "response": None,
            "error": None,
        }
        result = execute_tools(state)

        assert result["tool_results"] is None


class TestAgentState:
    """Tests for agent state utilities."""

    def test_create_initial_state(self):
        """Initial state should have all fields with defaults."""
        state = create_initial_state("Test input")

        assert state["user_input"] == "Test input"
        assert state["intent"] is None
        assert state["context"] is None
        assert state["response"] is None
        assert state["messages"] == []

    def test_intent_type_enum(self):
        """IntentType should have all expected values."""
        assert IntentType.INSTRUCTIONAL.value == "instructional"
        assert IntentType.MATHEMATICAL.value == "mathematical"
        assert IntentType.ADMINISTRATIVE.value == "administrative"
        assert IntentType.CONVERSATIONAL.value == "conversational"
