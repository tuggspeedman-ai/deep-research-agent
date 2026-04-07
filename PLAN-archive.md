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
