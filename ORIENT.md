# ORIENT — LangChain Deep Agents

Quick-start guide for humans. Read this first.

## What is this?

A learning project following the [LangChain Academy Deep Agents course](https://academy.langchain.com/courses/deep-agents-with-langgraph). We're building deep agents with LangGraph, powered by Google Gemma 4 running locally via Ollama.

## Prerequisites

```bash
# Python 3.12+
python3 --version

# uv (package manager)
brew install uv

# Ollama (local LLM runtime)
brew install ollama

# Pull Gemma 4 26B MoE (~18GB download)
ollama pull gemma4:26b
```

## Common Commands

```bash
# Run tests
pytest

# Lint
ruff check .

# Format
ruff format .

# Type check
pyright

# Verify Ollama is running
ollama list

# Quick test that Gemma 4 works
ollama run gemma4:26b "Hello, what model are you?"
```

## Project Structure

```
langchain-deep-agent/
  CLAUDE.md          # AI assistant instructions
  PLAN.md            # Active work tracker
  PLAN-archive.md    # Completed milestone detail
  ORIENT.md          # This file
  .claude/           # Claude Code config
    commands/        # Slash commands (/start, /wrapup, /review)
    rules/           # Behavioral rules
    memory/          # Project decisions & gotchas
    settings.json    # Permissions & hooks
  guides/            # Workflow guides (delegation, verification)
  src/               # Source code (created during M0)
  tests/             # Test suite
```

## Session Workflow

1. Start: `/start` — loads PLAN.md, orients on current state
2. Work: implement, test, iterate
3. Review: `/review` — QA from fresh context after milestones
4. Close: `/wrapup` — persists decisions and updates PLAN.md
