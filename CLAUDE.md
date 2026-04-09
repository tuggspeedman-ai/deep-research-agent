# CLAUDE.md — LangChain Deep Agents

## Project

**LangChain Deep Agents** — learning project following the [LangChain Academy Deep Agents course](https://academy.langchain.com/courses/deep-agents-with-langgraph). Building a deep agent system using LangGraph with Google Gemma 4 (26B A4B MoE) running locally via Ollama on Apple Silicon (M4 Pro, 48GB).

The goal is to learn LangGraph's agent patterns: explicit planning, sub-agent delegation, checkpointing, human-in-the-loop, and eval-driven development — while running entirely on local hardware.

## Core Principles

- **Simplicity first** — prefer the boring obvious solution. Can this be fewer lines? Are abstractions earning their complexity?
- **Push back when warranted** — if an approach has clear problems, say so directly, propose an alternative, accept override. Sycophancy is a failure mode
- **No over-engineering** — don't add features, abstractions, or error handling beyond what's asked. Don't touch code you weren't asked to touch
- **Verification is the #1 lever** — give every task a way to prove it worked (test, bash command, curl check). This 2-3x's output quality. See `guides/verification.md`
- **Naive-then-optimize** — implement the obviously-correct version first. Verify correctness. Then optimize. Never skip step 1
- **Compaction-safe artifacts** — write important outputs (schemas, decisions, data) to files immediately. Don't rely on conversation history
- **Learning-first** — this is an educational project. Prioritize understanding over speed. When a concept is new, explain the "why" before implementing

## Workflow

- **Assess before each task** — handle directly, delegate to a subagent, or route to MCP. Consider: (1) does the task benefit from fresh context (complex reasoning, independent scope)? (2) can you work on something else in parallel? (3) is context getting tight? Any of these -> delegate. Simple sequential tasks with spacious context -> work directly for faster iteration. See `guides/delegation.md` for the delegation loop and templates
- When delegating, use **`model: "opus"`** by default. Don't write code yourself — hold the plan, delegate precise task specs, receive reports back. Workers get fresh context windows
- **Always delegate research and reviews** — research agents explore, reviewer agents QA from fresh context (see `/review`). These benefit from isolation regardless of context pressure
- Be precise about specs — "implement the planning node with write_todos tool, Gemma 4 via ChatOllama, streaming enabled" not "build the planner"
- Enter plan mode for any non-trivial task (3+ steps or architectural decisions)
- Use `/start` at session start, `/wrapup` at session end
- Use `/review` after completing a milestone — spawns a fresh-context QA reviewer that defaults to rejection

## Session Management

- `/clear` between unrelated tasks; `/compact` to keep focus while clearing noise
- **Two-correction rule**: if wrong twice on the same thing, `/clear` and write a sharper prompt
- Feed raw data (logs, errors, API responses) instead of your interpretation
- Use neutral prompts — "search through this code, follow the logic, report findings" not "find the bug"

## Tech Stack

| Component | Choice |
|-----------|--------|
| Language | Python 3.12+ |
| Agent framework | LangGraph + LangChain |
| LLM | Google Gemma 4 26B A4B (MoE, 3.8B active params) |
| LLM runtime | Ollama (MLX on Apple Silicon) |
| LLM integration | `langchain-ollama` (`ChatOllama`) |
| Embeddings | Local via Ollama (`nomic-embed-text` or Gemma 4 E4B) |
| Observability | LangSmith (optional) |
| Testing | pytest |
| Linting | ruff |
| Type checking | pyright |
| Package manager | uv |

## Local LLM Setup

### Hardware
- Apple MacBook Pro M4 Pro, 48GB unified memory
- Gemma 4 26B A4B at Q4_K_M uses ~18GB, leaving ~30GB for context + system

### Running the model
```bash
# Install Ollama
brew install ollama

# Pull and run Gemma 4 26B MoE
ollama run gemma4:26b

# For quick experimentation, use the smaller E4B
ollama run gemma4:e4b
```

### Known Issues
- Gemma 4 tool calling was broken in Ollama v0.20.0. Fixed in v0.20.2+. If tool calling fails, update Ollama first
- If tool calling is still broken, use llama.cpp as a fallback: `brew install llama.cpp --HEAD && llama-server -hf ggml-org/gemma-4-26B-A4B-it-GGUF:Q4_K_M`

### LangChain Integration
```python
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="gemma4:26b",
    temperature=0,
)
```

## Key Design Decisions

- **Local-first, multi-provider** — defaults to Ollama on local hardware, but supports any LLM provider (OpenAI, Anthropic, Google, etc.) via provider:model strings
- **LangGraph over raw LangChain** — explicit graph-based agent with checkpointing, not simple chains
- **Course-driven structure** — follow the LangChain Academy curriculum, implementing each module as a milestone
- **Eval-driven** — implement behavioral evals as we go, not as an afterthought

## Project State Files

- **`PLAN.md`** — single source of truth for active work. Current milestone broken out with full detail. Completed milestones collapsed to short summary. Decisions Log is cumulative (never archived). Read at session start, update at session end
- **`PLAN-archive.md`** — full detail of completed milestones, preserved for historical context
- **`ORIENT.md`** — human onboarding doc. How the project works, common commands
- **`.claude/memory/MEMORY.md`** — accumulated decisions and gotchas. Append after non-obvious choices

## Key Documents

| Document | When to Read |
|----------|-------------|
| `PLAN.md` | Every session start. Current state, active milestone, decisions |
| `ORIENT.md` | First time setup, common commands |

## Situational Guides

- When delegating work to subagents -> read `guides/delegation.md`
- When verifying work, writing tests, or shipping -> read `guides/verification.md`
