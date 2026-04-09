"""Minimal example: create and invoke a deep research agent.

Usage:
    python examples/simple_query.py
"""

from src.deep_agent import create_deep_agent


def main():
    agent = create_deep_agent()
    result = agent.invoke(
        {
            "messages": [{"role": "user", "content": "What is LangGraph?"}],
            "todos": [],
            "files": {},
        }
    )

    # Print the final AI response
    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(msg.content)
            break


if __name__ == "__main__":
    main()
