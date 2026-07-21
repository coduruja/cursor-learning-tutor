Active probe: find what I know vs what this project needs, and adjust the profile.

Do not search the web. Prefer the stable CLI.

## Steps
1. Read the global profile and project context:
   ```bash
   python3 ~/.cursor/learning/cli.py show
   python3 ~/.cursor/learning/cli.py project-show
   ```
   If there is no `LEARNING-PROJECT` / project file and the repo has a clear
   stack, sync 3–8 specific candidates (no base languages):
   ```bash
   python3 ~/.cursor/learning/cli.py project-sync --stack "A;B" --candidates "t1;t2;t3"
   ```

2. Build a short hypothesis (do not dump a huge list):
   - what I **probably know** (level/focus + covered)
   - what I **should know** for this project (candidates + stack)
   Prioritize 5–8 topics total.

3. Ask **3–5 short questions in a single block** (not one per message).
   Practical questions, not trivia. Accept “I don’t know”.

4. From my answers, adjust:
   - answered confidently →
     `python3 ~/.cursor/learning/cli.py covered --topic "..." --level "..." --note "study-probe"`
     and, if it was a project candidate:
     `python3 ~/.cursor/learning/cli.py project-drop --topic "..."`
   - wrong / “I don’t know” →
     `python3 ~/.cursor/learning/cli.py want --topic "..." --note "gap from study-probe"`
   - partial →
     `python3 ~/.cursor/learning/cli.py want --topic "..." --note "reinforce (study-probe)"`

5. Update the project probe:
   ```bash
   python3 ~/.cursor/learning/cli.py project-sync --probe-summary "..."
   ```

## Final reply
In 2–3 lines: what went to **covered**, what entered the **queue**, and the
suggested next step (`/study-deep` on the first queue item, if any).
