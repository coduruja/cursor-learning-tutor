# Hooks + runtime refactor plan

Status: Phases 1–6 **done** on `cursor/hooks-agents-refactor` (released as **2.6.0**).

This plan replaces the old hooks diagnosis/contracts docs. It assumes Rules and
Skills ownership in `LEARNING_TUTOR_RULES_SKILLS_OWNERSHIP.md` stays stable.
Public CLI argv lives in `RUNTIME_CLI_CONTRACT.md`.

## Why refactor again

Phases A–F made adapters safer and split `lib_profile` into modules, but the
**mental model is still wrong for readers**: almost all persistence code still
lives under `hooks/`.

Across ecosystems the same lesson shows up:

| Source | Practice |
|---|---|
| Cursor docs / plugin packaging | Narrow events; `$CURSOR_PLUGIN_ROOT`; fail-open for non-gates; `sessionStart` is fire-and-forget |
| Claude Code production playbooks (e.g. Totalum 2026) | Keep hot-path hooks fast; fail open on non-security work; push heavy work off the critical path; match narrowly |
| Claude Lab / quality-gate notes | Formatters and side effects must exit 0; do not put judgmental product logic in hooks |
| OpenAI Agents SDK lifecycle hooks | Hooks observe/instrument the run; they are not the application service |
| LangChain agent middleware / harness write-ups | Cross-cutting concerns (redact, retry, inject) sit in middleware; domain state stays outside |
| Harness engineering (e.g. SemaClaw / agent-harness essays) | Separate plugin surfaces: tools, skills, agents, **hooks** — each with one concern |
| Real Cursor adapters (e.g. Atrium inject script) | Thin shell: call a service, emit `additional_context` or `{}`, always fail-open, tight timeout |

**Translation for Learning Tutor:** Cursor should only see two thin adapters.
Profile markdown, topic normalization, project sheets, and CLI packaging are a
**runtime service** that hooks call — not “hook features.”

## Target shape

```text
runtime/                         # domain service (name may vary)
  learning/
    paths.py
    topics.py
    sections.py
    context.py
    profile.py
    project.py
    install.py
  cli.py                         # or keep learning_cli.py name during migrate
  __init__ / py.typed as needed

hooks/
  hooks.json                     # only $CURSOR_PLUGIN_ROOT → thin scripts
  inject_profile.py              # sessionStart adapter only
  capture_learning.py            # afterAgentResponse adapter only
  hook_io.py                     # optional shared stdin/stdout/diag helpers

# Compat during transition
hooks/lib_profile.py             # temporary re-export OR deleted after install migrates
```

Stable public path for the Agent remains:

```bash
python3 ~/.cursor/learning/cli.py …
```

`sessionStart` (or an explicit install path) still copies/publishes the runtime
into `~/.cursor/learning/` so Rules/Skills do not need the plugin root.

## Non-goals

- Do not reopen the evidence policy (`covered` only via one-topic probe).
- Do not merge Rules back into a monolith.
- Do not make hooks fail-closed (this is not a security gate).
- Do not depend on `sessionStart` `additional_context` as the only calibration
  path (platform inject is best-effort / sometimes dropped).

## Design principles

1. **Hook = bell.** Parse event JSON, call runtime, emit allowed stdout fields,
   log failures to stderr, exit 0.
2. **Runtime = kitchen.** All profile/project/topic/install logic lives here.
3. **Policy stays in Rules/Skills.** Hooks never decide “should this be covered?”
4. **Install is the reliable sessionStart job.** Inject is optional enrichment.
5. **Fast and fail-open.** Prefer timeouts; never block the Agent loop.
6. **One public CLI contract.** Keep argv stable unless versioning a migration.
7. **Tests first.** Extend `scripts/test_hooks_agents.py` / `verify_release.py`
   before moving files.

## Phased plan

### Phase 1 — Freeze the story (docs + checks) — **done**

- Ownership map distinguishes Hook vs Runtime.
- Smoke: `hooks.json` references only adapter scripts; adapter line budgets.
- Public CLI surface documented in `RUNTIME_CLI_CONTRACT.md`.

Exit: contributors agree “hooks/ ≠ product backend.”

### Phase 2 — Move package without behavior change — **done**

- Moved `hooks/learning/` → `runtime/learning/` and CLI → `runtime/cli.py`.
- Adapters still load `hooks/lib_profile.py` shim (resolves `runtime/`).
- `install_cli` copies from `runtime/` (+ hooks shim) into `~/.cursor/learning/`.

Exit: same CLI behavior; folder names match the mental model.

### Phase 3 — Thin the adapters — **done**

- `inject_profile.py`: install + `render_session_context(...)` only.
- `capture_learning.py`: `iter_want_markers` + `add_want(...)` only.
- Explicit timeouts in `hooks.json` (sessionStart 10s, afterAgentResponse 5s).
- Tightened adapter line budgets; marker/context logic in `runtime/learning/`.

Exit: adapters readable in one screen; no domain branching inside them.

### Phase 4 — Harden calibration without overweighting inject — **done**

- Kept install on sessionStart; inject remains best-effort enrichment.
- Rules/Skills remind: missing `LEARNING-PROFILE` → `cli.py show` before
  inventing level (`tutor-core`, `study-deep`, `study-probe`, `study-plan`).
- `beforeSubmitPrompt` recall left as a later optional experiment.

Exit: tutor works even when inject is silent.

### Phase 5 — Optional product simplification — **done (no cuts)**

Explicit product decision: **keep** markdown profiles, topic aliases / anti-noise,
project sheet, and marker fallback. This refactor is folder clarity + thin
adapters only — not a feature reduction.

Exit: documented decision; no mixed “simplify while moving” work.

### Phase 6 — Release — **done**

- Bumped to **2.6.0** + CHANGELOG.
- `python3 scripts/verify_release.py` passes.
- Live checklist remains manual in Cursor after plugin install.

## Decision log

1. ~~Final directory name: `runtime/` vs `python/learning_tutor/`.~~
   **Chose `runtime/`** (Phase 2).
2. Whether home install stays a flat copy or becomes an importable package only.
3. Whether to add version stamps on install to detect drift.
4. Whether per-turn inject (`beforeSubmitPrompt`) is worth the complexity.
5. ~~Optional product cuts (JSON profile, drop aliases, drop project sheet,
   CLI-only writes).~~ **No cuts for this release** (Phase 5) — keep current
   product surface; only Hook/Runtime packaging changed.

## Success criteria

- `hooks/` contains adapters + `hooks.json` (+ tiny shared I/O), not domain modules.
- Runtime owns profile/project/topics/install.
- Public CLI path unchanged for Agents.
- Fail-open preserved; no Rules/Skills evidence regression.
- Docs use Hook vs Runtime language consistently.
