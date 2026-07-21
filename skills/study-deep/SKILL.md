---
name: study-deep
description: Builds a deep, curated learning track with current, ranked resources calibrated to the user level. Use when the user asks for a serious study path, curated materials, a course-like plan, deep research on a topic, or invokes /study-deep.
---

# Study Deep

Delegate research to the `study-researcher` subagent. Keep research out of the
main conversation context.

## Resolve topic and level

1. Use the topic supplied by the user.
2. If omitted, run:

   ```bash
   python3 ~/.cursor/learning/cli.py queue-next
   ```

3. Use the first open queue topic. If the queue is empty, ask for one topic.
4. Read the level from `LEARNING-PROFILE`; infer from conversation only when
   absent.
5. Pass relevant `LEARNING-PROJECT` stack/candidates as context, never as a
   replacement for the selected topic.

## Delegate

Ask `study-researcher` for:

- Topic and current level
- Starting point
- Ordered track of at most five ranked resources
- Why each resource fits
- Estimated effort
- Concrete advancement signals

Return only the subagent's final track. Do not duplicate its research.

## Finish

If the topic is not already queued, ask in one line whether to add it. Use the
stable CLI `want` operation when the user agrees.
