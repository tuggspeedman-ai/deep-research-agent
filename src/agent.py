"""ReAct agent built with create_agent and Gemma 4 via Ollama.

Demonstrates:
- create_agent with a custom state schema
- InjectedState for reading graph state from tools
- Command for updating state directly from tools
- InjectedToolCallId for proper tool message responses
"""

from typing import Annotated, Literal

from langchain.agents import AgentState, create_agent
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langchain_ollama import ChatOllama
from langgraph.prebuilt import InjectedState
from langgraph.types import Command


def reduce_list(left: list | None, right: list | None) -> list:
    """Merge two lists, handling None values."""
    if not left:
        left = []
    if not right:
        right = []
    return left + right


class CalcState(AgentState):
    """Agent state with operation history tracking."""

    ops: Annotated[list[str], reduce_list]


@tool
def calculator(
    operation: Literal["add", "subtract", "multiply", "divide"],
    a: int | float,
    b: int | float,
    state: Annotated[CalcState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Perform a calculation and record it in the operation history.

    Args:
        operation: The math operation to perform.
        a: First number.
        b: Second number.
    """
    if operation == "divide" and b == 0:
        return Command(
            update={
                "messages": [
                    ToolMessage("Error: division by zero", tool_call_id=tool_call_id)
                ],
            }
        )

    ops_map = {
        "add": lambda: a + b,
        "subtract": lambda: a - b,
        "multiply": lambda: a * b,
        "divide": lambda: a / b,
    }
    result = ops_map[operation]()

    entry = f"{a} {operation} {b} = {result}"
    return Command(
        update={
            "ops": [entry],
            "messages": [ToolMessage(str(result), tool_call_id=tool_call_id)],
        },
    )


@tool
def get_history(
    state: Annotated[CalcState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Get the history of all calculations performed so far."""
    ops = state.get("ops", [])
    if not ops:
        summary = "No calculations yet."
    else:
        lines = [f"  {i+1}. {op}" for i, op in enumerate(ops)]
        summary = "Calculation history:\n" + "\n".join(lines)

    return Command(
        update={
            "messages": [ToolMessage(summary, tool_call_id=tool_call_id)],
        },
    )


SYSTEM_PROMPT = """\
You are a calculator assistant. Use the calculator tool for math operations.
Use the get_history tool when asked about previous calculations.
Always use tools — never calculate in your head."""

TOOLS = [calculator, get_history]


def create_calc_agent(model: str = "gemma4:26b", temperature: float = 0):
    """Create a calculator agent with operation history tracking."""
    llm = ChatOllama(model=model, temperature=temperature)
    return create_agent(
        llm,
        TOOLS,
        system_prompt=SYSTEM_PROMPT,
        state_schema=CalcState,
    ).with_config({"recursion_limit": 20})
