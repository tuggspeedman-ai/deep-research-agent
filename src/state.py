"""State definitions for the deep agent.

Defines the Todo type and DeepAgentState used across M2+.
The files field will be added in M3.
"""

from typing import Literal, NotRequired

from langchain.agents import AgentState
from typing_extensions import TypedDict


class Todo(TypedDict):
    """A structured task item for tracking progress.

    Attributes:
        content: Short, specific description of the task.
        status: Current state — pending, in_progress, or completed.
    """

    content: str
    status: Literal["pending", "in_progress", "completed"]


class DeepAgentState(AgentState):
    """Extended agent state with TODO-based task planning.

    Inherits messages from AgentState. The todos field uses full-overwrite
    semantics (no reducer) — the LLM rewrites the entire list each update.
    """

    todos: NotRequired[list[Todo]]
