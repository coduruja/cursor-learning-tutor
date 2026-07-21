Record something in my learning profile (`~/.cursor/learning/profile.md`).

## What to record
- If I pass a topic (or describe what we learned): **covered**.
- If I say "I want to study X" / "add X to the queue": **queue**.
- If the profile is empty and I only run the command: do onboarding in 2
  questions (overall level + focus), run `init`, then ask for the first topic.

## Note on automatic capture
`concept_gap` questions (“what is X?”, “how does X work?”) **already go to the
queue automatically** via the tutor rule. Use `/study-log` for manual overrides,
corrections, or when automatic capture did not run.

## How to write (required)
Use the stable CLI (do not edit the markdown by hand unless the CLI is missing):

```bash
python3 ~/.cursor/learning/cli.py covered --topic "..." --level "beginner|intermediate|advanced" --note "..."
# or
python3 ~/.cursor/learning/cli.py want --topic "..." --note "..."
# or
python3 ~/.cursor/learning/cli.py init --level "..." --focus "..."
```

If the CLI does not exist, tell me to open a **new chat** so `sessionStart`
can install `~/.cursor/learning/cli.py`, or copy the helper from the plugin.

## Reply
Keep it short: confirm with `Saved to profile: …` and say whether it was
**covered** or **queue**.
Do not search the web.
