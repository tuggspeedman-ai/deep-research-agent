"""Deep agent with TODO-based task planning.

Demonstrates:
- DeepAgentState with a todos field for tracking progress
- write_todos / read_todos tools for plan management
- Mock web search (replaced with real search in M5)
- TODO workflow: plan → work → read todos → reflect → update → repeat
"""

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

from src.prompts import SIMPLE_RESEARCH_INSTRUCTIONS, TODO_USAGE_INSTRUCTIONS
from src.state import DeepAgentState
from src.todo_tools import read_todos, write_todos

# Canned response for mock search — real Tavily search comes in M5.
_MOCK_SEARCH_RESULT = """\
The Model Context Protocol (MCP) is an open standard protocol developed \
by Anthropic to enable seamless integration between AI models and external \
systems like tools, databases, and other services. It acts as a standardized \
communication layer, allowing AI models to access and utilize data from \
various sources in a consistent and efficient manner. Essentially, MCP \
simplifies the process of connecting AI assistants to external services \
by providing a unified language for data exchange."""


@tool(parse_docstring=True)
def mock_web_search(query: str) -> str:
    """Search the web for information on a specific topic.

    Args:
        query: The search query string.
    """
    return _MOCK_SEARCH_RESULT


SYSTEM_PROMPT = (
    "You are a research assistant. Help the user by planning your work "
    "with TODOs, researching via web search, and delivering clear answers.\n\n"
    + TODO_USAGE_INSTRUCTIONS
    + "\n\n"
    + "=" * 40
    + "\n\n"
    + SIMPLE_RESEARCH_INSTRUCTIONS
)

TOOLS = [write_todos, read_todos, mock_web_search]


def create_deep_agent(model: str = "gemma4:26b", temperature: float = 0):
    """Create a deep agent with TODO planning and mock web search."""
    llm = ChatOllama(model=model, temperature=temperature)
    return create_agent(
        llm,
        TOOLS,
        system_prompt=SYSTEM_PROMPT,
        state_schema=DeepAgentState,
    ).with_config({"recursion_limit": 30})
