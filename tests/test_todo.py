"""Tests for M2: TODO-based task planning.

Unit tests (no LLM) verify tool mechanics.
Integration tests (Ollama + Gemma 4) verify agent behavior.
"""

import pytest

from src.deep_agent import create_deep_agent
from src.state import Todo
from src.todo_tools import read_todos, submit_plan, write_todos

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def invoke(agent, prompt: str) -> dict:
    """Run the agent and return final state."""
    return agent.invoke({"messages": [("human", prompt)], "todos": []})


# ---------------------------------------------------------------------------
# Unit tests — tool mechanics, no LLM needed
# ---------------------------------------------------------------------------


def _tool_call(name: str, args: dict, call_id: str = "test-123") -> dict:
    """Build a ToolCall dict for invoking tools with InjectedToolCallId."""
    return {"name": name, "args": args, "type": "tool_call", "id": call_id}


def test_submit_plan_returns_command():
    """submit_plan returns a Command that sets todos and adds a ToolMessage."""
    from langgraph.types import Command

    todos: list[Todo] = [
        {"content": "Research MCP", "status": "pending"},
        {"content": "Summarize findings", "status": "pending"},
    ]
    result = submit_plan.invoke(_tool_call("submit_plan", {"todos": todos}))
    assert isinstance(result, Command)
    assert result.update["todos"] == todos
    assert len(result.update["messages"]) == 1
    assert result.update["messages"][0].tool_call_id == "test-123"


def test_write_todos_returns_command():
    """write_todos returns a Command that sets todos and adds a ToolMessage."""
    from langgraph.types import Command

    todos: list[Todo] = [
        {"content": "Research MCP", "status": "pending"},
        {"content": "Summarize findings", "status": "pending"},
    ]
    result = write_todos.invoke(_tool_call("write_todos", {"todos": todos}))
    assert isinstance(result, Command)
    assert result.update["todos"] == todos
    assert len(result.update["messages"]) == 1
    assert result.update["messages"][0].tool_call_id == "test-123"


def test_read_todos_formats_output():
    """read_todos formats the todo list with status icons and numbering."""
    state = {
        "todos": [
            {"content": "Step one", "status": "completed"},
            {"content": "Step two", "status": "in_progress"},
            {"content": "Step three", "status": "pending"},
        ],
        "messages": [],
    }
    result = read_todos.invoke(_tool_call("read_todos", {"state": state}, "test-456"))
    text = result.content if hasattr(result, "content") else result
    assert "Step one" in text
    assert "Step two" in text
    assert "Step three" in text
    assert "[x]" in text  # completed
    assert "[~]" in text  # in_progress
    assert "[ ]" in text  # pending


def test_read_todos_empty_state():
    """read_todos handles missing/empty todos gracefully."""
    result = read_todos.invoke(
        _tool_call("read_todos", {"state": {"todos": [], "messages": []}}, "test-789")
    )
    text = result.content if hasattr(result, "content") else result
    assert "No todos" in text


# ---------------------------------------------------------------------------
# Integration tests — require Ollama + Gemma 4 running
# ---------------------------------------------------------------------------


@pytest.fixture
def agent():
    return create_deep_agent()


@pytest.mark.integration
def test_agent_creates_todos(agent):
    """Agent creates a todo list when given a multi-step research prompt."""
    result = invoke(
        agent,
        "Research the Model Context Protocol: what it is, who created it, "
        "and how it works. Give me a short summary.",
    )
    todos = result.get("todos", [])
    assert len(todos) >= 1, "Agent should create at least one TODO"


@pytest.mark.integration
def test_agent_completes_todos(agent):
    """Agent marks at least one todo as completed by the end of the run."""
    result = invoke(
        agent,
        "Research the Model Context Protocol: what it is, who created it, "
        "and how it works. Give me a short summary.",
    )
    todos = result.get("todos", [])
    completed = [t for t in todos if t["status"] == "completed"]
    assert len(completed) >= 1, "Agent should complete at least one TODO"


@pytest.mark.integration
def test_agent_calls_web_search(agent):
    """Agent calls tavily_search during execution."""
    result = invoke(
        agent,
        "Research the Model Context Protocol and summarize it for me.",
    )
    messages = result["messages"]
    search_called = any(
        hasattr(m, "name") and m.name == "tavily_search" for m in messages
    )
    # Also check tool messages that contain search results
    if not search_called:
        search_called = any(
            "Model Context Protocol" in getattr(m, "content", "")
            for m in messages
            if getattr(m, "type", "") == "tool"
        )
    assert search_called, "Agent should call tavily_search"
