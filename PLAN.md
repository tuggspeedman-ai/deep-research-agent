# PLAN — LangChain Deep Agents

## Project Goals

1. **Learn LangGraph's deep agent patterns** — planning, sub-agent delegation, checkpointing, human-in-the-loop, eval-driven development
2. **Hands-on local LLM experience** — setting up and running Gemma 4 via Ollama on Apple Silicon
3. **Build a reusable deep research agent** — usable for real research tasks beyond the course
4. **Portfolio project** — publish to [GitHub](https://github.com/tuggspeedman-ai), showcase on [jonathanavni.com](https://jonathanavni.com/), write a [blog post](https://jonathanavni.com/blog) about it

## Current State

**Milestone:** M3 — Virtual File System & Context Offloading (in progress)
**Blocked:** Nothing

## M0: Project Setup ✅ COMPLETE

Python project initialized with uv. Gemma 4 26B running via Ollama v0.20.2. Smoke tests pass (basic response + tool calling). GitHub repo live. Full detail in `PLAN-archive.md`.

## M1: ReAct Agent Foundation ✅ COMPLETE

ReAct agent with `create_agent` + Gemma 4. Custom state, InjectedState, Command, structured output, parallel tool calls — all verified. 9 tests pass. Full detail in `PLAN-archive.md`.

## M2: Task Planning (TODOs) ✅ COMPLETE

DeepAgentState with todos, write_todos/read_todos tools, TODO workflow prompts. Agent plans, executes via mock search, updates progress. 6 new tests (3 unit + 3 integration), 15/15 total. Full detail in `PLAN-archive.md`.

## M3 — Virtual File System & Context Offloading ← ACTIVE

### Goal
Add a virtual file system in agent state so the agent can store and retrieve information, reducing token pressure in the message history.

*Course reference: notebook 2 (`2_files.ipynb`)*

### Design

**State:** Add `file_reducer(left, right)` → `{**left, **right}` (merges dicts, right wins, handles None). Add `files: Annotated[NotRequired[dict[str, str]], file_reducer]` to `DeepAgentState`. Unlike todos (full-overwrite), files use a merge reducer so `write_file` only sends `{path: content}`.

**Tools** (`src/file_tools.py` — new file):

| Tool | Params | Injections | Returns |
|------|--------|------------|---------|
| `ls` | none | `InjectedState` | `list[str]` |
| `read_file` | `file_path`, `offset=0`, `limit=2000` | `InjectedState` | `str` (line-numbered) |
| `write_file` | `file_path`, `content` | `InjectedToolCallId` | `Command` |

**Prompts** (`src/prompts.py`): Add `LS_DESCRIPTION`, `READ_FILE_DESCRIPTION`, `WRITE_FILE_DESCRIPTION`, `FILE_USAGE_INSTRUCTIONS` (orient→save→research→read workflow).

**Agent** (`src/deep_agent.py`): Import file tools, add to `TOOLS`, append `FILE_USAGE_INSTRUCTIONS` to system prompt.

### Tasks
- [ ] Add `file_reducer` + `files` field to `DeepAgentState` in `src/state.py`
- [ ] Create `src/file_tools.py` with `ls`, `read_file`, `write_file`
- [ ] Add file tool descriptions + `FILE_USAGE_INSTRUCTIONS` to `src/prompts.py`
- [ ] Wire file tools into `src/deep_agent.py` (TOOLS + system prompt)
- [ ] Create `tests/test_files.py` — unit tests (reducer, all 3 tools, edge cases)
- [ ] Add integration test — agent writes and reads files via LLM
- [ ] Run full test suite — all existing tests still pass

### Verification
- `uv run pytest tests/test_files.py -v` — unit tests pass without Ollama
- `uv run pytest tests/test_files.py -v -k integration` — agent writes/reads files
- `uv run pytest` — all 15 existing + new tests pass (no regressions)

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
