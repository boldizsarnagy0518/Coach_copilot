# 📋 Code Review Log

> **Purpose:** This file is used by the Reviewer Agent to provide feedback on code changes.
> The Coder Agent reads this file before making changes to address any pending feedback.

---

## 🔄 Current Status

**Status:** `APPROVED`

<!-- Status options: AWAITING_CHANGES | REVIEW_IN_PROGRESS | APPROVED | NEEDS_REVISION -->

---

## 📝 Review Template

<!--
Reviewer Agent: Copy this template for each review session.
Delete this section once reviews begin.

## Review - [YYYY-MM-DD HH:MM]

### Files Reviewed
- `path/to/file.py`

### 🔴 Critical Issues
> Issues that must be fixed before approval

- **File:** `filename.py:L##`
- **Issue:** Description of the problem
- **Suggestion:** How to fix it

### 🟡 Warnings
> Potential problems or code smells

- **File:** `filename.py:L##`
- **Issue:** Description
- **Suggestion:** Recommended fix

### 🟢 Suggestions
> Nice-to-have improvements

- **File:** `filename.py:L##`
- **Suggestion:** Improvement idea

### ✅ Approved Items
> Things that look good

- List of approved changes/files

### 📌 Notes for Coder
> Any additional context or questions

---
-->

## 📜 Review History

<!-- Reviews will be added below this line -->

## Review - 2025-12-31 04:20

### ✅ Approved Items

- **File:** `src/agent/graph.py:L23-33`
- **Resolution:** Fixed tool counting logic. Now correctly counts tool calls only for the current turn (since last `HumanMessage`).

- **File:** `Plan.md:L64-70`
- **Resolution:** Hungarian text translated to English. "Classify prompt" note formalized.

### 🟢 Suggestion

- **File:** `src/agent/nodes.py`
- **Suggestion:** The `_extract_text` helper correctly handles the list content format for Gemini 3.0. Good implementation.

---

## Review - 2025-12-31 05:08

### ✅ Approved Items

- **Feature:** Query Reformulation Agent
- **Files:** `src/agent/graph.py`, `src/agent/nodes.py`, `src/agent/state.py`
- **Resolution:** Implemented `reformulate_query` node and updated graph state. Correctly integrated into the workflow start.

- **Feature:** LangFuse Monitoring
- **File:** `src/llm.py`
- **Resolution:** Implemented lazy loading for LangFuse callbacks. Correctly attached to both standard and fast LLMs.

- **Feature:** RAG Scoring
- **File:** `src/rag.py`
- **Resolution:** Implemented `search_with_scores` retrieving top 5 documents based on relevance score.

- **Feature:** Prompt Improvements & Error Handling
- **File:** `src/agent/nodes.py`
- **Resolution:** Renamed `greeting` to `small_talk` for clarity. specific error handling added to key nodes.

- **File:** `Plan.md`
- **Resolution:** Updated status of all implemented features.

- **Feature:** Prompt Management
- **Files:** `src/prompts/`, `src/agent/nodes.py`
- **Resolution:** Created `src/prompts/` with external text files. `load_prompt` utility implemented and integrated into `nodes.py`.

- **Feature:** UI & UX Enhancements (Thinking, Sessions, Sources)
- **Files:** `src/app.py`, `src/rag.py`
- **Resolution:**

  - **Thinking Display:** Implemented collapsible `ui.expansion` showing reasoning steps in `app.py`.
  - **Chat Sessions:** Implemented session persistence, sidebar history, and load/delete functionality.
  - **Clickable Links:** Source metadata added to RAG context in `formatting_scored_results`.

- **Feature:** Infrastructure & Testing
- **Files:** `pyproject.toml`, `tests/`, `restart.ps1`
- **Resolution:**

  - **Dependencies:** Updated `pyproject.toml` with testing and observability libs.
  - **Tests:** Added comprehensive unit tests for RAG loaders and robust `conftest.py` fixtures.
  - **Scripts:** Added `restart.ps1` for easy dev iteration.

- **Feature:** YouTube Tool
- **File:** `src/tools/youtube.py`
- **Resolution:** Implemented transcript loading and channel info tools with proper error handling.

- **Feature:** Web Search & Tools
- **Files:** `src/tools/web_search.py`, `src/tools/__init__.py`
- **Resolution:** Implemented `search_web`, `crawl_url`, and `competition_countdown`. All tools correctly exported and integrated.

### 🟢 Suggestion

