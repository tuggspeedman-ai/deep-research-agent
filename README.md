# Deep Research Agent

A planning, delegating, searching research agent built with LangGraph - running Gemma 4 locally on Apple Silicon, or any cloud LLM.

## Why does this exist?

I had two goals: learn LangGraph's deep agent patterns hands-on by following the [LangChain Academy Deep Agents course](https://academy.langchain.com/courses/deep-agents-with-langgraph), and experiment running real world agentic workflows using a local LLM. The course uses cloud APIs. I swapped in Google's Gemma 4 26B running via Ollama on an M4 Pro with 48GB of unified memory. The result is a research agent that can take a question, break it into a plan, delegate research tasks to specialized sub-agents, search the web, and synthesize findings - all without calling a cloud LLM.

An interesting takeaway for me was LangGraph itself. Defining an agent as a state machine with typed state, reducers, and explicit tool routing gives you control over context and state flow that a `prompt -> LLM -> action` loop doesn't.

## How it works

```
User ──> Supervisor Agent ──> submit_plan ──> [HITL: approve / edit / reject]
              |                                         |
              |  <──────────────────────────────────────+
              |
              +──> task(research-agent) ──> tavily_search ──> think_tool
              |         |                       |
              |         +── writes to ──> Virtual File System (shared state)
              |
              +──> write_todos (progress updates, no interrupt)
              +──> read_todos
              +──> ls / read_file / write_file
              +──> tavily_search (direct)
              +──> think_tool
```

The supervisor creates a TODO-based research plan, submits it for human approval via HITL, then delegates research tasks to sub-agents. Sub-agents run with isolated message history (no context pollution) but share the virtual file system through LangGraph's `file_reducer` merge semantics. Raw web content is offloaded to files; only short summaries stay in the message stream. This lets the agent search dozens of pages without exhausting its context window.

| Component | Details |
|-----------|---------|
| Model | Gemma 4 26B A4B (MoE, 3.8B active params) via Ollama, or any provider |
| Summarizer | Gemma 4 E4B (lightweight, runs alongside the main model) |
| Framework | LangGraph + LangChain |
| Search | Tavily web search with context offloading |
| UI | [Deep Agents UI](https://github.com/langchain-ai/deep-agents-ui) (Next.js, git submodule) |
| Tests | 36 unit + 16 integration, pytest |

## Quick start

### Local (Ollama)

Prerequisites: Python 3.12+, Node.js, [Ollama](https://ollama.com/)

```bash
git clone --recursive https://github.com/tuggspeedman-ai/langchain-deep-agent.git
cd langchain-deep-agent

cp .env.example .env
# Add your TAVILY_API_KEY to .env

make pull-models    # pulls gemma4:26b + gemma4:e4b
make setup          # Python deps + UI deps
make run            # backend on :2024, UI on :3000
```

### Cloud provider

```bash
git clone --recursive https://github.com/tuggspeedman-ai/langchain-deep-agent.git
cd langchain-deep-agent

cp .env.example .env
# Set MODEL=openai:gpt-5.4-mini (or anthropic:claude-sonnet-4-6, google_genai:gemini-2.5-flash)
# Set the matching API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
# Set TAVILY_API_KEY

uv sync --extra openai   # or: --extra anthropic, --extra google
make setup
make run
```

In the UI, set **Deployment URL** to `http://127.0.0.1:2024` and **Assistant ID** to `deep_agent`.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL` | `ollama:gemma4:26b` | LLM in `provider:model` format |
| `SUMMARIZER_MODEL` | `ollama:gemma4:e4b` | Model for summarizing search results |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL (local only) |
| `TAVILY_API_KEY` | | Web search API key ([tavily.com](https://tavily.com/)) |
| `LANGSMITH_API_KEY` | | Optional, enables tracing |

## Project structure

```
src/
  deep_agent.py       Agent factory - wires tools, prompts, middleware, sub-agents
  state.py            DeepAgentState with todos (overwrite) and files (merge reducer)
  todo_tools.py       submit_plan, write_todos, read_todos
  file_tools.py       ls, read_file, write_file (virtual filesystem)
  research_tools.py   tavily_search with context offloading + summarization
  task_tool.py        Sub-agent delegation with context isolation
  think_tool.py       Structured reflection tool
  prompts.py          All prompt templates and tool descriptions
ui/                   Deep Agents UI (git submodule)
tests/                36 unit + 16 integration tests
examples/             CLI scripts for running without the UI
```

## Architecture highlights

A few decisions that might be useful if you're building something similar:

- **Context isolation via message reset.** Sub-agents get fresh message history containing only their task description. They don't inherit the supervisor's conversation, which prevents context pollution as research scales. But they share the virtual file system through `file_reducer` merge semantics, so research results flow back automatically.

- **Context offloading over context stuffing.** `tavily_search` fetches full page content, summarizes it with the E4B model, saves the raw content to files, and returns only the summary to the message stream. The agent sees "here's what I found, full content is in `result_a3f2.md`" and can `read_file` when needed. One tool call updates both `files` and `messages` atomically via `Command`.

- **HITL on plan submission, not every update.** The `submit_plan` tool triggers human-in-the-loop approval for the initial research plan. `write_todos` handles progress updates without interrupting. This is cleaner than tracking call counts in middleware.

- **Multi-provider via `init_chat_model`.** One environment variable (`MODEL`) switches between local Ollama and any cloud provider. No code changes, no provider-specific imports. LangChain's `init_chat_model` parses `"provider:model"` strings and returns the right chat model.

- **Testing outcomes, not sequences.** Unit tests don't assert tool call order. They assert that after running, TODOs exist, files contain expected content, and the final message answers the question. Integration tests (requiring Ollama + Tavily) are marked separately with `@pytest.mark.integration` so unit tests run fast.

## Tests

```bash
make test              # unit tests (fast, no external deps)
make test-integration  # integration tests (requires Ollama + Tavily)
```

## Based on

- [LangChain Academy Deep Agents course](https://academy.langchain.com/courses/deep-agents-with-langgraph)
- [Deep Agents UI](https://github.com/langchain-ai/deep-agents-ui)
- [Gemma 4](https://ai.google.dev/gemma) via [Ollama](https://ollama.com/)
- [Tavily](https://tavily.com/) for web search

## License

MIT
