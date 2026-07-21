---
name: study-plan
description: Reviews the Learning Tutor profile and project context to summarize progress, queue, gaps, and prioritized next steps. Use when the user asks what they know, what is saved for study, what to learn next, or requests /study-plan.
---

# Study Plan

Produce a passive snapshot of the user's learning state. Do not test the user
and do not search the web.

## Load state

```bash
python3 ~/.cursor/learning/cli.py show
python3 ~/.cursor/learning/cli.py project-show
```

Use `LEARNING-PROFILE` and `LEARNING-PROJECT` from context when already present.
The global profile is authoritative for queue and covered knowledge; the project
sheet only supplies local stack and candidates.

## Empty profile

Ask at most three short onboarding questions:

1. Overall level: beginner, intermediate, or advanced
2. Current focus
3. One to three topics to study now

Then run `init` and `want` through the stable CLI, confirm the saved state, and
stop.

## Existing profile

Return a concise snapshot:

- **Solid** — advanced or stable knowledge
- **In progress** — intermediate or repeatedly encountered topics
- **Queue** — open global queue items
- **Project context** — stack and local candidates, clearly labeled as local
- **Gaps** — transferable concepts not already queued or covered
- **Next 3 steps** — prioritized and actionable

Do not promote repo-specific symbols, paths, environment variables, or class
names into the global learning plan. Generalize them to a transferable concept
or keep them under project context.

End by offering `/study-probe` for active assessment or `/study-deep <topic>`
for a curated track.
