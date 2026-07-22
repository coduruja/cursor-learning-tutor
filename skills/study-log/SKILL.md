---
name: study-log
description: >-
  Explicit, manual edit of the learning profile — create it, or hand-add a topic
  to the study queue. Only ever runs when the user invokes /study-log. Never
  records covered knowledge; a claim of understanding is routed to study-probe
  instead.
disable-model-invocation: true
---

# Study Log

The explicit write path for profile creation and queue corrections. Never
auto-invoked. Do not search the web. Do not edit `profile.md` by hand — every
write goes through the CLI below.

## Decide the operation

- Wants to study something later / add to the queue → `want`, after the
  transferability check.
- Says they learned or already understand something → do **not** write
  `covered`. Hand off to a one-topic `study-probe` for that topic.
- `/study-log` with no topic:
  - Profile empty → onboarding: ask for overall level and current focus, run
    `init`, then ask which topics to queue first.
  - Otherwise → ask which topic to queue (never which to mark covered).

## Transferability

Before any global `want`:

- Transferable concept → queue it.
- Repo-local symbol, path, or env var → generalize it to the broader concept and
  queue that instead (confirm the rename with the user), or offer to keep it in
  `.cursor/learning/project.md`. The raw symbol never enters the global profile.

## Commands

```bash
python3 ~/.cursor/learning/cli.py init --level "beginner|intermediate|advanced" --focus "..."
python3 ~/.cursor/learning/cli.py want --topic "TOPIC" --note "why"
```

If `~/.cursor/learning/cli.py` does not exist, emit this marker as an isolated
final line so the `afterAgentResponse` hook can persist the queue entry, and say
it was queued via fallback:

```text
<!-- LEARNING-WANT topic="TOPIC" note="why" -->
```

There is no `covered` marker, and `init` has no fallback. Never claim a write
you could not perform — tell the user a new chat lets `sessionStart` install the
CLI.

## Reply

One line: what changed (`queue` / `init`), or that a one-topic probe was started
instead of writing `covered`.
