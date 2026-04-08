"""Deep agent with TODO planning, virtual file system, and sub-agent delegation.

Demonstrates:
- DeepAgentState with todos and files fields
- write_todos / read_todos tools for plan management
- ls / read_file / write_file tools for context offloading
- think_tool for structured reflection
- task tool for sub-agent delegation with context isolation
- Mock web search (replaced with real search in M5)
"""

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

from src.file_tools import ls, read_file, write_file
from src.prompts import (
    FILE_USAGE_INSTRUCTIONS,
    SIMPLE_RESEARCH_INSTRUCTIONS,
    SUBAGENT_USAGE_INSTRUCTIONS,
    TODO_USAGE_INSTRUCTIONS,
)
from src.state import DeepAgentState
from src.task_tool import SubAgent, _create_task_tool
from src.think_tool import think_tool
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


# Default sub-agent: research agent with search + file tools + think
DEFAULT_SUBAGENTS: list[SubAgent] = [
    {
        "name": "research-agent",
        "description": (
            "Delegate research to the sub-agent researcher. "
            "Only give this researcher one topic at a time."
        ),
        "prompt": SIMPLE_RESEARCH_INSTRUCTIONS,
        "tools": ["mock_web_search", "think_tool", "ls", "read_file", "write_file"],
    },
]

# Tools available to the supervisor and sub-agents
SUPERVISOR_TOOLS = [
    write_todos,
    read_todos,
    mock_web_search,
    think_tool,
    ls,
    read_file,
    write_file,
]

SUPERVISOR_PROMPT = (
    "You are a research assistant. Help the user by planning your work "
    "with TODOs, delegating research to sub-agents, and delivering clear answers.\n\n"
    + TODO_USAGE_INSTRUCTIONS
    + "\n\n"
    + "=" * 40
    + "\n\n"
    + FILE_USAGE_INSTRUCTIONS
    + "\n\n"
    + "=" * 40
    + "\n\n"
    + SUBAGENT_USAGE_INSTRUCTIONS.format(
        max_concurrent_research_units=3,
        max_researcher_iterations=3,
    )
)


def create_deep_agent(
    model: str = "gemma4:26b",
    temperature: float = 0,
    subagents: list[SubAgent] | None = None,
):
    """Create a deep agent with TODO planning, file system, and sub-agent delegation.

    Args:
        model: Ollama model name.
        temperature: LLM temperature.
        subagents: Sub-agent configs. Defaults to a research agent with mock search.
    """
    llm = ChatOllama(model=model, temperature=temperature)

    if subagents is None:
        subagents = DEFAULT_SUBAGENTS

    task_tool = _create_task_tool(
        SUPERVISOR_TOOLS, subagents, llm, DeepAgentState
    )

    all_tools = [*SUPERVISOR_TOOLS, task_tool]

    return create_agent(
        llm,
        all_tools,
        system_prompt=SUPERVISOR_PROMPT,
        state_schema=DeepAgentState,
    ).with_config({"recursion_limit": 50})
