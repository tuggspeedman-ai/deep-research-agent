# PLAN — LangChain Deep Agents

## Project Goals

1. **Learn LangGraph's deep agent patterns** — planning, sub-agent delegation, checkpointing, human-in-the-loop, eval-driven development
2. **Hands-on local LLM experience** — setting up and running Gemma 4 via Ollama on Apple Silicon
3. **Build a reusable deep research agent** — usable for real research tasks beyond the course
4. **Portfolio project** — publish to [GitHub](https://github.com/tuggspeedman-ai), showcase on [jonathanavni.com](https://jonathanavni.com/), write a [blog post](https://jonathanavni.com/blog) about it

## Current State

**Milestone:** M1 — Complete. Ready for M2
**Next session:** Start M2 — Task Planning (TODOs)
**Blocked:** Nothing

## M0: Project Setup ✅ COMPLETE

Python project initialized with uv. Gemma 4 26B running via Ollama v0.20.2. Smoke tests pass (basic response + tool calling). GitHub repo live. Full detail in `PLAN-archive.md`.

## M1: ReAct Agent Foundation ✅ COMPLETE

ReAct agent with `create_agent` + Gemma 4. Custom state, InjectedState, Command, structured output, parallel tool calls — all verified. 9 tests pass. Full detail in `PLAN-archive.md`.

## M2 — Task Planning (TODOs) 🔄 IN PROGRESS

### Goal
Implement TODO-based planning so the agent can break complex tasks into steps, track progress, and resist context drift.

*Course reference: notebook 1 (`1_todo.ipynb`)*

### Design Decisions
- **`todos` only** — no `files` field until M3. No over-engineering
- **No reducer on `todos`** — full overwrite semantics. LLM rewrites the entire list each call (Manus/Claude Code pattern)
- **Mock `web_search`** — canned MCP response. Real search comes in M5, avoids API keys now
- **`read_todos` returns `str`** — simpler than Command when no state update needed (LangGraph auto-wraps as ToolMessage)
- **Recursion limit 30** — TODO loop needs more tool-call steps than M1's calculator (20)
- **M1 untouched** — calc agent stays as-is. M2 starts the "deep agent" lineage (M2→M5)

### New Files
| File | ~Lines | Purpose |
|------|--------|---------|
| `src/state.py` | 30 | `Todo` TypedDict + `DeepAgentState(AgentState)` with `todos` field |
| `src/prompts.py` | 50 | `WRITE_TODOS_DESCRIPTION`, `TODO_USAGE_INSTRUCTIONS`, `SIMPLE_RESEARCH_INSTRUCTIONS` |
| `src/todo_tools.py` | 60 | `write_todos` (→ Command) + `read_todos` (→ str) |
| `src/deep_agent.py` | 70 | `mock_web_search` tool + `create_deep_agent()` factory |
| `tests/test_todo.py` | 120 | Unit tests (no LLM) + integration tests (Ollama + Gemma 4) |

### Tasks
- [x] `src/state.py` — `Todo` TypedDict + `DeepAgentState` with `todos` field
- [x] `src/prompts.py` — tool descriptions + TODO workflow instructions
- [x] `src/todo_tools.py` — `write_todos` (Command return) + `read_todos` (str return)
- [x] `src/deep_agent.py` — mock web search + `create_deep_agent()` factory
- [x] `tests/test_todo.py` — unit tests (tool mechanics) + integration tests (agent behavior)
- [x] Run all tests (M1 + M2), verify everything passes — 15/15 pass

### Verification
- Unit: `write_todos` returns Command with correct todos + ToolMessage; `read_todos` formats output; handles empty state
- Integration: agent creates todos for multi-step prompt, completes at least one, calls mock_web_search
- Regression: all M1 tests still pass
- `uv run pytest -v`

## M3 — Virtual File System & Context Offloading

### Goal
Add a virtual file system in agent state so the agent can store and retrieve information, reducing token pressure in the message history.

*Course reference: notebook 2 (`2_files.ipynb`)*

### Tasks
- [ ] Add `files` field to `DeepAgentState` with a merge reducer
- [ ] Implement `ls`, `read_file`, `write_file` tools
- [ ] Pattern: agent saves verbose tool output to files, keeps summaries in messages
- [ ] Test file persistence across agent steps

### Verification
- Agent stores search results in files, retrieves them later
- Token usage is lower than keeping everything in messages

## M4 — Sub-agent Delegation

### Goal
Implement sub-agent spawning for context isolation. The supervisor delegates tasks to specialized sub-agents with their own tools and fresh context windows.

*Course reference: notebook 3 (`3_subagents.ipynb`)*

### Tasks
- [ ] Define `SubAgent` config (name, description, prompt, tools)
- [ ] Implement `_create_task_tool()` factory — creates a `task(description, subagent_type)` tool
- [ ] Sub-agents get isolated messages but share the file system
- [ ] Implement `think_tool` for structured reflection
- [ ] Test parallel sub-agent execution for independent research streams

### Verification
- Supervisor delegates to sub-agents, receives results
- Sub-agents don't pollute supervisor's context
- File system changes from sub-agents are visible to supervisor

## M5 — Full Deep Research Agent

### Goal
Compose everything into a working deep research agent with real web search, summarization, and the full tool suite.

*Course reference: notebook 4 (`4_full_agent.ipynb`)*

### Tasks
- [ ] Integrate web search (Tavily)
- [ ] Implement search result summarization (Gemma 4 E4B as lightweight summarizer)
- [ ] Build the full tool suite: TODOs + files + sub-agents + search + think
- [ ] Craft the supervisor system prompt
- [ ] Test on a real research question end-to-end
- [ ] Add dependencies: `tavily-python`, `httpx`, `markdownify`

### Verification
- Agent researches a complex topic, produces a structured report
- Report is saved to the virtual file system
- Sub-agents handle parallel research streams

## M6 — Polish & Portfolio

### Goal
Make the project presentable: README, documentation, clean API, example usage.

### Tasks
- [ ] Write README with project overview, architecture diagram, setup instructions
- [ ] Add example scripts showing the agent in action
- [ ] Write blog post draft
- [ ] Clean up code, ensure consistent style
- [ ] Tag a release

---

## Decisions Log

<!-- Cumulative. Never archive these — they persist across milestones. -->

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-06 | Gemma 4 26B A4B as primary model | MoE efficiency (3.8B active params), fits easily in 48GB, near-frontier reasoning |
| 2026-04-06 | Ollama over llama.cpp | Native LangChain integration via ChatOllama, MLX on Apple Silicon, simpler setup |
| 2026-04-06 | uv as package manager | Fast, modern Python package management |
| 2026-04-06 | Course-driven milestones | Follow LangChain Academy curriculum structure for systematic learning |
| 2026-04-06 | Tavily for web search | Consistency with LangChain course; free tier sufficient |
