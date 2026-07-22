# Runtime CLI compatibility surface

Public Agent path (must stay stable unless a versioned migration says otherwise):

```bash
python3 ~/.cursor/learning/cli.py <command> …
```

Installed by `sessionStart` from the plugin runtime into `~/.cursor/learning/`.

## Commands

```text
init [--level ...] [--focus ...]
covered --topic ... [--level ...] [--note ...]
want --topic ... [--note ...]
done --topic ...
show
queue-next
project-show [--cwd ...]
project-sync [--stack ...] [--candidates ...] [--probe-summary ...] [--cwd ...]
project-drop --topic ... [--cwd ...]
```

## Stable reply prefixes (do not rename lightly)

- `Saved to profile (covered):`
- `Saved to profile (queue):`
- `Already in queue:`
- `Already covered recently:`
- `Ignored (generic topic / base language):`
- `Marked done in queue:`
- `Not found in queue:`

## Marker fallback (want only)

When the CLI is missing, Rules may emit:

```text
<!-- LEARNING-WANT topic="TOPIC" note="context" -->
```

Captured by `afterAgentResponse`. No covered marker.
