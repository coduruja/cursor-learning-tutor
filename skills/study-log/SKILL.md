---
name: study-log
description: Manually initializes the Learning Tutor profile or adds a topic to the study queue. Use only when explicitly invoked with /study-log for corrections, queue updates, or empty-profile setup. Do not use to attest covered knowledge.
disable-model-invocation: true
---

# Study Log

Explicit write path for profile creation and queue updates. Never auto-invoked.
Do not edit `profile.md` directly. Persist `want` through the Learning Tutor
recording policy (do not duplicate the `want`/`covered` CLI or markers here).
Do not search the web.

## Decide the operation

- User wants to study something later / add to queue → `want` (after the
  transferability check below)
- User says they learned or understand something → do **not** write `covered`;
  hand off to a one-topic `study-probe` for that topic
- User only invokes `/study-log` with no topic:
  - If the profile is empty → onboarding: ask overall level and current focus,
    run `init`, then ask for the first topic(s) to queue as `want`
  - Otherwise ask whether to queue a study topic (not to mark covered)

## Transferability

Before any global `want`, apply the `project-learning-boundary` test:

- Transferable → queue the topic via the recording policy
- Repo-local symbol / path / env var → generalize to the broader concept and
  queue that concept (confirm with the user), or offer to keep it in
  `.cursor/learning/project.md` — never write the raw symbol to the global
  profile

## Profile creation only

`init` stays in this Skill (outside the recording contract):

```bash
python3 ~/.cursor/learning/cli.py init --level "..." --focus "..."
```

## CLI missing

If `~/.cursor/learning/cli.py` is missing when a `want` is needed, emit a
`LEARNING-WANT` marker per the recording policy (want-only fallback). Do not
claim success if the hook also fails. Tell the user a new chat lets
`sessionStart` install the CLI.

## Reply

Confirm in one line what changed (`queue` / `init`) or that a one-topic probe
was started instead of writing `covered`.
