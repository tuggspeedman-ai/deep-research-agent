# PLAN Archive — LangChain Deep Agents

Completed milestone details, preserved for historical context. Active work tracked in `PLAN.md`.

---

## M0: Project Setup ✅ COMPLETE

**Result:** Python project initialized with uv. Gemma 4 26B running via Ollama v0.20.2. Basic response and tool calling smoke tests pass. Course materials downloaded for reference.

### Tasks
- [x] Initialize Python project with uv (`pyproject.toml`)
- [x] Install core dependencies: `langgraph`, `langchain`, `langchain-ollama`, `pytest`, `ruff`
- [x] Install and start Ollama, pull Gemma 4 26B (Q4_K_M, 17GB)
- [x] Write a smoke test: `ChatOllama` → Gemma 4 → get a response
- [x] Write a tool-calling smoke test: bind a simple tool, verify Gemma 4 calls it
- [x] Set up pytest config and ruff config in `pyproject.toml`
- [x] Create `.env.example` with Ollama and LangSmith config
- [x] Set up GitHub repo (tuggspeedman-ai/deep-research-agent)
- [x] Download course materials (notebooks, transcript, setup notes) into gitignored `course-materials/`

### Key Files Created
- `pyproject.toml` — project config, deps, ruff + pytest settings
- `tests/test_smoke.py` — basic response + tool calling smoke tests
- `.env.example` — environment variable template
- `course-materials/` — reference notebooks + transcript (gitignored)

---

## M1: ReAct Agent Foundation ✅ COMPLETE

**Result:** ReAct agent using `create_agent` with Gemma 4 26B. Demonstrates all four key LangGraph patterns: custom state schema, InjectedState, Command, InjectedToolCallId. Structured output and parallel tool calls verified. 9 tests pass, ruff clean.

### Tasks
- [x] Create a ReAct agent with `create_agent` and Gemma 4
- [x] Add a custom state schema (`CalcState`) extending `AgentState` with `reduce_list` reducer
- [x] Implement a tool using `InjectedState` to read graph state (`get_history`)
- [x] Implement a tool returning `Command` to update state directly (`calculator`)
- [x] Verify structured output (`.with_structured_output()`) works with Gemma 4
- [x] Test parallel tool calls in a single response (2 tools called simultaneously)
- [x] Write tests for the agent loop (5 agent tests + 2 capability tests)

### Key Files Created
- `src/agent.py` — ReAct agent with calculator + history tools, custom state, Command pattern
- `tests/test_agent.py` — 7 tests: single calc, multi-step, history, div-by-zero, state accumulation, structured output, parallel tool calls

### Notable Findings
- `create_agent` is in `langchain.agents` (the 1.0 API), not `langgraph.prebuilt`
- Structured output mechanism works but Gemma 4 can hallucinate values — test the mechanism, not model correctness
- Parallel tool calls work reliably with Gemma 4 via Ollama v0.20.2

---

## M2: Task Planning (TODOs) ✅ COMPLETE

**Result:** DeepAgentState with todos field, write_todos/read_todos tools, and TODO workflow prompts. Agent plans with TODOs, executes via mock web search, and updates progress. 6 new tests (3 unit + 3 integration), 15/15 total passing.

### Design Decisions
- **`todos` only** — no `files` field until M3. No over-engineering
- **No reducer on `todos`** — full overwrite semantics. LLM rewrites the entire list each call (Manus/Claude Code pattern)
- **Mock `web_search`** — canned MCP response. Real search comes in M5, avoids API keys now
- **`read_todos` returns `str`** — simpler than Command when no state update needed (LangGraph auto-wraps as ToolMessage)
- **Recursion limit 30** — TODO loop needs more tool-call steps than M1's calculator (20)
- **M1 untouched** — calc agent stays as-is. M2 starts the "deep agent" lineage (M2→M5)

### Tasks
- [x] `src/state.py` — `Todo` TypedDict + `DeepAgentState` with `todos` field
- [x] `src/prompts.py` — tool descriptions + TODO workflow instructions
- [x] `src/todo_tools.py` — `write_todos` (Command return) + `read_todos` (str return)
- [x] `src/deep_agent.py` — mock web search + `create_deep_agent()` factory
- [x] `tests/test_todo.py` — unit tests (tool mechanics) + integration tests (agent behavior)
- [x] Run all tests (M1 + M2), verify everything passes — 15/15 pass

### Key Files Created
- `src/state.py` — `Todo` TypedDict + `DeepAgentState(AgentState)` with `todos` field
- `src/prompts.py` — `WRITE_TODOS_DESCRIPTION`, `TODO_USAGE_INSTRUCTIONS`, `SIMPLE_RESEARCH_INSTRUCTIONS`
- `src/todo_tools.py` — `write_todos` (→ Command) + `read_todos` (→ str)
- `src/deep_agent.py` — `mock_web_search` tool + `create_deep_agent()` factory
- `tests/test_todo.py` — 3 unit tests + 3 integration tests

### Notable Findings
- Tools with `InjectedToolCallId` require full ToolCall dict format (`{name, args, type, id}`) when invoked directly in tests — plain dict invocation raises ValueError
- `read_todos` returning `str` vs `Command`: when a `@tool` returns a plain string, LangGraph auto-wraps it as a ToolMessage. Use `str` when no state update needed, `Command` when you need to mutate state
- Gemma 4 follows the TODO workflow reliably with explicit prompting (plan → work → read → reflect → update)
