---
name: study-plan
description: >-
  Read-only progress snapshot of the learning profile — what is covered, what is
  in the study queue, and what to study next. Use when the user wants to review
  or plan their learning state, or invokes /study-plan. Not for quizzes or
  knowledge verification, not for answering a concept question, not for building
  a curated study track, and never for profile writes.
---

# Study Plan

A passive snapshot. Do not test the user, do not search the web, and do not run
`init`, `want`, or `covered` — this skill has no write path into the profile.

## Load state

Use `LEARNING-PROFILE` and `LEARNING-PROJECT` from context when they are already
present. Session inject is best-effort, so when either is missing, read it:

```bash
python3 ~/.cursor/learning/cli.py show
python3 ~/.cursor/learning/cli.py project-show
```

Those commands are the source of truth — never invent a level or a queue from
memory. The global profile is authoritative for the queue and covered knowledge;
the project sheet only supplies local stack and candidates.

## Empty profile

Report that the profile is empty in one short message and direct the user to
`/study-log` to set level and focus and queue their first topics. Do not onboard
here.

## Missing project sheet

If the repo has clear stack signals (`package.json`, `pyproject.toml`,
`Dockerfile`, `compose.yml`, `Cargo.toml`, README…) and there is no useful
`LEARNING-PROJECT`, you may create the local sheet once with 3–8 specific
candidates — no bare base languages:

```bash
python3 ~/.cursor/learning/cli.py project-sync --stack "A;B" --candidates "topic1;topic2;topic3"
```

This is local-sheet discovery, not a global learning write. Only do it when the
sheet is missing or empty, or when the user asks — not on every invocation.

## The snapshot

- **Solid** — advanced or stable knowledge
- **In progress** — intermediate or repeatedly encountered topics
- **Queue** — open global queue items
- **Project context** — stack and local candidates, clearly labeled as local
- **Gaps** — transferable concepts not yet queued or covered. Report them only:
  recommend `/study-log`, or note that conceptual questions queue themselves.
  Never call `want` yourself.
- **Next 3 steps** — prioritized and actionable

Keep gaps transferable — apply the test *"Would this still be useful without
opening this repository?"* Yes → a real gap worth listing. No → project-local;
leave it out of the global list even if it is a strong local candidate. Partly
→ describe the broader concept, not the local instance.

Close by offering `/study-probe` to verify a topic or `/study-deep <topic>` for
a curated track.
