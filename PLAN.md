# PLAN — LangChain Deep Agents

## Project Goals

1. **Learn LangGraph's deep agent patterns** — planning, sub-agent delegation, checkpointing, human-in-the-loop, eval-driven development
2. **Hands-on local LLM experience** — setting up and running Gemma 4 via Ollama on Apple Silicon
3. **Build a reusable deep research agent** — usable for real research tasks beyond the course
4. **Portfolio project** — publish to [GitHub](https://github.com/tuggspeedman-ai), showcase on [jonathanavni.com](https://jonathanavni.com/), write a [blog post](https://jonathanavni.com/blog) about it

## Current State

**Milestone:** M5.5 — Human-in-the-Loop Plan Approval (not started)
**Next session:** Implement M5.5
**Blocked:** Nothing

## M0: Project Setup ✅ COMPLETE

Python project initialized with uv. Gemma 4 26B running via Ollama v0.20.2. Smoke tests pass (basic response + tool calling). GitHub repo live. Full detail in `PLAN-archive.md`.

## M1: ReAct Agent Foundation ✅ COMPLETE

ReAct agent with `create_agent` + Gemma 4. Custom state, InjectedState, Command, structured output, parallel tool calls — all verified. 9 tests pass. Full detail in `PLAN-archive.md`.

## M2: Task Planning (TODOs) ✅ COMPLETE

DeepAgentState with todos, write_todos/read_todos tools, TODO workflow prompts. Agent plans, executes via mock search, updates progress. 6 new tests (3 unit + 3 integration), 15/15 total. Full detail in `PLAN-archive.md`.

## M3: Virtual File System & Context Offloading ✅ COMPLETE

Virtual filesystem in DeepAgentState with `file_reducer` (merge semantics). `ls`, `read_file`, `write_file` tools. `write_file` simplified over course version — skips `InjectedState` since reducer handles merge. 13 new tests (12 unit + 1 integration), 28 total. Full detail in `PLAN-archive.md`.

## M4: Sub-agent Delegation ✅ COMPLETE

Sub-agent delegation with context isolation via `_create_task_tool()` factory. `SubAgent` TypedDict config, `think_tool` for reflection, supervisor prompt with scaling rules. Context isolation through message reset; shared file system via `file_reducer`. 11 new tests (9 unit + 2 integration), 39 total. Full detail in `PLAN-archive.md`.

## M5: Full Deep Research Agent ✅ COMPLETE

Real Tavily web search with context offloading (full content → files, summaries → messages). Gemma 4 E4B for summarization via structured output. `RESEARCHER_INSTRUCTIONS` prompt with search budgets and think-after-search workflow. Old `mock_web_search` replaced. 6 new unit tests + 1 integration test, 46 total (39 unit + 7 integration). Full detail in `PLAN-archive.md`.

## M5.5 — Human-in-the-Loop + Deep Agents UI

### Goal
Add a single approval gate after the supervisor creates its research plan, served via LangGraph dev server with the LangChain Deep Agents UI. User reviews TODOs in a web UI, approves/edits/rejects, then the agent executes autonomously. Demonstrates LangGraph's `interrupt()` + checkpointing + deployment.

### Approach
1. **HITL middleware** — Use LangChain's built-in `HumanInTheLoopMiddleware` configured to interrupt on `write_todos`. `create_agent()` already accepts `checkpointer` and `middleware` params — no manual graph building needed
2. **LangGraph dev server** — Serve the agent via `langgraph dev` (local API server on port 2024). Provides checkpointer automatically. No LangSmith account required
3. **Deep Agents UI** — LangChain's open-source Next.js UI (MIT licensed). Add as git submodule. Renders TODOs, files, streaming chat, and HITL approve/edit/reject out of the box
4. **Easy setup** — `Makefile` with `make setup` and `make run` commands. One-command experience

### Tasks
- [ ] **Modify `src/deep_agent.py`** — Add `hitl` param to `create_deep_agent()`. When `hitl=True`, attach `HumanInTheLoopMiddleware(interrupt_on={"write_todos": True})`. Remove `.with_config({"recursion_limit": 50})` (create_agent sets 9999; 50 too low for HITL). No need to pass checkpointer — `langgraph dev` provides one
- [ ] **Create `langgraph.json`** — Config file pointing to our agent graph. Maps `"deep_agent"` → `src/deep_agent.py:graph` (module-level export)
- [ ] **Export agent via factory** — Add `_make_graph()` factory to `src/deep_agent.py` for `langgraph dev` (avoids eager ChatOllama init at import time)
- [ ] **Add `deep-agents-ui` as git submodule** — `git submodule add https://github.com/langchain-ai/deep-agents-ui.git ui`
- [ ] **Add `langgraph-cli` to dependencies** — Update `pyproject.toml`
- [ ] **Create `Makefile`** — `make setup` (uv install, yarn install in ui/, pull ollama model), `make run` (starts langgraph dev + yarn dev in parallel)
- [ ] **Create `tests/test_hitl.py`** — Unit tests (mock LLM): agent creation with HITL, interrupt fires on write_todos, approve resumes, reject sends error. Integration tests (Ollama+Tavily): full approve flow
- [ ] **Verify** — All existing tests pass. `make run` starts both servers. UI connects, sends query, shows plan approval, executes to completion

### Key APIs
```python
from langchain.agents.middleware.human_in_the_loop import HumanInTheLoopMiddleware
# Middleware: interrupt_on={"write_todos": True} → approve/edit/reject
# Checkpointer: provided by langgraph dev server (not needed in code)
# UI handles interrupt display + resume via Command(resume=HITLResponse(...))
```

### Distribution
Someone cloning the repo needs:
- Python 3.12+ & `uv` — standard
- Ollama + Gemma 4 model — `brew install ollama && ollama pull gemma4:26b`
- Tavily API key (free tier) — goes in `.env`
- Node.js + npm — for the UI
- Then: `git clone --recursive` + `make setup` + `make run`
- No LangSmith/LangChain account required. Fully local

---

## M6 — Polish & Portfolio

### Goal
Make the project presentable and easy for anyone to run, regardless of their LLM setup.

### Tasks
- [ ] **HITL: interrupt only on initial plan** — Only trigger approval on the first `write_todos` call (the plan), not on subsequent status updates. Either custom middleware that tracks call count, or a separate `submit_plan` tool that the agent calls once after planning
- [ ] **Multi-provider LLM support** — `create_deep_agent` accepts `provider:model` strings (e.g. `"openai:gpt-4o"`, `"anthropic:claude-sonnet-4-5-20250514"`, `"google_genai:gemini-2.0-flash"`) via `create_agent`'s native string support, OR Ollama model names for local (current behavior). Make summarizer configurable too. Config via `MODEL` env var in `.env`
- [ ] Write README with project overview, architecture diagram, setup instructions (local + cloud LLM paths)
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
| 2026-04-08 | Gemma 4 E4B for summarization | Lightweight local model replaces course's GPT-4o-mini; keeps everything local |
| 2026-04-08 | Lazy client initialization | TavilyClient + ChatOllama created on first use, not at import time; avoids test/import failures |
| 2026-04-08 | Integration tests marked separately | `@pytest.mark.integration` for tests requiring Ollama + Tavily; unit tests run fast without external deps |
| 2026-04-08 | Deep Agents UI over custom CLI demo | LangChain's MIT-licensed Next.js UI handles TODOs, files, streaming, and HITL natively; much more impressive for portfolio than a terminal script |
| 2026-04-08 | langgraph dev for serving | Local API server with built-in checkpointer; no LangSmith account required; standard deployment pattern |
| 2026-04-08 | Git submodule for UI | Pin version, single `git clone --recursive` for users; MIT license allows this |
