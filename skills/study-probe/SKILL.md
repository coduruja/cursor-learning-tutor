---
name: study-probe
description: Tests understanding of one named or selected topic by asking practical questions, scoring the answers, and updating the profile from evidence. Use when the user asks to be tested, quizzed, or assessed; claims they understand, finished studying, or read the material on a topic; or after a study-deep track for that topic. Do not use for passive profile summaries or study-plan requests.
---

# Study Probe

Assess knowledge; do not infer mastery from exposure, self-report, or finishing
a study track. Read
[references/assessment-rubric.md](references/assessment-rubric.md) before
writing questions or scoring answers.

## Load state

Use injected `LEARNING-PROFILE` / `LEARNING-PROJECT` when present. Session
inject is best-effort — if either is missing, run:

```bash
python3 ~/.cursor/learning/cli.py show
python3 ~/.cursor/learning/cli.py project-show
```

## Select one topic

Pick **exactly one** transferable topic for this probe:

1. The topic the user named, or
2. The first open global queue item (`queue-next`), or
3. An explicit choice among a short list (queue / focus / a generalized project
   candidate)

Never run a multi-topic exam. Never test trivia about local symbols, paths,
environment variables, or class names. If a local detail is the starting point,
apply the project-learning-boundary transferability test and probe the broader
concept instead.

## Run the probe

1. Ask **5 to 10** short practical questions about that one topic, in one block.
   Fewer than 5 questions is an incomplete probe and must not write `covered`.
2. Wait for the user's answers before writing any profile state.
3. Score each answer with the assessment rubric.
4. Persist results for **this topic only**:
   - If at least **50%** of the answers are correct → `covered` with a short
     evidence note and an appropriate level.
   - Otherwise keep or add `want` for the topic; do **not** write `covered`.
   - Persist `want` / `covered` through the Learning Tutor recording policy
     (do not duplicate the CLI or markers here).
   - Probe-specific project sheet hygiene:

```bash
python3 ~/.cursor/learning/cli.py project-drop --topic "..."
python3 ~/.cursor/learning/cli.py project-sync --probe-summary "..."
```

Remove a project candidate only when its transferable concept was demonstrated.
## Report

Summarize:

- Topic probed
- Evidence accepted as covered (or why not)
- Queue updates
- One recommended next action

Keep the report concise and distinguish global learning from project-local
context.
