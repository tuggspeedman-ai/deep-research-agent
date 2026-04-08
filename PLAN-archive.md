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

---

## M3: Virtual File System & Context Offloading ✅ COMPLETE

**Result:** Virtual filesystem stored as `dict[str, str]` in DeepAgentState with merge reducer. Three tools (`ls`, `read_file`, `write_file`) for context offloading. System prompt includes `FILE_USAGE_INSTRUCTIONS` for orient→save→research→read workflow. 13 new tests, 28 total passing.

### Design Decisions
- **Merge reducer on `files`** — unlike todos (full-overwrite), files use `file_reducer` that merges dicts with `{**left, **right}`. This means `write_file` only sends `{path: content}` and the reducer handles merging into existing files
- **`write_file` skips `InjectedState`** — the course version reads existing files from state and rebuilds the full dict manually. Our reducer makes this unnecessary, simpler implementation
- **No physical files** — the "filesystem" is purely in-memory, keys are arbitrary strings that look like paths. No directory structure, no disk I/O
- **`read_file` pagination** — offset/limit support with `cat -n` style line numbering, 2000 char line truncation. Negative offset/limit clamped to 0

### Tasks
- [x] `src/state.py` — `file_reducer` function + `files` field on `DeepAgentState`
- [x] `src/file_tools.py` — `ls` (→ list), `read_file` (→ str), `write_file` (→ Command)
- [x] `src/prompts.py` — `LS_DESCRIPTION`, `READ_FILE_DESCRIPTION`, `WRITE_FILE_DESCRIPTION`, `FILE_USAGE_INSTRUCTIONS`
- [x] `src/deep_agent.py` — wired file tools into TOOLS list + system prompt
- [x] `tests/test_files.py` — 12 unit tests + 1 integration test
- [x] All 28 tests pass (no regressions)

### Key Files Created/Modified
- `src/state.py` — added `file_reducer`, `files` field
- `src/file_tools.py` — **new** — three file tools
- `src/prompts.py` — added 4 prompt constants
- `src/deep_agent.py` — extended TOOLS and system prompt
- `tests/test_files.py` — **new** — 13 tests

### Notable Findings
- Tools returning `list` (like `ls`) get auto-wrapped as `ToolMessage` by LangGraph — tests need to extract `.content`
- Merge reducer eliminates need for `InjectedState` in `write_file` — a genuine simplification over the course reference
- `FILE_USAGE_INSTRUCTIONS` nudges the LLM to use files proactively, but Gemma 4 follows inconsistently unless explicitly asked

---

## M4: Sub-agent Delegation ✅ COMPLETE

**Result:** Sub-agent delegation with context isolation. `_create_task_tool()` factory spawns sub-agents with fresh message history but shared virtual file system. `SubAgent` TypedDict config, `think_tool` for structured reflection, supervisor prompt with delegation scaling rules. 11 new tests (9 unit + 2 integration), 39 total passing.

### Design Decisions
- **Context isolation via message reset** — `state["messages"] = [{"role": "user", "content": description}]` gives sub-agents fresh context while preserving shared file system through `file_reducer`
- **`SubAgent` is a TypedDict** — `name`, `description`, `prompt`, `tools: NotRequired[list[str]]`. Matches course pattern exactly
- **`_create_task_tool()` factory** — builds agent registry at init time, returns a `task` tool with `InjectedState` + `InjectedToolCallId`
- **`think_tool` is stateless** — takes reflection string, returns confirmation. No `Command`, no state changes. Gives the LLM a scratchpad
- **Default sub-agent uses mock search** — real Tavily search deferred to M5
- **Recursion limit raised to 50** — sub-agent delegation adds depth (supervisor + sub-agent each consume steps)

### Tasks
- [x] T1: Create `src/think_tool.py` — stateless `think_tool(reflection) -> str`
- [x] T2: Add `TASK_DESCRIPTION_PREFIX` and `SUBAGENT_USAGE_INSTRUCTIONS` to `src/prompts.py`
- [x] T3: Create `src/task_tool.py` — `SubAgent` TypedDict + `_create_task_tool()` factory
- [x] T4: Update `src/deep_agent.py` — integrate task/think tools, define default research sub-agent
- [x] T5: Create `tests/test_task.py` — unit tests (think_tool, task tool isolation, error handling)
- [x] T6: Add integration tests — supervisor delegates, sub-agent file writes visible
- [x] T7: Run full test suite, verify 28+ existing tests still pass + new tests

### Key Files Created/Modified
- `src/think_tool.py` — **new** — stateless reflection tool
- `src/task_tool.py` — **new** — `SubAgent` TypedDict + `_create_task_tool()` factory
- `src/prompts.py` — added `TASK_DESCRIPTION_PREFIX`, `SUBAGENT_USAGE_INSTRUCTIONS`
- `src/deep_agent.py` — integrated task/think tools, `DEFAULT_SUBAGENTS` config, `SUPERVISOR_PROMPT`
- `tests/test_task.py` — **new** — 9 unit + 2 integration tests

### Notable Findings
- Mocking tools in `_create_task_tool` tests requires real `BaseTool` instances — `MagicMock` fails the `isinstance(tool_, BaseTool)` check and LangChain tries to wrap it
- Test state `messages` field must contain proper LangChain message objects (`HumanMessage`, `AIMessage`), not plain dicts — `InjectedState` validation rejects dicts without `type` key
- Review flagged: no error handling around `sub_agent.invoke()` — add in M5 when real network calls can fail
- Review flagged: sub-agents don't get explicit `recursion_limit` — consider setting in M5

