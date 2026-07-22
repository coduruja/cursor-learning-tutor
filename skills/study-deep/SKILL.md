---
name: study-deep
description: >-
  Build a curated study track for one topic — ranked, current resources
  calibrated to the user's level. Use when the user wants a serious learning
  path, course-like plan, real study materials, or deep research on a topic, or
  invokes /study-deep. Not for a quick one-line answer to a concept question,
  not for quizzes, and not for viewing existing learning state.
---

# Study Deep

Delegate the research to the `study-researcher` subagent so the raw research
never enters the main conversation context.

## Resolve topic and level

1. Use the topic the user supplied. If they gave none:

   ```bash
   python3 ~/.cursor/learning/cli.py queue-next
   ```

   Use the first open queue topic; if the queue is empty, ask for one topic.
2. Take the level from `LEARNING-PROFILE` in context. If it is missing or empty,
   run `python3 ~/.cursor/learning/cli.py show` before inventing one; infer from
   the conversation only when that is empty too.
3. Pass relevant `LEARNING-PROJECT` stack/candidates as context only — they
   never replace the selected topic.

## Delegate

Call the `study-researcher` subagent with this contract:

**Pass in** — the topic (required), the current level, and optionally the
project stack/candidates as context.

**Expect back** (do not rewrite or re-research):

- Starting point
- An ordered track of at most five ranked resources (name, type, link, why,
  effort)
- Concrete advancement signals

The subagent is research/curation only: it must not probe, score, or write
`want` / `covered`. Return its final track to the user as-is.

## Finish

Finishing a curated track is **not** evidence of understanding and must **not**
write `covered`.

1. If the topic is not already queued, ask in one line whether to add it. On
   agreement:

   ```bash
   python3 ~/.cursor/learning/cli.py want --topic "TOPIC" --note "deep track started"
   ```

   If `~/.cursor/learning/cli.py` does not exist, emit this marker instead and
   say it was queued via fallback:

   ```text
   <!-- LEARNING-WANT topic="TOPIC" note="deep track started" -->
   ```

2. Always continue into a one-topic `study-probe` for the same topic (ask which
   topic only if it is ambiguous). Assessment is the next step, not an optional
   suggestion.
