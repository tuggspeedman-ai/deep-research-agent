"""TODO management tools for task planning and progress tracking.

Provides write_todos (overwrites the list via Command) and read_todos
(reads from state, returns formatted string).
"""

from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from src.prompts import WRITE_TODOS_DESCRIPTION
from src.state import DeepAgentState, Todo


@tool(description=WRITE_TODOS_DESCRIPTION, parse_docstring=True)
def write_todos(
    todos: list[Todo],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Create or update the agent's TODO list.

    Args:
        todos: List of Todo items with content and status fields.
        tool_call_id: Tool call identifier for message response.
    """
    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(
                    f"Updated todo list to {todos}",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )


@tool(parse_docstring=True)
def read_todos(
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    """Read the current TODO list from agent state.

    Use this after completing a task to remind yourself of the plan
    and decide what to do next.

    Args:
        state: Injected agent state containing the current TODO list.
        tool_call_id: Injected tool call identifier.
    """
    todos = state.get("todos", [])
    if not todos:
        return "No todos currently in the list."

    status_icon = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}
    lines = []
    for i, todo in enumerate(todos, 1):
        icon = status_icon.get(todo["status"], "[?]")
        lines.append(f"{i}. {icon} {todo['content']} ({todo['status']})")

    return "Current TODO List:\n" + "\n".join(lines)
