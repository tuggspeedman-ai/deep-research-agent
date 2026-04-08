"""Tests for M5.5: Human-in-the-loop plan approval.

Unit tests (no LLM) verify HITL middleware wiring and interrupt/resume mechanics.
Integration tests (Ollama + Tavily) verify the full approve/reject flow.
"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from src.deep_agent import create_deep_agent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tool_call(name: str, args: dict, call_id: str = "tc-001") -> dict:
    return {"name": name, "args": args, "type": "tool_call", "id": call_id}


SAMPLE_TODOS = [
    {"content": "Search for MCP overview", "status": "pending"},
    {"content": "Summarize findings", "status": "pending"},
]


# ---------------------------------------------------------------------------
# Unit tests — agent creation
# ---------------------------------------------------------------------------


def test_create_agent_without_hitl():
    """Agent creation without HITL works (no middleware, no checkpointer)."""
    with patch("src.deep_agent.ChatOllama") as mock_llm:
        mock_llm.return_value = MagicMock()
        with patch("src.deep_agent.create_agent") as mock_create:
            mock_create.return_value = MagicMock()
            create_deep_agent(hitl=False)
            _, kwargs = mock_create.call_args
            assert kwargs["middleware"] == []
            assert kwargs["checkpointer"] is None


def test_create_agent_with_hitl():
    """Agent creation with HITL attaches middleware and accepts checkpointer."""
    checkpointer = InMemorySaver()
    with patch("src.deep_agent.ChatOllama") as mock_llm:
        mock_llm.return_value = MagicMock()
        with patch("src.deep_agent.create_agent") as mock_create:
            mock_create.return_value = MagicMock()
            create_deep_agent(hitl=True, checkpointer=checkpointer)
            _, kwargs = mock_create.call_args
            assert len(kwargs["middleware"]) == 1
            assert kwargs["checkpointer"] is checkpointer


def test_hitl_middleware_targets_write_todos():
    """HITL middleware is configured to interrupt on write_todos."""
    from langchain.agents.middleware.human_in_the_loop import (
        HumanInTheLoopMiddleware,
    )

    checkpointer = InMemorySaver()
    with patch("src.deep_agent.ChatOllama") as mock_llm:
        mock_llm.return_value = MagicMock()
        with patch("src.deep_agent.create_agent") as mock_create:
            mock_create.return_value = MagicMock()
            create_deep_agent(hitl=True, checkpointer=checkpointer)
            _, kwargs = mock_create.call_args
            mw = kwargs["middleware"][0]
            assert isinstance(mw, HumanInTheLoopMiddleware)
            assert "write_todos" in mw.interrupt_on


# ---------------------------------------------------------------------------
# Unit tests — interrupt/resume mechanics (mocked LLM)
# ---------------------------------------------------------------------------


def _make_ai_message_with_write_todos(todos=None):
    """Create an AIMessage that calls write_todos."""
    if todos is None:
        todos = SAMPLE_TODOS
    return AIMessage(
        content="",
        tool_calls=[_tool_call("write_todos", {"todos": todos})],
    )


# Note: interrupt mechanics (interrupt fires on write_todos, resume works)
# are tested in the integration tests below, since they require real graph
# execution with a checkpointer.


# ---------------------------------------------------------------------------
# Integration tests — full HITL flow (requires Ollama + Tavily)
# ---------------------------------------------------------------------------


@pytest.fixture
def hitl_agent():
    """Create an HITL-enabled agent with in-memory checkpointer."""
    checkpointer = InMemorySaver()
    return create_deep_agent(hitl=True, checkpointer=checkpointer), checkpointer


def _resume_loop(agent, thread, initial_response):
    """Resume agent, auto-approving all subsequent interrupts until completion."""
    from langchain.agents.middleware.human_in_the_loop import HITLResponse

    result = initial_response
    state = agent.get_state(thread)

    while state.tasks:
        resume = HITLResponse(decisions=[{"type": "approve"}])
        result = agent.invoke(Command(resume=resume), config=thread)
        state = agent.get_state(thread)

    return result


@pytest.mark.integration
def test_hitl_approve_flow(hitl_agent):
    """Full flow: plan -> interrupt -> approve -> execute -> complete."""
    from langchain.agents.middleware.human_in_the_loop import HITLResponse

    agent, _ = hitl_agent
    thread = {"configurable": {"thread_id": "test-approve"}}

    # Phase 1: Agent plans, should hit interrupt on write_todos
    result = agent.invoke(
        {"messages": [("human", "Research what is MCP (Model Context Protocol)")],
         "todos": [], "files": {}},
        config=thread,
    )

    state = agent.get_state(thread)
    assert state.tasks, "Expected interrupt on write_todos"

    # Phase 2: Approve and resume until completion
    result = _resume_loop(agent, thread, result)

    # Agent should have created TODOs and written files
    todos = result.get("todos", [])
    assert len(todos) >= 1, f"Expected TODOs, got: {todos}"


@pytest.mark.integration
def test_hitl_reject_flow(hitl_agent):
    """Reject flow: plan -> interrupt -> reject -> agent receives rejection."""
    from langchain.agents.middleware.human_in_the_loop import HITLResponse

    agent, _ = hitl_agent
    thread = {"configurable": {"thread_id": "test-reject"}}

    # Phase 1: Agent plans
    result = agent.invoke(
        {"messages": [("human", "Research what is MCP (Model Context Protocol)")],
         "todos": [], "files": {}},
        config=thread,
    )

    state = agent.get_state(thread)
    assert state.tasks, "Expected interrupt on write_todos"

    # Phase 2: Reject the plan
    resume = HITLResponse(
        decisions=[{"type": "reject", "message": "Too broad, focus on security aspects only"}]
    )
    result = agent.invoke(Command(resume=resume), config=thread)

    # Agent should continue (either replan or respond to rejection)
    last_msg = result["messages"][-1]
    assert last_msg.content, "Agent should respond after rejection"
