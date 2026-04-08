"""Reflection tool for structured thinking during research.

Provides a deliberate pause for the agent to analyze findings,
assess gaps, and plan next steps before continuing.
"""

from langchain_core.tools import tool


@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Reflect on research progress and plan next steps.

    Use after receiving results from delegated tasks or searches to assess
    what you've learned, identify gaps, and decide whether to continue
    researching or synthesize your findings.

    Args:
        reflection: Your analysis of current findings, gaps, and next steps.
    """
    return f"Reflection recorded: {reflection}"
