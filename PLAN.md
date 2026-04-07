# PLAN — LangChain Deep Agents

## Project Goals

1. **Learn LangGraph's deep agent patterns** — planning, sub-agent delegation, checkpointing, human-in-the-loop, eval-driven development
2. **Hands-on local LLM experience** — setting up and running Gemma 4 via Ollama on Apple Silicon
3. **Build a reusable deep research agent** — usable for real research tasks beyond the course
4. **Portfolio project** — publish to [GitHub](https://github.com/tuggspeedman-ai), showcase on [jonathanavni.com](https://jonathanavni.com/), write a [blog post](https://jonathanavni.com/blog) about it

## Current State

**Milestone:** M0 — Project Setup
**Status:** Complete

## Completed Milestones

### M0 — Project Setup ✓
Initialized Python project with uv, installed deps, verified Gemma 4 26B runs via Ollama v0.20.2, basic response and tool calling smoke tests pass.

## M1 — ReAct Agent Foundation

### Goal
Build a basic ReAct agent using LangGraph's `create_agent` with Gemma 4. Understand the agent loop, custom state, `InjectedState`, and `Command` patterns.

*Course reference: notebook 0 (`0_create_agent.ipynb`)*

### Tasks
- [ ] Create a ReAct agent with `create_agent` (or `create_react_agent`) and Gemma 4
- [ ] Add a custom state schema extending `AgentState`
- [ ] Implement a tool using `InjectedState` to read graph state
- [ ] Implement a tool returning `Command` to update state directly
- [ ] Verify structured output (`.with_structured_output()`) works with Gemma 4
- [ ] Test parallel tool calls in a single response (needed for M3)
- [ ] Write tests for the agent loop

### Verification
- Agent completes a multi-step task using tools
- Custom state is read and updated correctly via tools
- `pytest` passes, `ruff check .` clean

## M2 — Task Planning (TODOs)

### Goal
Implement TODO-based planning so the agent can break complex tasks into steps, track progress, and resist context drift.

*Course reference: notebook 1 (`1_todo.ipynb`)*

### Tasks
- [ ] Define `DeepAgentState` with `todos` field
- [ ] Implement `write_todos` tool — LLM generates `Todo` items (content + status), writes to state via `Command`
- [ ] Implement `read_todos` tool — reads TODO list back into context
- [ ] Craft prompts that instruct the agent to plan first, update TODOs after each step
- [ ] Test context steering — agent stays on track across long runs

### Verification
- Agent creates a plan, executes steps, updates TODO status
- TODOs prevent drift on a multi-step research prompt

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
