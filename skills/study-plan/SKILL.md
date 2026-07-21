---
name: study-plan
description: Provides a read-only snapshot of the Learning Tutor profile — covered topics, saved study queue, progress, and recommended next steps. Use for requests to view existing learning state or decide what to study next. Do not use for quizzes, knowledge verification, or profile writes.
---

# Study Plan

Produce a passive, **read-only** snapshot of the user's learning state. Do not
test the user, do not search the web, and do not run `init`, `want`, or
`covered`.

## Load state

```bash
python3 ~/.cursor/learning/cli.py show
python3 ~/.cursor/learning/cli.py project-show
```

Use `LEARNING-PROFILE` and `LEARNING-PROJECT` from context when already present.
The global profile is authoritative for queue and covered knowledge; the project
sheet only supplies local stack and candidates.

## Missing project sheet

If the repo has clear stack signals (`package.json`, `pyproject.toml`,
`Dockerfile`, `compose.yml`, `Cargo.toml`, README, etc.) and there is no useful
`LEARNING-PROJECT`, you may sync 3–8 specific candidates once (no bare base
languages):

```bash
python3 ~/.cursor/learning/cli.py project-sync --stack "A;B" --candidates "topic1;topic2;topic3"
```

Do not sync on every invocation — only when the sheet is missing/empty or the
user asks. This is local-sheet discovery, not a global learning write.

## Empty profile

Report that the profile is empty in one short message and direct the user to
`/study-log` to set level/focus and queue the first topics. Do not onboard here.

## Existing profile

Return a concise snapshot:

- **Solid** — advanced or stable knowledge
- **In progress** — intermediate or repeatedly encountered topics
- **Queue** — open global queue items
- **Project context** — stack and local candidates, clearly labeled as local
- **Gaps** — transferable concepts not already queued or covered (report only;
  recommend `/study-log` or note that conceptual questions may auto-queue —
  never call `want` yourself)
- **Next 3 steps** — prioritized and actionable

Apply the `project-learning-boundary` transferability test when labeling gaps
(one-line reminder only; do not restate the full gate).

End by offering `/study-probe` for active assessment or `/study-deep <topic>`
for a curated track.
