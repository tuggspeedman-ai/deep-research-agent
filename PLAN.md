# PLAN — LangChain Deep Agents

## Current State

**Milestone:** M0 — Project Setup
**Status:** Not started

## M0 — Project Setup

### Goal
Initialize the Python project, install dependencies, verify Gemma 4 runs locally via Ollama, and confirm LangChain can talk to it.

### Tasks
- [ ] Initialize Python project with uv (`pyproject.toml`)
- [ ] Install core dependencies: `langgraph`, `langchain`, `langchain-ollama`, `pytest`, `ruff`
- [ ] Verify Ollama is running and Gemma 4 26B is pulled (`ollama run gemma4:26b`)
- [ ] Write a smoke test: `ChatOllama` -> Gemma 4 -> get a response
- [ ] Write a tool-calling smoke test: bind a simple tool, verify Gemma 4 calls it
- [ ] Set up pytest config and ruff config in `pyproject.toml`
- [ ] Create `.env.example` with any needed config

### Verification
- `pytest` passes with at least the smoke tests
- `ruff check .` clean
- Gemma 4 responds to a basic prompt via `ChatOllama`

## Upcoming Milestones

> These will be fleshed out as we work through the LangChain Academy course modules.

- **M1** — Basic Agent Graph (single LLM node + tools, LangGraph structure)
- **M2** — Planning & Sub-agents (write_todos, task delegation)
- **M3** — Memory & Checkpointing (conversation persistence, state save/restore)
- **M4** — Human-in-the-Loop (interrupt points, approval workflows)
- **M5** — Evals (behavioral test suite, eval-driven iteration)

---

## Decisions Log

<!-- Cumulative. Never archive these — they persist across milestones. -->

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-06 | Gemma 4 26B A4B as primary model | MoE efficiency (3.8B active params), fits easily in 48GB, near-frontier reasoning |
| 2026-04-06 | Ollama over llama.cpp | Native LangChain integration via ChatOllama, MLX on Apple Silicon, simpler setup |
| 2026-04-06 | uv as package manager | Fast, modern Python package management |
| 2026-04-06 | Course-driven milestones | Follow LangChain Academy curriculum structure for systematic learning |