- **File:** `src/agent/nodes.py` vs `src/prompts/grade.txt`
- **Issue:** `grade_documents` node uses an inline prompt string for Instructor, while `grade.txt` exists but appears unused for this specific node.
- **Suggestion:** Consolidate to use `load_prompt("grade")` if possible, or delete `grade.txt` if the inline prompt is preferred for structured output models.

- **Feature:** PydanticAI Integration
- **Files:** `src/agent/reformulate_agent.py`, `src/agent/nodes.py`
- **Resolution:** Implemented `reformulate_agent` using PydanticAI with `run_sync`. Replaced previous LangChain implementation in `reformulate_query` node.

- **Feature:** Documentation
- **File:** `Architecture.md`
- **Resolution:** Updated tech stack and file structure to include PydanticAI and new agent files.

---

## Review - 2025-12-31 09:44

### ✅ Approved Items

- **Feature:** UI Welcome Screen Centering
- **File:** `src/app.py`
- **Resolution:** Fixed horizontal misalignment between welcome screen and input area. Root cause was `msg-container` missing `w-full` class, causing it to shrink to content width (964px) instead of spanning full width (1559px) like `input-wrapper`. Added `w-full` class to ensure both containers have identical centering behavior.

- **Feature:** DevTools-Assisted Debugging
- **Resolution:** Used browser subagent with JavaScript execution to measure exact pixel positions and identify the misalignment (~145 unit offset). This approach proved essential for diagnosing framework-level CSS conflicts.

- **Feature:** Layout Refinements
- **File:** `src/app.py`
- **Resolution:**
  - Reduced `chat-area` max-width from 95% to 85% for more black space on the right edge.
  - Standardized padding between `msg-container` and `input-wrapper` (both use `2rem`).
  - Applied multiple centering strategies: CSS `!important` overrides, Quasar utility classes, and inline styles.

### 🟢 Suggestions

- **File:** `src/app.py`
- **Suggestion:** Consider extracting CSS styles into a separate `.css` file for better maintainability. The current inline CSS in `add_styles()` function is over 100 lines.

- **File:** `src/app.py`
- **Suggestion:** The welcome screen structure was refactored multiple times. Consider adding a comment explaining why `w-full` is required on `msg-container` to prevent future regressions.

---

## Review - 2025-12-31 09:55

### ✅ Approved Items

- **Feature:** Instructor Client Caching
- **File:** `src/utils/instructor_client.py`
- **Resolution:** Added singleton pattern to cache the Instructor client, avoiding recreation on every call.

- **Feature:** PydanticAI Lazy Initialization
- **File:** `src/agent/reformulate_agent.py`
- **Resolution:** Refactored to use lazy initialization with explicit OpenAI client configuration. Removed global `os.environ` modification at import time, improving thread-safety and avoiding side effects.

- **Feature:** Real-time Chain of Thought
- **Files:** `src/agent/runner.py`, `src/app.py`
- **Resolution:** Added `on_step` callback to chat function for real-time UI updates. Thinking label now shows current step (e.g., "Understanding query...", "Searching documents...") instead of static "Thinking...".

- **Feature:** Enhanced Few-Shot Prompting
- **Files:** `src/agent/nodes.py`, `src/prompts/grade.txt`
- **Resolution:** Expanded classify prompt from 5 to 17 examples including Hungarian greetings and edge cases. Added 3 concrete examples to grade prompt for yes/no decisions.

- **Feature:** Message Alignment
- **File:** `src/app.py`
- **Resolution:** Bot messages now align left (`align-self: flex-start`), user messages align right (`align-self: flex-end`). Removed emojis from CoT display per user request.

---

_Last updated: 2025-12-31 10:00_

---

## Review - 2025-12-31 10:00

### ✅ Approved Items

- **Feature:** Performance & Refactoring
- **Files:** `src/agent/nodes.py`, `src/utils/instructor_client.py`, `src/config.py`
- **Resolution:**

  - **Singleton Pattern:** `instructor_client` is now a singleton.
  - **Prompt Consistency:** `grade_documents` successfully integrates `GRADE_PROMPT` constant.
  - **Refactoring:** `config.py` remains clean and type-safe.

- **Feature:** Documentation
- **File:** `Plan.md`
- **Resolution:** Updated "Implemented" section with "Lazy Initialization", "Real-time Status", and other recent features.

---

## Review - 2026-01-03 03:15

### ✅ Approved Items

- **Feature:** YouTube Data API Integration
- **Files:** `src/tools/youtube.py`, `src/config.py`
- **Resolution:**
  - Added 3 new tools: `search_channel_videos`, `get_video_details`, `list_channel_playlists`.
  - Lazy initialization of YouTube API client.
  - Graceful fallback to URL-based suggestions when API key is missing.
  - Config updated with `youtube_api_key` and `youtube_channel_id` fields.

