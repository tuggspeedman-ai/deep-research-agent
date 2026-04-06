# Verification Guide

Read this when verifying work, writing quality gates, or setting up test strategies.

## Core Rule

Never mark a task complete without proving it works. Give Claude a verification feedback loop (test suite, browser, bash command) — this 2-3x's output quality.

## Match Harness to Task

Every harness component encodes an assumption about a model limitation. If the limitation doesn't apply, the component is overhead. Simplify first; add complexity only where capabilities hit a ceiling.

| Task Complexity | Harness Level | Evaluator |
|----------------|--------------|-----------|
| Bug fix, small feature | Solo agent + hooks (linter, type check) | None — hooks are enough |
| Multi-file feature | Solo agent + test suite as exit criteria | Tests are the evaluator |
| Complex multi-node graph | Orchestrator + separate Reviewer subagent | Dedicated — runs tests, checks graph execution |
| Ambitious long-running build | Generator-evaluator loop with task contracts | Iterative — rubric-based scoring, multiple rounds |

## Test-First Bug Fixing

When a bug is reported:

1. Write a test that reproduces it (proves the bug exists)
2. Fix the bug (proves the test passes)
3. Check: are there other instances of the same mistake?
4. Write tests that catch the whole class of similar bugs
5. If it reveals a gap in instructions, update CLAUDE.md

## Task Contracts (End-Conditions)

Agents know how to start tasks but not how to end them — leading to stubs and premature "done."

**The contract pattern:**
1. Create a `{TASK}_CONTRACT.md` specifying all required verification
2. Include: tests that must pass (agent may NOT edit the tests), screenshots to verify design/behavior
3. Use a stop-hook to prevent session termination until all items pass
4. Vet the tests yourself — then you have peace of mind

For automation, prefer **one fresh session per contract** over long-running sessions. Context bleed from unrelated contracts causes drift.

## The Reality Checker Pattern

A dedicated QA subagent that **defaults to rejection**. Implemented as the `/review` command (`.claude/commands/review.md`).

- Triggered after milestone completion or significant implementation work
- Opus model, fresh context — doesn't share the implementer's assumptions
- Receives: scope, file list, requirements, verification checklist
- Returns: structured PASS / NEEDS WORK with categorized issues
- Fix critical issues before proceeding; warnings at your discretion

## LangGraph-Specific Verification

When verifying LangGraph agents:
1. Does the graph compile? (`graph.compile()` succeeds)
2. Can it handle a simple end-to-end query?
3. Does checkpointing work? (save state, restore, continue)
4. Do tool calls produce valid responses from Gemma 4?
5. Does streaming work? (token-level and step-level)

## Tests as Handoff Contracts

When using an orchestrator, have the planning step write tests *before* the implementer starts. This:
- Gives the Reality Checker objective criteria
- Avoids self-evaluation bias (same agent writing code and tests)
- Creates a clear "done" signal

## Operationalize Every Fix

After fixing a bug, don't stop:

1. Write tests that would have caught it AND all similar bugs
2. Check: are there other instances of the same mistake in the codebase?
3. Under what conditions might similar issues arise in the future?
4. If it reveals a gap in workflow or instructions -> update CLAUDE.md or the relevant guide

Every bug is a learning opportunity. Extract the lesson and encode it so it can't recur.
