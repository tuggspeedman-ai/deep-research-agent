"""Run a deep research query from the command line.

Usage:
    python examples/run_research.py "What is Model Context Protocol?"
    MODEL=openai:gpt-4o python examples/run_research.py "What is MCP?"
"""

import os
import sys

from src.deep_agent import create_deep_agent


def main():
    # Get query from args or prompt interactively
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your research query: ").strip()
        if not query:
            print("No query provided. Exiting.")
            sys.exit(1)

    model = os.environ.get("MODEL", "ollama:gemma4:26b")
    print(f"Using model: {model}")
    print(f"Query: {query}\n")

    agent = create_deep_agent(model=model)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": query}], "todos": [], "files": {}}
    )

    # Print the final response (last AI message)
    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print("=" * 60)
            print("RESPONSE")
            print("=" * 60)
            print(msg.content)
            break

    # Print TODO list if present
    todos = result.get("todos", [])
    if todos:
        print("\n" + "=" * 60)
        print("TODO LIST")
        print("=" * 60)
        for todo in todos:
            status = todo["status"]
            icon = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}.get(
                status, "[ ]"
            )
            print(f"  {icon} {todo['content']}")

    # Print files created
    files = result.get("files", {})
    if files:
        print("\n" + "=" * 60)
        print("FILES CREATED")
        print("=" * 60)
        for path in sorted(files.keys()):
            print(f"  {path}")


if __name__ == "__main__":
    main()
