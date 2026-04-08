"""Tests for M4: Sub-agent delegation & context isolation.

Unit tests (no LLM) verify think_tool, task tool mechanics, and context isolation.
Integration tests (Ollama + Gemma 4) verify supervisor delegates to sub-agents.
"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from src.deep_agent import create_deep_agent
from src.task_tool import SubAgent, _create_task_tool
from src.think_tool import think_tool

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
# Unit tests — think_tool
# ---------------------------------------------------------------------------


def test_think_tool_returns_reflection():
    """think_tool echoes the reflection back with prefix."""
    result = think_tool.invoke(
        _tool_call("think_tool", {"reflection": "I need more data on MCP"})
    )
    text = result.content if hasattr(result, "content") else result
    assert "Reflection recorded" in text
    assert "I need more data on MCP" in text


def test_think_tool_empty_reflection():
    """think_tool handles empty string."""
    result = think_tool.invoke(
        _tool_call("think_tool", {"reflection": ""})
    )
    text = result.content if hasattr(result, "content") else result
    assert "Reflection recorded" in text


# ---------------------------------------------------------------------------
# Unit tests — SubAgent config
# ---------------------------------------------------------------------------


def test_subagent_config_minimal():
    """SubAgent works with just required fields."""
    agent: SubAgent = {
        "name": "test-agent",
        "description": "A test agent",
        "prompt": "You are a test agent.",
    }
    assert agent["name"] == "test-agent"
    assert "tools" not in agent


def test_subagent_config_with_tools():
    """SubAgent accepts optional tools list."""
    agent: SubAgent = {
        "name": "test-agent",
        "description": "A test agent",
        "prompt": "You are a test agent.",
        "tools": ["mock_web_search", "think_tool"],
    }
    assert agent["tools"] == ["mock_web_search", "think_tool"]


# ---------------------------------------------------------------------------
# Unit tests — task tool (mocked sub-agent)
# ---------------------------------------------------------------------------


def _make_mock_subagent_result(content: str, files: dict | None = None):
    """Create a mock sub-agent invoke result."""
    return {
        "messages": [AIMessage(content=content)],
        "files": files or {},
        "todos": [],
    }


class TestTaskTool:
    """Tests for _create_task_tool using mocked sub-agents."""

    def _build_task_tool(self, mock_agent):
        """Create a task tool with a mocked sub-agent."""
        subagents: list[SubAgent] = [
            {
                "name": "research-agent",
                "description": "A research agent",
                "prompt": "Research stuff.",
                "tools": ["dummy_tool"],
            },
        ]

        # Use a real tool so BaseTool isinstance check passes
        from langchain_core.tools import tool as tool_decorator

        @tool_decorator
        def dummy_tool() -> str:
            """A dummy tool for testing."""
            return "dummy"

        with patch("src.task_tool.create_agent", return_value=mock_agent):
            return _create_task_tool(
                [dummy_tool], subagents, MagicMock(), MagicMock()
            )

    def test_invalid_subagent_type(self):
        """task tool returns error for unknown subagent_type."""
        mock_agent = MagicMock()
        task = self._build_task_tool(mock_agent)

        result = task.invoke(
            _tool_call(
                "task",
                {
                    "description": "Research MCP",
                    "subagent_type": "nonexistent-agent",
                    "state": {"messages": [], "files": {}, "todos": []},
                },
            )
        )
        text = result.content if hasattr(result, "content") else result
        assert "Error" in text
        assert "nonexistent-agent" in text

    def test_context_isolation(self):
        """Sub-agent receives only the task description, not parent messages."""
        captured_state = {}

        def capture_invoke(state):
            captured_state.update(state)
            return _make_mock_subagent_result("Done researching.")

        mock_agent = MagicMock()
        mock_agent.invoke = capture_invoke
        task = self._build_task_tool(mock_agent)

        parent_state = {
            "messages": [
                HumanMessage(content="Original long conversation..."),
                AIMessage(content="I'll delegate this."),
            ],
            "files": {"existing.md": "important context"},
            "todos": [{"content": "Research MCP", "status": "in_progress"}],
        }

        task.invoke(
            _tool_call(
                "task",
                {
                    "description": "Research MCP protocol",
                    "subagent_type": "research-agent",
                    "state": parent_state,
                },
            )
        )

        # Messages should be replaced with just the task
        assert len(captured_state["messages"]) == 1
        assert captured_state["messages"][0]["content"] == "Research MCP protocol"

        # Files should be preserved (shared)
        assert captured_state["files"] == {"existing.md": "important context"}

    def test_file_changes_propagated(self):
        """File changes from sub-agent appear in Command update."""
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = _make_mock_subagent_result(
            "Found info on MCP.",
            files={"mcp_research.md": "MCP is a protocol..."},
        )
        task = self._build_task_tool(mock_agent)

        result = task.invoke(
            _tool_call(
                "task",
                {
                    "description": "Research MCP",
                    "subagent_type": "research-agent",
                    "state": {"messages": [], "files": {}, "todos": []},
                },
            )
        )

        assert isinstance(result, Command)
        assert result.update["files"] == {"mcp_research.md": "MCP is a protocol..."}

    def test_tool_message_contains_subagent_response(self):
        """Command's ToolMessage contains the sub-agent's last message."""
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = _make_mock_subagent_result(
            "MCP enables AI-tool integration."
        )
        task = self._build_task_tool(mock_agent)

        result = task.invoke(
            _tool_call(
                "task",
                {
                    "description": "Research MCP",
                    "subagent_type": "research-agent",
                    "state": {"messages": [], "files": {}, "todos": []},
                },
            )
        )

        assert isinstance(result, Command)
        messages = result.update["messages"]
        assert len(messages) == 1
        assert isinstance(messages[0], ToolMessage)
        assert "MCP enables AI-tool integration" in messages[0].content
        assert messages[0].tool_call_id == "test-123"

    def test_task_tool_description_lists_agents(self):
        """Task tool description includes available sub-agent names."""
        mock_agent = MagicMock()
        task = self._build_task_tool(mock_agent)
        assert "research-agent" in task.description


# ---------------------------------------------------------------------------
# Integration tests — full agent with Gemma 4 (requires Ollama)
# ---------------------------------------------------------------------------


@pytest.fixture
def agent():
    return create_deep_agent()


def test_supervisor_delegates_to_subagent(agent):
    """Supervisor delegates a research task and receives a result."""
    result = invoke(
        agent,
        "Use the task tool to delegate this research to a research-agent: "
        "What is the Model Context Protocol? Save findings to mcp.md",
    )
    # Sub-agent should have written to the file system
    files = result.get("files", {})
    assert len(files) >= 1, f"Expected sub-agent to write files, got: {files}"


def test_subagent_file_writes_visible(agent):
    """Files written by sub-agents are visible in the final state."""
    result = invoke(
        agent,
        "Delegate to a research-agent: Research MCP and save a summary to "
        "'mcp_summary.md'. After the sub-agent finishes, list the files.",
    )
    files = result.get("files", {})
    # At least one file should exist from the sub-agent's work
    assert len(files) >= 1, f"Expected files from sub-agent, got: {files}"