---

## M5: Full Deep Research Agent ✅ COMPLETE

**Result:** Real Tavily web search with context offloading. Full page content fetched via httpx, converted to markdown, summarized by Gemma 4 E4B, saved to virtual files — only minimal summaries returned to agent messages. RESEARCHER_INSTRUCTIONS prompt with search budgets (1–5 calls) and think-after-search workflow. 7 new tests (6 unit + 1 integration), 46 total (39 unit + 7 integration).

### Design Decisions
- **Context offloading via search tool** — `tavily_search` returns `Command` updating both `files` (full content) and `messages` (summary only). Keeps agent context minimal while preserving raw data
- **Gemma 4 E4B for summarization** — replaces course's GPT-4o-mini. `Summary` Pydantic model with structured output. Fallback: truncate content on error
- **Lazy initialization** — both `TavilyClient` and `ChatOllama` created on first use via `_get_tavily_client()` / `_get_summarization_model()`. Avoids import-time failures when API keys or Ollama unavailable
- **Research sub-agent gets search + think only** — no file tools needed since `tavily_search` handles file writes via `Command`
- **InjectedToolArg for max_results/topic** — not exposed to LLM, controlled programmatically. Default: 1 result, general topic
- **Integration tests marked separately** — `@pytest.mark.integration` for tests requiring Ollama + Tavily API key

### Tasks
- [x] T1: Add dependencies (`tavily-python`, `httpx`, `markdownify`) + `.env.example`
- [x] T2: Create `src/research_tools.py` — Tavily search, E4B summarizer, context offloading
- [x] T3: Update `src/prompts.py` — `SUMMARIZE_WEB_SEARCH`, `RESEARCHER_INSTRUCTIONS`; remove `SIMPLE_RESEARCH_INSTRUCTIONS`
- [x] T4: Update `src/deep_agent.py` — wire `tavily_search`, remove `mock_web_search`
- [x] T5: Create `tests/test_research.py` — 6 unit + 1 integration test
- [x] T6: Update old tests — mark integration tests, update `mock_web_search` → `tavily_search` refs

### Key Files Created/Modified
- `src/research_tools.py` — **new** — `tavily_search` tool, `Summary` model, `run_tavily_search`, `summarize_webpage_content`, `process_search_results`
- `src/prompts.py` — added `SUMMARIZE_WEB_SEARCH`, `RESEARCHER_INSTRUCTIONS`; removed `SIMPLE_RESEARCH_INSTRUCTIONS`
- `src/deep_agent.py` — replaced mock search with real Tavily, updated sub-agent config
- `src/task_tool.py` — fixed state mutation (shallow copy before modifying messages)
- `tests/test_research.py` — **new** — 6 unit + 1 integration test
- `tests/test_files.py`, `tests/test_task.py`, `tests/test_todo.py` — marked integration tests, updated refs

### Notable Findings
- `TavilyClient()` raises `MissingAPIKeyError` at construction if `TAVILY_API_KEY` not set — lazy init essential
- Review caught state mutation bug in `task_tool.py`: `state["messages"] = ...` mutated caller's dict. Fixed with shallow copy
- Review caught httpx.Client leak: client created inside loop, never closed. Fixed by hoisting outside loop + `.close()`
- E4B structured output works reliably for the `Summary` schema
- Full integration test (supervisor → delegate → Tavily → E4B summarize → file write → return) takes ~5 min on M4 Pro

---

## M5.5: Human-in-the-Loop + Deep Agents UI ✅

### Goal
Single approval gate after supervisor creates research plan. Web UI for demo.

### What Was Built
- `hitl` + `checkpointer` params on `create_deep_agent()` — opt-in HITL
- `HumanInTheLoopMiddleware(interrupt_on={"write_todos": True})` — interrupts on every `write_todos` call (plan + status updates)
- `_make_graph()` factory in `deep_agent.py` — lazy init for `langgraph dev`, avoids ChatOllama at import time
- `langgraph.json` — config pointing to `_make_graph`, reads `.env`
- `langgraph-cli[inmem]` dependency — includes `langgraph-api` for local dev server
- Deep Agents UI as git submodule (`ui/`) — MIT licensed Next.js app with chat, TODO sidebar, file viewer, HITL approve/edit/reject
- `Makefile` — `make setup` (Python + UI deps), `make run` (both servers in parallel), `make test`
- `.gitignore` updated for `.langgraph_api/`
- Removed `.with_config({"recursion_limit": 50})` — `create_agent` sets 9999 internally, 50 was too low for HITL

### Tests
- 3 unit tests: agent creation without/with HITL, middleware targets write_todos
- 2 integration tests: full approve flow, full reject flow
- 42 unit tests total (removed 1 dead test during review)

### Key Decisions
- Used `HumanInTheLoopMiddleware` over custom `interrupt()` calls — cleaner, officially supported
- `_make_graph()` factory over module-level `graph = ...` — avoids eager ChatOllama init that breaks tests
- `npm --legacy-peer-deps` over yarn — yarn not installed, eslint conflict in upstream UI repo
- `langgraph dev` provides checkpointer — no need to pass one in code
- LangSmith tracing optional — added to `.env`, no account required for core functionality

### Known Limitations (addressed in M6)
- Every `write_todos` call triggers approval (including status updates), not just the initial plan
- Makefile hardcodes `ollama pull gemma4:26b` — doesn't support cloud providers
- No multi-provider LLM support yet
