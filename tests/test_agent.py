"""Tests for the ReAct agent with custom state, InjectedState, and Command."""

import pytest
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from src.agent import create_calc_agent


@pytest.fixture
def llm():
    return ChatOllama(model="gemma4:26b", temperature=0)


@pytest.fixture
def agent():
    return create_calc_agent()


def invoke(agent, prompt: str) -> dict:
    """Run the agent and return final state."""
    return agent.invoke({"messages": [("human", prompt)]})


def test_single_calculation(agent):
    """Agent uses calculator tool and returns a result."""
    result = invoke(agent, "What is 12 * 7?")
    assert len(result["ops"]) >= 1
    assert "84" in result["ops"][-1]


def test_multi_step(agent):
    """Agent handles multiple calculations in sequence."""
    result = invoke(
        agent, "Calculate 10 + 5, then multiply that result by 3."
    )
    assert len(result["ops"]) >= 2


def test_history_tool(agent):
    """Agent can read operation history via InjectedState."""
    result = invoke(
        agent, "Calculate 9 * 9, then show me the history."
    )
    assert len(result["ops"]) >= 1
    # Verify a ToolMessage contains the history content
    messages = result["messages"]
    history_found = any(
        "9" in m.content and "81" in m.content
        for m in messages
        if hasattr(m, "content")
        and isinstance(m.content, str)
        and m.type == "tool"
    )
    assert history_found, "Expected a tool message with history"


def test_division_by_zero(agent):
    """Agent handles division by zero gracefully."""
    result = invoke(agent, "What is 5 divided by 0?")
    messages = result["messages"]
    all_text = " ".join(
        m.content
        for m in messages
        if hasattr(m, "content") and isinstance(m.content, str)
    )
    assert "zero" in all_text.lower() or "error" in all_text.lower()


def test_state_accumulates(agent):
    """Operations accumulate in state via the reduce_list reducer."""
    result = invoke(agent, "First add 1 and 2, then add 3 and 4.")
    assert len(result["ops"]) >= 2


def test_structured_output(llm):
    """Gemma 4 supports .with_structured_output() for Pydantic models."""

    class CityInfo(BaseModel):
        name: str
        country: str

    structured = llm.with_structured_output(CityInfo)
    result = structured.invoke("Tell me about Paris, France.")
    assert isinstance(result, CityInfo)
    assert len(result.name) > 0
    assert len(result.country) > 0


def test_parallel_tool_calls(llm):
    """Gemma 4 can make multiple tool calls in a single response."""
    from langchain_core.tools import tool

    @tool
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    @tool
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b

    llm_with_tools = llm.bind_tools([add, multiply])
    response = llm_with_tools.invoke(
        "What is 3+4 and 5*6? Calculate both."
    )
    assert len(response.tool_calls) == 2
    names = {tc["name"] for tc in response.tool_calls}
    assert names == {"add", "multiply"}
