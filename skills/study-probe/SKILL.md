---
name: study-probe
description: Actively assesses understanding with practical questions, scores evidence, and updates the Learning Tutor profile. Use when the user asks to test their knowledge, verify what they know, calibrate their level, or invokes /study-probe.
---

# Study Probe

Assess knowledge; do not infer mastery merely because a topic appeared in chat.
Read [references/assessment-rubric.md](references/assessment-rubric.md) before
writing questions or scoring answers.

## Load state

Use injected `LEARNING-PROFILE` / `LEARNING-PROJECT`, or run:

```bash
python3 ~/.cursor/learning/cli.py show
python3 ~/.cursor/learning/cli.py project-show
```

## Select topics

Choose 5-10 transferable concepts from:

1. Open global queue items
2. Current global focus
3. Project candidates generalized beyond repo-specific names

Never test trivia about local symbols, paths, environment variables, or class
names. If a local detail reveals a broader concept, test the broader concept.

## Run the probe

1. Ask 5-10 short practical questions in one block.
2. Wait for the user's answers before writing any profile state.
3. Score each answer with the assessment rubric.
4. Persist results:

```bash
python3 ~/.cursor/learning/cli.py covered --topic "..." --level "..." --note "study-probe: evidence summary"
python3 ~/.cursor/learning/cli.py want --topic "..." --note "gap from study-probe"
python3 ~/.cursor/learning/cli.py project-drop --topic "..."
python3 ~/.cursor/learning/cli.py project-sync --probe-summary "..."
```

Only record `covered` when the answer provides positive evidence. A partial or
incorrect answer remains in or enters the queue. Remove a project candidate only
when its transferable concept was demonstrated.

## Report

Summarize:

- Evidence accepted as covered
- Gaps added to the queue
- One recommended next action

Keep the report concise and distinguish global learning from project-local context.
