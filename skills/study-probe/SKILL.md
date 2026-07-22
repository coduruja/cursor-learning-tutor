---
name: study-probe
description: >-
  Test one topic with practical questions, score the answers, and record the
  result as evidence. Use when the user asks to be tested, quizzed, or assessed;
  claims they understand, finished studying, or read the material on a topic; or
  just completed a study-deep track. This is the only skill that may write
  covered. Not for passive profile summaries or progress snapshots.
---

# Study Probe

Assess knowledge. Never infer mastery from exposure, self-report, or finishing a
study track. Read
[references/assessment-rubric.md](references/assessment-rubric.md) before
writing questions or scoring answers.

## Load state

Use injected `LEARNING-PROFILE` / `LEARNING-PROJECT` when present. Session
inject is best-effort — if either is missing, run:

```bash
python3 ~/.cursor/learning/cli.py show
python3 ~/.cursor/learning/cli.py project-show
```

## Select exactly one topic

1. The topic the user named, or
2. The first open global queue item:

   ```bash
   python3 ~/.cursor/learning/cli.py queue-next
   ```

3. Or an explicit choice from a short list (queue, focus, or a generalized
   project candidate).

Never run a multi-topic exam. Never test trivia about local symbols, paths,
environment variables, or class names — if a local detail is the starting point,
rename it to the broader concept and probe that instead.

## Run the probe

1. Ask **5 to 10** short practical questions about that one topic, in one block.
   Fewer than 5 questions is an incomplete probe and must not write `covered`.
2. Wait for the user's answers before writing any profile state.
3. Score each answer with the assessment rubric.

## Persist the result — this topic only

If at least **50%** of the answers are covered-quality:

```bash
python3 ~/.cursor/learning/cli.py covered --topic "TOPIC" --level "beginner|intermediate|advanced" --note "what the answers demonstrated"
```

Otherwise keep or add the topic as a gap, and do **not** write `covered`:

```bash
python3 ~/.cursor/learning/cli.py want --topic "TOPIC" --note "probe gaps: ..."
```

The evidence note says what the user demonstrated, not "passed probe". If
`~/.cursor/learning/cli.py` does not exist, you cannot record a probe result:
say so and tell the user a new chat lets `sessionStart` install the CLI. The
`LEARNING-WANT` marker fallback exists for gaps only — there is no `covered`
marker, by design.

## Project sheet hygiene

Only after the transferable concept was actually demonstrated:

```bash
python3 ~/.cursor/learning/cli.py project-drop --topic "..."
python3 ~/.cursor/learning/cli.py project-sync --probe-summary "..."
```

## Report

- Topic probed
- Evidence accepted as covered, or why it was not
- Queue updates
- One recommended next action

Keep it concise, and keep global learning visibly separate from project-local
context.
