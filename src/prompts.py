"""Prompt templates and tool descriptions for the deep agent."""

WRITE_TODOS_DESCRIPTION = """\
Create and manage structured task lists for tracking progress through complex workflows.

## When to Use
- Multi-step or non-trivial tasks requiring coordination
- When user provides multiple tasks or explicitly requests a todo list
- Avoid for single, trivial actions unless directed otherwise

## Structure
- Maintain one list containing multiple todo objects (content, status)
- Use clear, actionable content descriptions
- Status must be: pending, in_progress, or completed

## Best Practices
- Only one in_progress task at a time
- Mark completed immediately when task is fully done
- Always send the full updated list when making changes
- Prune irrelevant items to keep list focused

## Progress Updates
- Call write_todos again to change task status or edit content
- Reflect real-time progress; don't batch completions
- If blocked, keep in_progress and add new task describing blocker

## Parameters
- todos: List of TODO items with content and status fields

## Returns
Updates agent state with new todo list."""

TODO_USAGE_INSTRUCTIONS = """\
Based upon the user's request:
1. Use the write_todos tool to create TODOs at the start of a \
user request, per the tool description.
2. After you accomplish a TODO, use the read_todos tool to read \
the TODOs and remind yourself of the plan.
3. Reflect on what you've done and the TODO list.
4. Mark your task as completed, and proceed to the next TODO.
5. Continue this process until you have completed all TODOs.

IMPORTANT: Always create a research plan of TODOs and conduct \
research following the above guidelines for ANY user request.
IMPORTANT: Aim to batch research tasks into a *single TODO* in \
order to minimize the number of TODOs you have to keep track of."""

SIMPLE_RESEARCH_INSTRUCTIONS = """\
IMPORTANT: Just make a single call to the web_search tool and use the result \
provided by the tool to answer the user's question."""

LS_DESCRIPTION = """\
List all files in the virtual filesystem stored in agent state.

Shows what files currently exist in agent memory. Use this to orient yourself \
before other file operations and maintain awareness of your file organization.

No parameters required — simply call ls() to see all available files."""

READ_FILE_DESCRIPTION = """\
Read content from a file in the virtual filesystem with optional pagination.

Returns file content with line numbers (like cat -n) and supports reading \
large files in chunks to avoid context overflow.

Parameters:
- file_path (required): Path to the file you want to read
- offset (optional, default=0): Line number to start reading from
- limit (optional, default=2000): Maximum number of lines to read

Essential before making any edits to understand existing content."""

WRITE_FILE_DESCRIPTION = """\
Create a new file or completely overwrite an existing file in the virtual filesystem.

Use for storing research results, saving context, or writing reports. \
Files are stored persistently in agent state across tool calls.

Parameters:
- file_path (required): Path where the file should be created/overwritten
- content (required): The complete content to write to the file

Important: This replaces the entire file content."""

TASK_DESCRIPTION_PREFIX = """\
Delegate a task to a specialized sub-agent with isolated context. \
Available agents for delegation are:
{other_agents}
"""

SUBAGENT_USAGE_INSTRUCTIONS = """\
You can delegate tasks to sub-agents.

<Task>
Your role is to coordinate research by delegating specific research tasks to sub-agents.
</Task>

<Available Tools>
1. **task(description, subagent_type)**: Delegate research tasks to specialized sub-agents
   - description: Clear, specific research question or task
   - subagent_type: Type of agent to use (e.g., "research-agent")
2. **think_tool(reflection)**: Reflect on the results of each delegated task and plan next steps.
   - reflection: Your detailed reflection on the results of the task and next steps.

**PARALLEL RESEARCH**: When you identify multiple independent research directions, \
make multiple **task** tool calls in a single response to enable parallel execution. \
Use at most {max_concurrent_research_units} parallel agents per iteration.
</Available Tools>

<Hard Limits>
- **Bias towards focused research** - Use single agent for simple questions, \
multiple only when clearly beneficial
- **Stop when adequate** - Don't over-research; stop when you have sufficient information
- **Limit iterations** - Stop after {max_researcher_iterations} task delegations
</Hard Limits>

<Scaling Rules>
**Simple fact-finding**: 1 sub-agent.
**Comparisons**: 1 sub-agent per element being compared.
**Multi-faceted research**: Parallel agents for different aspects.

**Important Reminders:**
- Each **task** call creates a dedicated research agent with isolated context
- Sub-agents can't see each other's work — provide complete standalone instructions
- Use clear, specific language — avoid acronyms in task descriptions
</Scaling Rules>"""

FILE_USAGE_INSTRUCTIONS = """\
You have access to a virtual file system to help you retain and save context.

## Workflow Process
1. **Orient**: Use ls() to see existing files before starting work
2. **Save**: Use write_file() to store the user's request \
so you can reference it later
3. **Research**: Proceed with research. Save verbose results \
to files, keep summaries in messages
4. **Read**: Once satisfied with collected sources, read the \
files and use them to answer the user's question"""
