"""Task delegation tools for context isolation through sub-agents.

Sub-agents prevent context pollution by operating with fresh message
history containing only their specific task description. They share
the virtual file system with the supervisor via file_reducer merges.
"""

from typing import Annotated, NotRequired

from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from typing_extensions import TypedDict

from src.prompts import TASK_DESCRIPTION_PREFIX
from src.state import DeepAgentState


class SubAgent(TypedDict):
    """Configuration for a specialized sub-agent."""

    name: str
    description: str
    prompt: str
    tools: NotRequired[list[str]]


def _create_task_tool(tools, subagents: list[SubAgent], model, state_schema):
    """Create a task delegation tool that spawns sub-agents with isolated context.

    Builds an agent registry from SubAgent configs, each with selective tools
    and their own system prompt. Returns a `task` tool the supervisor can call.

    Args:
        tools: List of available tools that can be assigned to sub-agents.
        subagents: List of SubAgent configurations.
        model: The language model instance for all sub-agents.
        state_schema: The state schema (typically DeepAgentState).

    Returns:
        A 'task' tool that delegates work to specialized sub-agents.
    """
    agents = {}

    # Build tool name mapping for selective assignment
    tools_by_name = {}
    for tool_ in tools:
        if not isinstance(tool_, BaseTool):
            tool_ = tool(tool_)
        tools_by_name[tool_.name] = tool_

    # Create sub-agent instances
    for _agent in subagents:
        if "tools" in _agent:
            _tools = [tools_by_name[t] for t in _agent["tools"]]
        else:
            _tools = tools
        agents[_agent["name"]] = create_agent(
            model,
            system_prompt=_agent["prompt"],
            tools=_tools,
            state_schema=state_schema,
        )

    # Build description listing available sub-agents
    other_agents_string = "\n".join(
        f"- {_agent['name']}: {_agent['description']}" for _agent in subagents
    )

    @tool(description=TASK_DESCRIPTION_PREFIX.format(other_agents=other_agents_string))
    def task(
        description: str,
        subagent_type: str,
        state: Annotated[DeepAgentState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        """Delegate a task to a specialized sub-agent with isolated context."""
        if subagent_type not in agents:
            return (
                f"Error: invoked agent of type {subagent_type}, "
                f"the only allowed types are {list(agents.keys())}"
            )

        sub_agent = agents[subagent_type]

        # Context isolation — replace parent messages with just the task
        state["messages"] = [{"role": "user", "content": description}]

        result = sub_agent.invoke(state)

        return Command(
            update={
                "files": result.get("files", {}),
                "messages": [
                    ToolMessage(
                        result["messages"][-1].content,
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )

    return task
