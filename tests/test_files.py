"""Tests for M3: Virtual file system & context offloading.

Unit tests (no LLM) verify tool mechanics and reducer.
Integration tests (Ollama + Gemma 4) verify agent uses files.
"""

import pytest
from langgraph.types import Command

from src.deep_agent import create_deep_agent
from src.file_tools import ls, read_file, write_file
from src.state import file_reducer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tool_call(name: str, args: dict, call_id: str = "test-123") -> dict:
    """Build a ToolCall dict for invoking tools with InjectedToolCallId."""
    return {"name": name, "args": args, "type": "tool_call", "id": call_id}


def invoke(agent, prompt: str) -> dict:
    """Run the agent and return final state."""
    return agent.invoke({"messages": [("human", prompt)], "todos": [], "files": {}})


# ---------------------------------------------------------------------------
# Unit tests — file_reducer
# ---------------------------------------------------------------------------


def test_file_reducer_merges():
    """Reducer merges two dicts, right side wins on conflicts."""
    left = {"a.md": "old a", "b.md": "content b"}
    right = {"a.md": "new a", "c.md": "content c"}
    result = file_reducer(left, right)
    assert result == {"a.md": "new a", "b.md": "content b", "c.md": "content c"}


def test_file_reducer_left_none():
    """Reducer handles None left (initial state)."""
    assert file_reducer(None, {"a.md": "hello"}) == {"a.md": "hello"}


def test_file_reducer_right_none():
    """Reducer handles None right (no update)."""
    assert file_reducer({"a.md": "hello"}, None) == {"a.md": "hello"}


def test_file_reducer_both_none():
    """Reducer handles both None."""
    assert file_reducer(None, None) == {}


# ---------------------------------------------------------------------------
# Unit tests — ls tool
# ---------------------------------------------------------------------------


def test_ls_with_files():
    """ls returns list of file paths."""
    state = {"files": {"a.md": "aaa", "b.txt": "bbb"}, "messages": []}
    result = ls.invoke(_tool_call("ls", {"state": state}))
    content = result.content if hasattr(result, "content") else result
    assert sorted(content) == ["a.md", "b.txt"]


def test_ls_empty():
    """ls returns empty list when no files exist."""
    state = {"files": {}, "messages": []}
    result = ls.invoke(_tool_call("ls", {"state": state}))
    content = result.content if hasattr(result, "content") else result
    assert content == []


# ---------------------------------------------------------------------------
# Unit tests — read_file tool
# ---------------------------------------------------------------------------


def test_read_file_with_content():
    """read_file returns line-numbered content."""
    state = {"files": {"notes.md": "line one\nline two\nline three"}, "messages": []}
    result = read_file.invoke(
        _tool_call("read_file", {"file_path": "notes.md", "state": state})
    )
    text = result.content if hasattr(result, "content") else result
    assert "line one" in text
    assert "line two" in text
    assert "line three" in text
    # Check line numbers are present
    assert "1\t" in text


def test_read_file_not_found():
    """read_file returns error for missing file."""
    state = {"files": {}, "messages": []}
    result = read_file.invoke(
        _tool_call("read_file", {"file_path": "missing.md", "state": state})
    )
    text = result.content if hasattr(result, "content") else result
    assert "Error" in text
    assert "not found" in text


def test_read_file_empty():
    """read_file handles empty file content."""
    state = {"files": {"empty.md": ""}, "messages": []}
    result = read_file.invoke(
        _tool_call("read_file", {"file_path": "empty.md", "state": state})
    )
    text = result.content if hasattr(result, "content") else result
    assert "empty" in text.lower()


def test_read_file_with_offset_and_limit():
    """read_file respects offset and limit for pagination."""
    content = "\n".join(f"line {i}" for i in range(1, 11))  # 10 lines
    state = {"files": {"big.md": content}, "messages": []}
    result = read_file.invoke(
        _tool_call(
            "read_file",
            {"file_path": "big.md", "state": state, "offset": 3, "limit": 2},
        )
    )
    text = result.content if hasattr(result, "content") else result
    assert "line 4" in text  # offset=3 means start at 4th line (0-indexed)
    assert "line 5" in text
    assert "line 6" not in text  # limit=2
    assert "line 3" not in text  # before offset


def test_read_file_offset_out_of_range():
    """read_file returns error when offset exceeds file length."""
    state = {"files": {"short.md": "one line"}, "messages": []}
    result = read_file.invoke(
        _tool_call(
            "read_file",
            {"file_path": "short.md", "state": state, "offset": 100},
        )
    )
    text = result.content if hasattr(result, "content") else result
    assert "Error" in text
    assert "offset" in text.lower()


# ---------------------------------------------------------------------------
# Unit tests — write_file tool
# ---------------------------------------------------------------------------


def test_write_file_returns_command():
    """write_file returns a Command with files dict and ToolMessage."""
    result = write_file.invoke(
        _tool_call("write_file", {"file_path": "report.md", "content": "# Report"})
    )
    assert isinstance(result, Command)
    assert result.update["files"] == {"report.md": "# Report"}
    assert len(result.update["messages"]) == 1
    assert result.update["messages"][0].tool_call_id == "test-123"
    assert "report.md" in result.update["messages"][0].content


# ---------------------------------------------------------------------------
# Integration tests — require Ollama + Gemma 4 running
# ---------------------------------------------------------------------------


@pytest.fixture
def agent():
    return create_deep_agent()


def test_agent_writes_and_reads_file(agent):
    """Agent stores information in a file and the files dict is populated."""
    result = invoke(
        agent,
        "Research MCP and save your findings to a file called 'mcp_research.md'. "
        "Then read the file back and summarize what you saved.",
    )
    files = result.get("files", {})
    assert len(files) >= 1, "Agent should create at least one file"
