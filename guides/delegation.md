# Delegation Guide

## When to Delegate

Before each task, assess: handle directly or delegate?

**Delegate when any of these apply:**
- Task benefits from fresh context (complex reasoning, independent scope)
- You can work on something else in parallel
- Context is getting tight (over 50%)
- Task is research or review (always delegate these)

**Work directly when:**
- Simple sequential task with spacious context
- Faster iteration matters (tight feedback loop with the user)
- Task requires context from the current conversation that's hard to summarize

**Default model: `model: "opus"`** for all subagents. Don't downgrade unless there's a specific reason.

## The Delegation Loop

```
ORCHESTRATOR (main session — holds plan, assesses each task)
     |
     | 1. Write task spec (goal, files owned, boundaries, how to verify)
     |
     |---> WORKER (fresh context, Opus)
     |         |
     |         | Returns: status + summary + concerns + files changed
     |         |
     |    3. Validate report — sections present? Status DONE or BLOCKED?
     |         |
     |         | if BLOCKED -> unblock and re-dispatch
     |         | if DONE -->
     |
     |---> /review (fresh context — see .claude/commands/review.md)
     |         |
     |         | Returns: PASS / NEEDS_WORK with structured issues
     |         |
     |    5. Act on review
     |         | NEEDS_WORK -> fix critical issues, re-review if needed
     |         | PASS -> integrate and move to next task
     |
     +-- Next task
```

**Scale the loop to the task.** A simple bug fix: implement directly, spot-check. A milestone completion: implement (directly or delegated), then `/review` with fresh context.

## Handoff Format

Every subagent should receive:

1. **What to change** — the specific goal
2. **Which files they own** — explicit scope
3. **What not to touch** — boundaries
4. **How to verify** — test, command, or check to confirm it works

**Context discipline:** Paste relevant context into the prompt. Don't say "read CLAUDE.md." The subagent can't see your conversation history.

## Implementer Prompt Template

```
You are implementing a specific task for the LangChain Deep Agents project.

## Task
[What to build/change — specific deliverable]

## Context
[Relevant code, conventions, schema, constraints.
Paste what the agent needs — don't reference files it can't see.]

## Scope
- Files you own: [explicit list]
- Do NOT touch: [boundaries]

## Rules
1. Implement exactly what is described. Do not add features or refactor surrounding code.
2. If the spec is ambiguous, report NEEDS_CONTEXT with specific questions.
3. BLOCKED is always better than wrong.
4. Your output will be reviewed by a separate agent.

## Report Format
Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
Summary: [What was accomplished in 2-3 sentences]
Concerns: [Anything the reviewer should look at, or "None"]
Files changed: [List with one-line descriptions]
```

## Reviewer

Use the `/review` command (`.claude/commands/review.md`). It spawns an Opus reviewer with:
- Structured checklist (correctness, LangGraph patterns, code quality, testing)
- Depth scaling based on change magnitude
- Test execution via pytest
- Structured report: PASS / NEEDS WORK with categorized issues

Don't duplicate the reviewer prompt here — the command is the source of truth.

## Before Dispatching

- [ ] Task description is self-contained (agent doesn't need conversation history)
- [ ] Context is pasted, not referenced
- [ ] Report format is included in the prompt
- [ ] Model is set to Opus

## After Receiving

- [ ] All required report sections are present
- [ ] If sections are missing, push back — don't accept incomplete reports
- [ ] For reviews: fix critical issues before proceeding
