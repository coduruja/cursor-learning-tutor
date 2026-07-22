---
name: concept-gap-capture
description: >-
  Explain a concept the user is missing and queue it for study. Use when the
  user asks what something is, how or why it works, how A differs from B, or
  otherwise shows a conceptual gap while reading code — even mid-task, and even
  if they never say "study" or "queue". Not for implement/fix/refactor requests
  with no learning intent, not for quizzes or assessments, not for curated study
  tracks, and not for progress snapshots of the profile.
---

# Concept gap capture

Answer the question, then queue **at most one** transferable topic — and only
when the user is trying to *understand* something, not merely to get work done.

## 1. Classify the turn

| Kind | Signals | Action |
|------|---------|--------|
| `agent_task` | implement, fix, refactor, "do X in the repo" | Do the work. Stop here. No queue write. |
| `concept_gap` | definition, mechanism, purpose/why, contrast between two concepts; not aimed at a specific file or symbol | Go to step 3. |
| `repo_question` | asks about this codebase — a file, module, path, symbol, "how does this project…" | Go to step 2. |

If you cannot tell an `agent_task` from a question, ask one clarifying question
before writing anything.

## 2. Repo question: project familiarity or missing concept?

Ask one or two short questions first, for example:

- Are you unsure what this *part of the project* does, or what the underlying
  *concept/tool* is (Docker, hooks, HTTP…)?
- If you already knew the concept, would this code make sense?

Then:

- **Project unfamiliarity** → explain from the repo. No global queue write.
- **Missing concept** → treat it as a `concept_gap` under a generalized topic
  name, never the raw symbol or path. Go to step 3.
- **Both** → explain the local part briefly; queue only the transferable concept.

## 3. Explain

Lead with the main idea in plain language, add one concrete example, then say
why it matters. Never announce the internal labels above.

## 4. Check the queue before writing

```bash
python3 ~/.cursor/learning/cli.py show
```

If the topic or a clear alias is already queued or covered, say so in one line
and do **not** add a duplicate.

## 5. Queue it if missing

```bash
python3 ~/.cursor/learning/cli.py want --topic "TOPIC" --note "why it came up"
```

If `~/.cursor/learning/cli.py` does not exist, do not silently drop the write.
Emit this marker as an isolated final line so the `afterAgentResponse` hook can
persist it, and say it was queued via fallback and that a new chat lets
`sessionStart` install the CLI for direct writes:

```text
<!-- LEARNING-WANT topic="TOPIC" note="why it came up" -->
```

Confirm the result in one line. If the CLI answers "Already in queue" or
"Ignored", report that and do not insist.

## Never

- Queue more than one topic in this turn.
- Queue bare generics (code, file, error…) or bare base languages (Python, JS…).
- Queue raw repo jargon that has no transferable concept behind it.
- Write `covered` here — this skill only ever queues `want`.
- Recommend more than 1–2 named sources, or say "search for X". A real study
  track is `study-deep`.
