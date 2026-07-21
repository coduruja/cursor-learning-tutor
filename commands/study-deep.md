Delegate to the `study-researcher` subagent to create a deep, curated study track.

- Topic: use what I write after the command. If I do not specify:
  1. run `python3 ~/.cursor/learning/cli.py queue-next`
  2. if there is an open queue item, use that topic (say which in one line)
  3. otherwise, ask in one line which topic
- Level: take from `LEARNING-PROFILE`. If missing, infer from the conversation or ask.
- If there is a `LEARNING-PROJECT`, mention relevant stack/candidates in the
  subagent prompt (context only; they do not replace the topic).

Pass topic + level to the subagent and return only the final track (starting
point, ordered track, advancement signals). Do not redo the research in chat.

At the end, ask in one line whether I want the topic on the **queue** with
`/study-log` (or run `want` if I say yes).
