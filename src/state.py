"""State definitions for the deep agent.

Defines the Todo type and DeepAgentState used across M2+.
"""

from typing import Annotated, Literal, NotRequired

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


def file_reducer(
    left: dict[str, str] | None, right: dict[str, str] | None
) -> dict[str, str]:
    """Merge two file dictionaries, with right side taking precedence.

    Unlike todos (full-overwrite), files use a merge reducer so write_file
    only needs to send {path: content} and it merges into existing files.
    """
    if left is None:
        return right or {}
    if right is None:
        return left
    return {**left, **right}


class DeepAgentState(AgentState):
    """Extended agent state with TODO planning and virtual file system.

    Inherits messages from AgentState. The todos field uses full-overwrite
    semantics. The files field uses file_reducer for incremental merges.
    """

    todos: NotRequired[list[Todo]]
    files: Annotated[NotRequired[dict[str, str]], file_reducer]