---

## 📋 Implementation Plan for Coder Agent

### Feature: Agent Unit Tests

**Priority:** High  
**Estimated Effort:** Medium

#### Objective

Add comprehensive unit tests for the agent nodes in `src/agent/nodes.py` to ensure classification, reformulation, and grading logic is testable and reliable.

#### Files to Create/Modify

1. **[NEW] `tests/unit/test_agents.py`**

   - Test `classify_input` with mocked Instructor client
   - Test `reformulate_query` with mocked PydanticAI agent
   - Test `grade_documents` with mocked responses
   - Test heuristic small_talk detection (no mocking needed)

2. **[MODIFY] `tests/conftest.py`**
   - Add fixture for mocked `instructor_client`
   - Add fixture for mocked `reformulate_agent`

#### Test Cases

```python
# classify_input tests
- test_classify_small_talk_heuristic()  # "hello", "hi", "thanks"
- test_classify_command_with_my()        # "What is my PR?"
- test_classify_question_general()       # "What is RPE?"
- test_classify_fallback_on_error()      # Instructor fails → defaults to command

# reformulate_query tests
- test_reformulate_clear_input_unchanged()  # "Hello!" → unchanged
- test_reformulate_ambiguous_input()        # "that thing" → clarification
- test_reformulate_error_fallback()         # PydanticAI fails → original input

# grade_documents tests
- test_grade_relevant_documents()    # Returns yes
- test_grade_irrelevant_documents()  # Returns no
- test_grade_empty_context()         # Skips grading, returns web_search_needed=True
```

#### Acceptance Criteria

- [ ] All tests pass with `pytest tests/unit/test_agents.py`
- [ ] No external API calls (fully mocked)
- [ ] Coverage for error fallback paths

---

### Feature: Prompt Refinement (CoT + Clarification)

**Priority:** High  
**Estimated Effort:** Low

#### Objective

Add chain-of-thought reasoning and conditional clarification to improve response quality without making the agent overly chatty.

#### Files to Modify

1. **`src/prompts/system.txt`**

   ```diff
   + When answering complex questions, think through the problem step by step.
   + If critical information is missing, ask ONE clarifying question before proceeding.
   + Never ask questions for simple requests like greetings or calculations.
   ```

2. **`src/prompts/plan.txt`**

   ```diff
   + Break down the user's request into clear, numbered steps before retrieving information.
   ```

3. **`src/prompts/grade.txt`**
   ```diff
   + Think step by step: Does this document help answer the user's specific question?
   ```

#### Acceptance Criteria

- [ ] Prompts updated in `src/prompts/`
- [ ] No regression in classification speed (heuristics still work)
- [ ] Manual test: Complex question triggers step-by-step reasoning

---

### Feature: RPE Logger Tool

**Priority:** Medium  
**Estimated Effort:** Medium (increased due to DuckDB)

#### Objective

Create a tool that logs Rate of Perceived Exertion (RPE) after sets, using DuckDB for fast analytics with optional Google Sheets sync for user visibility.

#### Architecture

```
User Input → log_rpe() → DuckDB (primary) → [optional] Sheets Sync
                              ↓
                      get_rpe_trends() → SQL aggregations
```

#### Files to Create/Modify

1. **[NEW] `src/db/__init__.py`**

   - DuckDB connection manager (singleton)
   - Schema initialization on first run

2. **[NEW] `src/db/models.py`**

   ```python
   # DuckDB tables
   RPE_LOGS = """
   CREATE TABLE IF NOT EXISTS rpe_logs (
       id INTEGER PRIMARY KEY,
       athlete_id TEXT,
       exercise TEXT,
       weight FLOAT,
       reps INTEGER,
       rpe FLOAT,
       notes TEXT,
       logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
   """
   ```

3. **[NEW] `src/tools/rpe_logger.py`**

   - `log_rpe(exercise, weight, reps, rpe, notes) -> str` - Insert to DuckDB
   - `get_rpe_trends(exercise, days=7) -> str` - Weekly averages via SQL
   - `sync_rpe_to_sheets() -> str` - Optional batch export

4. **[MODIFY] `src/tools/__init__.py`**

   - Import and add RPE tools to `ALL_TOOLS`

5. **[MODIFY] `pyproject.toml`**
   - Add `duckdb>=1.0.0` dependency

#### Pydantic Schema

