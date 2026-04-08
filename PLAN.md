# PLAN — LangChain Deep Agents

## Project Goals

1. **Learn LangGraph's deep agent patterns** — planning, sub-agent delegation, checkpointing, human-in-the-loop, eval-driven development
2. **Hands-on local LLM experience** — setting up and running Gemma 4 via Ollama on Apple Silicon
3. **Build a reusable deep research agent** — usable for real research tasks beyond the course
4. **Portfolio project** — publish to [GitHub](https://github.com/tuggspeedman-ai), showcase on [jonathanavni.com](https://jonathanavni.com/), write a [blog post](https://jonathanavni.com/blog) about it

## Current State

**Milestone:** M4 — Sub-agent Delegation (in progress)
**Status:** Plan complete, ready to implement T1-T7
**Blocked:** Nothing

## M0: Project Setup ✅ COMPLETE

Python project initialized with uv. Gemma 4 26B running via Ollama v0.20.2. Smoke tests pass (basic response + tool calling). GitHub repo live. Full detail in `PLAN-archive.md`.

## M1: ReAct Agent Foundation ✅ COMPLETE

ReAct agent with `create_agent` + Gemma 4. Custom state, InjectedState, Command, structured output, parallel tool calls — all verified. 9 tests pass. Full detail in `PLAN-archive.md`.

## M2: Task Planning (TODOs) ✅ COMPLETE

DeepAgentState with todos, write_todos/read_todos tools, TODO workflow prompts. Agent plans, executes via mock search, updates progress. 6 new tests (3 unit + 3 integration), 15/15 total. Full detail in `PLAN-archive.md`.

## M3: Virtual File System & Context Offloading ✅ COMPLETE

Virtual filesystem in DeepAgentState with `file_reducer` (merge semantics). `ls`, `read_file`, `write_file` tools. `write_file` simplified over course version — skips `InjectedState` since reducer handles merge. 13 new tests (12 unit + 1 integration), 28 total. Full detail in `PLAN-archive.md`.

## M4 — Sub-agent Delegation ← ACTIVE

### Goal
Implement sub-agent spawning for context isolation. The supervisor delegates tasks to specialized sub-agents with their own tools and fresh context windows.

*Course reference: notebook 3 (`3_subagents.ipynb`), course impl: `course-materials/.../task_tool.py`*

### Design

**Core pattern:** Context isolation through message reset. Sub-agents receive `state["messages"] = [{"role": "user", "content": description}]` — fresh messages, shared file system (via `file_reducer` merge).

**New files:**
- `src/think_tool.py` (~15 lines) — stateless reflection tool, returns confirmation string
- `src/task_tool.py` (~80 lines) — `SubAgent` TypedDict + `_create_task_tool()` factory
- `tests/test_task.py` (~150 lines) — unit tests (no LLM) + integration tests

**Modified files:**
- `src/prompts.py` — add `TASK_DESCRIPTION_PREFIX`, `SUBAGENT_USAGE_INSTRUCTIONS`
- `src/deep_agent.py` — integrate task tool + think_tool, default research sub-agent config

**Key decisions:**
- `SubAgent` is a TypedDict: `name`, `description`, `prompt`, `tools: NotRequired[list[str]]`
- `_create_task_tool()` builds an agent registry, returns a `task` tool with `InjectedState` + `InjectedToolCallId`
- Task tool returns `Command` with merged files + ToolMessage (sub-agent's last message)
- Default sub-agent ("research-agent") uses mock_web_search + file tools + think_tool
- Real Tavily search deferred to M5

### Tasks
- [x] T1: Create `src/think_tool.py` — stateless `think_tool(reflection) -> str`
- [x] T2: Add `TASK_DESCRIPTION_PREFIX` and `SUBAGENT_USAGE_INSTRUCTIONS` to `src/prompts.py`
- [x] T3: Create `src/task_tool.py` — `SubAgent` TypedDict + `_create_task_tool()` factory
- [x] T4: Update `src/deep_agent.py` — integrate task/think tools, define default research sub-agent
- [x] T5: Create `tests/test_task.py` — unit tests (think_tool, task tool isolation, error handling)
- [x] T6: Add integration tests — supervisor delegates, sub-agent file writes visible
- [x] T7: Run full test suite, verify 28+ existing tests still pass + new tests

### Verification
- `uv run pytest tests/test_task.py -v` — all new tests pass
- `uv run pytest tests/ -v` — all 28 existing + new tests pass
- Unit: think_tool returns expected string
- Unit: task tool rejects invalid subagent_type
- Unit: context isolation (messages replaced, files preserved)
- Unit: file changes propagated back via Command
- Integration: supervisor delegates and receives results
- Integration: sub-agent file writes visible to supervisor

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
