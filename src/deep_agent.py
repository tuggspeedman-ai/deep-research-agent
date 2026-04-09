"""Deep agent with TODO planning, virtual file system, and sub-agent delegation.

Composes all tools into a full deep research agent:
- DeepAgentState with todos and files fields
- submit_plan / write_todos / read_todos tools for plan management
- ls / read_file / write_file tools for context offloading
- think_tool for structured reflection
- tavily_search for web search with context offloading
- task tool for sub-agent delegation with context isolation
"""

import os
from datetime import datetime

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from src.file_tools import ls, read_file, write_file
from src.prompts import (
    FILE_USAGE_INSTRUCTIONS,
    RESEARCHER_INSTRUCTIONS,
    SUBAGENT_USAGE_INSTRUCTIONS,
    TODO_USAGE_INSTRUCTIONS,
)
from src.research_tools import tavily_search
from src.state import DeepAgentState
from src.task_tool import SubAgent, _create_task_tool
from src.think_tool import think_tool
from src.todo_tools import read_todos, submit_plan, write_todos


def _get_today_str() -> str:
    return datetime.now().strftime("%a %b %-d, %Y")


# Default sub-agent: research agent with search + think
DEFAULT_SUBAGENTS: list[SubAgent] = [
    {
        "name": "research-agent",
        "description": (
            "Delegate research to the sub-agent researcher. "
            "Only give this researcher one topic at a time."
        ),
        "prompt": RESEARCHER_INSTRUCTIONS.format(date=_get_today_str()),
        "tools": ["tavily_search", "think_tool"],
    },
]

# Tools available to the supervisor and sub-agents
SUPERVISOR_TOOLS = [
    submit_plan,
    write_todos,
    read_todos,
    tavily_search,
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
    model: str = "ollama:gemma4:26b",
    temperature: float = 0,
    subagents: list[SubAgent] | None = None,
    hitl: bool = False,
    checkpointer: "Checkpointer | None" = None,  # noqa: F821
):
    """Create a deep agent with TODO planning, file system, and sub-agent delegation.

    Args:
        model: Model in "provider:model" format (e.g. "openai:gpt-4o",
            "anthropic:claude-sonnet-4-5-20250514", "ollama:gemma4:26b").
        temperature: LLM temperature.
        subagents: Sub-agent configs. Defaults to a research agent with Tavily search.
        hitl: Enable human-in-the-loop plan approval via interrupt on submit_plan.
        checkpointer: LangGraph checkpointer for persistence. Required for hitl.
            If None and hitl=True, one must be provided by the runtime
            (e.g. langgraph dev).
    """
    llm = init_chat_model(model, temperature=temperature)

    if subagents is None:
        subagents = DEFAULT_SUBAGENTS

    task_tool = _create_task_tool(SUPERVISOR_TOOLS, subagents, llm, DeepAgentState)

    all_tools = [*SUPERVISOR_TOOLS, task_tool]

    middleware = []
    if hitl:
        from langchain.agents.middleware.human_in_the_loop import (
            HumanInTheLoopMiddleware,
        )

        middleware.append(
            HumanInTheLoopMiddleware(
                interrupt_on={"submit_plan": True},
            )
        )

    return create_agent(
        llm,
        all_tools,
        system_prompt=SUPERVISOR_PROMPT,
        state_schema=DeepAgentState,
        middleware=middleware,
        checkpointer=checkpointer,
    )


def _make_graph():
    """Lazy graph factory for langgraph dev server.

    langgraph dev calls this to get the compiled graph.
    Defined as a function to avoid eager LLM initialization at import time.
    """
    model = os.environ.get("MODEL", "ollama:gemma4:26b")
    return create_deep_agent(model=model, hitl=True)