```python
class RPELogInput(BaseModel):
    exercise: str = Field(description="Exercise name (squat, bench, deadlift)")
    weight: float = Field(description="Weight in kg")
    reps: int = Field(description="Number of reps")
    rpe: float = Field(ge=1, le=10, description="RPE scale 1-10")
    notes: str = Field(default="", description="Optional notes")
```

#### Acceptance Criteria

- [ ] DuckDB table created on first run
- [ ] `log_rpe` inserts record in <10ms
- [ ] `get_rpe_trends` returns weekly averages
- [ ] Optional Sheets sync works when API configured

---

### Feature: Meet Results Tracker

**Priority:** Medium  
**Estimated Effort:** Medium

#### Objective

Store competition results in DuckDB for fast PR calculations and historical analysis, with optional Sheets export.

#### Architecture

```
User Input → record_meet() → DuckDB → PR calculations (SQL)
                                 ↓
                        [optional] Sheets export to "Meet Results" tab
```

#### Files to Create/Modify

1. **[MODIFY] `src/db/models.py`**

   ```python
   MEET_RESULTS = """
   CREATE TABLE IF NOT EXISTS meet_results (
       id INTEGER PRIMARY KEY,
       athlete_id TEXT,
       meet_name TEXT,
       meet_date DATE,
       weight_class TEXT,
       squat FLOAT,
       bench FLOAT,
       deadlift FLOAT,
       total FLOAT,
       placing INTEGER,
       notes TEXT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
   """
   ```

2. **[NEW] `src/tools/meet_tracker.py`**

   - `record_meet_result(meet_name, date, squat, bench, deadlift, weight_class, placing) -> str`
   - `get_pr_history(lift: str) -> str` - Returns PR progression via SQL
   - `compare_to_pr(lift: str) -> str` - Compares current training to all-time PR
   - `export_meets_to_sheets() -> str` - Batch export to Google Sheets

3. **[MODIFY] `src/config.py`**
   - Add `duckdb_path: Path = Path("./data/coach.duckdb")`

#### Acceptance Criteria

- [ ] Meet results stored in DuckDB
- [ ] `get_pr_history` correctly identifies PRs per lift
- [ ] `compare_to_pr` shows % of PR
- [ ] Optional Sheets export creates "Meet Results" tab

---

## 🔧 Production-Ready Recommendations

### Critical for Production

| Category             | Recommendation                                                     | Files                                         |
| -------------------- | ------------------------------------------------------------------ | --------------------------------------------- |
| **Error Boundaries** | Wrap all tool calls in try/except with user-friendly messages      | `src/agent/nodes.py`                          |
| **Rate Limiting**    | Add rate limiter for YouTube/Google APIs to avoid quota exhaustion | `src/tools/youtube.py`, `src/tools/sheets.py` |
| **Input Validation** | Validate all user inputs before LLM processing                     | `src/agent/nodes.py`                          |
| **Timeout Handling** | Add timeouts to LLM calls (prevent hanging on slow Ollama)         | `src/llm.py`                                  |
| **Logging**          | Replace `print()` with structured logging (JSON format)            | All files                                     |

### Tests to Add for Production

```python
# tests/unit/test_tools.py
- test_log_rpe_validation()         # RPE must be 1-10
- test_log_rpe_sheets_error()       # Graceful handling when Sheets unavailable
- test_meet_result_parsing()        # Various input formats
- test_pr_calculation()             # Correctly identifies PRs

# tests/integration/test_agent_flow.py
- test_full_rag_pipeline()          # Query → Retrieve → Grade → Generate
- test_tool_calling_circuit()       # Verify tool limit (max 3 per turn)
- test_session_persistence()        # Chat history survives reload

# tests/e2e/test_ui.py (browser-based)
- test_login_flow()                 # PIN authentication
- test_chat_session_switching()     # Create, switch, delete sessions
- test_file_upload()                # PDF processing
```

### Monitoring & Observability

1. **LangFuse Dashboards** (already integrated)

   - Track latency per node (reformulate, classify, retrieve, generate)
   - Monitor token usage and cost
   - Set alerts for error rate > 5%

2. **Health Endpoint** (to add)
   ```python
   # src/app.py
   @app.get("/health")
   def health():
       return {"status": "ok", "llm": check_ollama(), "sheets": check_sheets()}
   ```

### Security Considerations

- [ ] Sanitize user input before passing to LLM (prompt injection prevention)
- [ ] Validate file uploads (size limit, allowed types)
- [ ] Rate limit API endpoints
- [ ] Audit log for Google Sheets modifications

---

_Last updated: 2026-01-03 03:35_
