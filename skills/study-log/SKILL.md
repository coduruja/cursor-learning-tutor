---
name: study-log
description: Manually records a topic as covered or adds it to the Learning Tutor study queue. Use only when explicitly invoked with /study-log for corrections, overrides, or deliberate profile updates.
disable-model-invocation: true
---

# Study Log

Update `~/.cursor/learning/profile.md` through the stable CLI. Do not edit the
profile directly unless the CLI is unavailable.

## Decide the operation

- User describes something they learned → `covered`
- User wants to study something later → `want`
- User only invokes `/study-log` and gives no topic:
  - If the profile is empty, ask for overall level and current focus, run `init`,
    then ask for the first topic.
  - Otherwise ask whether to record a covered topic or a queue item.

## Execute

```bash
python3 ~/.cursor/learning/cli.py covered --topic "..." --level "beginner|intermediate|advanced" --note "..."
python3 ~/.cursor/learning/cli.py want --topic "..." --note "..."
python3 ~/.cursor/learning/cli.py init --level "..." --focus "..."
```

If the CLI is missing, tell the user to open a new chat so `sessionStart` can
install it. Do not search the web.

## Reply

Confirm in one line what changed and whether it was `covered` or `queue`.
