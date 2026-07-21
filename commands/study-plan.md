Quick snapshot of my learning. Do not search the web.

## If LEARNING-PROFILE is empty / nearly empty
Do not invent domains. Do onboarding in at most 3 short questions:
1. Overall level (beginner / intermediate / advanced)
2. Current focus (e.g. Python backend, React, CS fundamentals)
3. 1–3 topics I want to study now

With the answers, run:
```bash
python3 ~/.cursor/learning/cli.py init --level "..." --focus "..."
python3 ~/.cursor/learning/cli.py want --topic "..." --note "..."
```
Confirm what you saved and stop. I can ask for the snapshot again later.

## If there is a profile
Produce:
- **Solid** — advanced / stable
- **In progress** — intermediate, or repeated covered entries without leveling up
- **Queue** — open items in "Study queue"
- **Project stack** — if `LEARNING-PROJECT` / `.cursor/learning/project.md` exists
- **Candidates** — project topics not yet promoted to the global queue
- **Gaps** — showed up in context but are neither in the queue nor covered
- **Next 3 steps** — prioritized; each with 1 specific resource

Remember: active calibration = `/study-probe`. Deep track = `/study-deep`.
Manual record = `/study-log`.
