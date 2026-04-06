---
description: QA review from fresh context — spawns a reviewer subagent that defaults to rejection
---

# /review

Spawn a QA reviewer subagent with fresh context to review recent implementation work. The reviewer defaults to "NEEDS WORK" — it must be convinced the code is solid, not the other way around.

## When to Use

- After completing a milestone or multi-step feature
- Before committing a significant batch of changes
- When you want a second opinion on architectural choices

## Steps

1. **Determine review scope** — identify what was implemented since the last commit or checkpoint:
   - Run `git diff --stat` to see changed/new files
   - Run `git diff --name-only` to get the file list
   - Read `PLAN.md` for the current milestone's requirements, design decisions, and verification checklist

2. **Scale review depth** based on change magnitude:
   - Under 200 lines changed: full detail review of every line
   - 200-1000 lines: focused review on critical areas (security, API design, error handling)
   - Over 1000 lines: architectural-level review + spot-check critical paths

3. **Spawn reviewer subagent** using the Agent tool with:
   - `model: "opus"` (strongest reasoning for finding subtle issues)
   - The prompt template below, filled in with the scope and context

4. **Process the report** — when the reviewer returns:
   - If PASS: proceed to commit/wrapup
   - If NEEDS WORK: fix critical issues, then re-review (or fix warnings at your discretion)
   - Don't argue with the reviewer — fix the issues or explain to the user why you disagree

## Reviewer Prompt Template

Use this as the prompt for the Agent tool. Fill in `{{SCOPE}}`, `{{FILES}}`, `{{REQUIREMENTS}}`, and `{{VERIFICATION_CHECKLIST}}`.

```
You are a QA Reviewer for the LangChain Deep Agents project. Your job is to review recent implementation work with fresh eyes. Default to "NEEDS WORK" — only pass if everything is genuinely solid.

## Context
{{SCOPE}}

## Files to Review
{{FILES}}

## Requirements & Design Decisions
{{REQUIREMENTS}}

## Your Task

1. **Read all files listed above** — every new and modified file
2. **Check for these specific issues:**

### Correctness (CRITICAL)
- Does the implementation match the requirements?
- LangGraph graph structure: are nodes and edges wired correctly?
- Tool definitions: do they match what Gemma 4 expects?
- Edge cases: empty inputs, missing fields, malformed LLM responses
- Error handling: uncaught exceptions, missing error cases
- Resource leaks: unclosed connections, missing cleanup

### LangGraph Patterns (HIGH)
- State schema consistency across nodes
- Checkpointing: is state serializable?
- Human-in-the-loop: are interrupt points correct?
- Sub-agent delegation: proper state isolation?

### Code Quality (MEDIUM)
- Dead code, unused imports
- Duplicated logic that should be shared
- Functions > 50 lines, files > 400 lines, nesting > 4 levels
- Inconsistent naming between files
- Missing type hints

### Testing (MEDIUM)
- Are key paths tested?
- Do tests actually assert meaningful things?
- Are LLM calls properly mocked in unit tests?

3. **Run the tests** — `pytest` and verify they pass

4. **Return a structured report:**

## Status: PASS | NEEDS WORK

## Critical Issues (must fix before shipping)
- [file:line] Description. Why it matters. How to fix.

## Warnings (should fix, not blocking)
- [file:line] Description. Why it matters.

## Observations (nice to fix, low priority)
- [file:line] Description.

## What Works Well
- Positive observations about the implementation.

Be thorough. Be harsh. The implementer wants to ship quality code, not hear that everything looks good.
```

## Rules

- Always use `model: "opus"` for the reviewer — it needs strong reasoning
- Never skip the review for milestone completions, even if you're confident
- The reviewer's report is advisory — the user makes the final call on what to fix
- After fixing critical issues from a review, consider re-running `/review` to verify fixes
