---
name: concept-gap-capture
description: >-
  Use when the user asks what/how/why something is, how A differs from B, or
  shows a conceptual gap while exploring code (any language)—even if they don't
  say "study" or "queue." Separates understanding-questions from agent tasks,
  clarifies project-unfamiliarity vs missing concepts, and adds transferable
  topics to the study queue when missing. Do not use for pure implement/fix/
  refactor with no learning intent, quizzes, or curated study tracks.
---

# Concept gap capture

Capture at most **one** transferable study topic when the user is trying to
*understand* something—not when they only want work done.

## 1. Classify the turn

| Kind | Signals | Action |
|------|---------|--------|
| `agent_task` | implement, fix, refactor, “do X in the repo” | Do the work. Stop. No queue write. |
| `concept_gap` | definition, mechanism, purpose/why, contrast between concepts; not aimed at a specific file/symbol | Continue from step 3. |
| `repo_question` | asks about this codebase (file, module, path, symbol, “how does this project…”) | Continue from step 2. |

If unclear between `agent_task` and a question, prefer asking one clarifying
question before writing the queue.

## 2. Repo question: concept vs project familiarity

Ask **one or two** short questions before assuming a study topic, for example:

- Are you unsure what this *part of the project* does, or what the underlying
  *concept/tool* is (e.g. Docker, hooks, HTTP)?
- If you already knew the concept, would the code make sense?

Then:

- **Project unfamiliarity** → explain from the repo; no global queue write
  (optional: local note in `.cursor/learning/project.md` only if useful).
- **Missing concept** → treat as `concept_gap` with a generalized topic
  (not the raw symbol/path). Continue from step 3.
- **Both** → explain the local bit briefly; queue only the transferable concept.

## 3. Explain

Answer the question (prefer `learning-explanations` style when teaching).
Do not announce internal labels (`concept_gap`, etc.) unless asked.

## 4. Check the study queue

```bash
python3 ~/.cursor/learning/cli.py show
```

If the topic (or a clear alias) is already queued or covered, say so in one
line and do **not** add a duplicate.

## 5. Add if missing

```bash
python3 ~/.cursor/learning/cli.py want --topic "TOPIC" --note "why"
```

If the CLI is missing:

```text
<!-- LEARNING-WANT topic="TOPIC" note="why" -->
```

Then one confirmation line after a successful write.

## MUST NOT

- Queue bare generics (code, file, error…) or bare base languages (Python, JS…).
- Queue raw repo jargon with no transferable concept.
- Queue more than one topic in this turn.
- Recommend more than 1–2 named sources, or say “search for X”.
- Run deep research / build a syllabus here → use `study-deep`.
