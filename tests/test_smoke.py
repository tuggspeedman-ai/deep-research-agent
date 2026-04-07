"""Smoke tests: verify Gemma 4 via Ollama works with LangChain."""

import pytest
from langchain_ollama import ChatOllama


@pytest.fixture
def llm():
    return ChatOllama(model="gemma4:26b", temperature=0)


def test_basic_response(llm):
    """Gemma 4 responds to a simple prompt."""
    response = llm.invoke("What is 2 + 2? Reply with just the number.")
    assert "4" in response.content


def test_tool_calling(llm):
    """Gemma 4 can call a bound tool."""

    def get_weather(city: str) -> str:
        """Get the current weather for a city."""
        return f"Sunny, 72°F in {city}"

    llm_with_tools = llm.bind_tools([get_weather])
    response = llm_with_tools.invoke("What's the weather in San Francisco?")

    assert response.tool_calls, "Expected at least one tool call"
    tool_call = response.tool_calls[0]
    assert tool_call["name"] == "get_weather"
    assert "city" in tool_call["args"]
