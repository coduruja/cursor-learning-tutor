# Learning Tutor Architecture

## Goal

Make Learning Tutor reliable without injecting the full tutoring, recording,
project-discovery, and workflow policy into every Agent request.

This document describes the intended runtime architecture of Learning Tutor:
how Rules and Skills divide responsibility, when each loads, how they persist
learning, and how they avoid duplicated or conflicting policy. It is written as
a set of recommendations to refactor the plugin, followed by a concrete,
ordered implementation plan.

## Sources reviewed

Primary sources:

- [Cursor Rules documentation](https://cursor.com/docs/context/rules)
- [Cursor Plugins reference](https://cursor.com/docs/reference/plugins)

Practitioner guidance and public examples:

- [Morph — Cursor Rules Best Practices](https://www.morphllm.com/cursor-rules-best-practices)
- [TECHSY — Cursor Rules Guide](https://techsy.io/en/blog/cursor-rules-guide)
- [Packmind — Context Engineering Best Practices](https://packmind.com/context-engineering-ai-coding/context-engineering-best-practices/)
- [LaunchDarkly Labs — public Cursor rules](https://github.com/launchdarkly-labs/cursor-rules)

Cursor documentation is the source of truth for behavior. Third-party sources
are useful for operational patterns, not product guarantees.

## What Cursor rules do

Applied rules are inserted near the start of the Agent context. Their
frontmatter controls when they load:

| Mode | Frontmatter | Appropriate use |
|---|---|---|
| Always Apply | `alwaysApply: true` | Small, universal invariants |
| Apply Intelligently | `alwaysApply: false`, descriptive `description`, no `globs` | Intent-based policies |
| File-scoped | `alwaysApply: false`, `globs` | Guidance tied to specific files |
| Manual | `alwaysApply: false`, no description/globs | Rare guidance invoked with `@rule` |

With `alwaysApply: true`, Cursor ignores `description` and `globs`. Every line is
paid for in every chat, whether relevant or not.

Rules should provide persistent policy. Skills should own multi-step workflows,
scripts, optional references, and substantial procedures.

## What Cursor skills do

Agent Skills are packages under `skills/<name>/SKILL.md`. Cursor discovers them
from the plugin `skills/` path. Unlike always-on rules, a Skill loads when:

- the user invokes it explicitly (for example `/study-log`), or
- the model matches the Skill `description` to the user intent (unless
  `disable-model-invocation: true`).

Skills may carry progressive disclosure via `references/` (loaded only when the
Skill needs them). That makes Skills the right home for long procedures and
rubrics that should not sit in every Agent turn.

### Rule vs Skill vs Reference

| Keep in a **Rule** | Keep in a **Skill** |
|---|---|
| Short policy (“when X, do / do not Y”) | Multi-step workflow (load → decide → act → report) |
| Must apply outside any `/study-*` invocation | Only meaningful when that Skill is active |
| Shared contract used by several flows | Operational detail of one flow |
| Always-on or intent-scoped invariants | Scripts, checklists, optional references |

A useful shorthand:

- **Rule** ≈ “write always like this” / “never do that”
- **Skill** ≈ “run this study task end-to-end”
- **Reference** ≈ “read this detailed doc only when the Skill needs it”

By this test, persistence is a Rule (`learning-recording`) because it is a
shared sub-step of several flows, not a user-invoked task. The probe scoring
rubric is a Skill reference because it is only needed during `study-probe`.

## Why the monolithic rule was replaced

The original runtime rule `rules/tutor.mdc` was ~98 lines and always applied. It
combined at least six concerns: tutor identity and calibration, intent
classification, concept-gap capture and anti-noise, project stack discovery,
the CLI and marker reference, and the Skill catalog. That created four problems:

1. **Unnecessary context cost.** CLI syntax, marker formats, project sync, and
   skill descriptions were loaded even for ordinary coding requests with no
   learning event.
2. **Rule/Skill overlap.** Skills already own their workflows; repeating those
   procedures in an always-on rule created multiple sources of truth.
3. **Hidden policy conflicts.** The rule allowed recording a concept as covered
   after merely teaching it, while the probe rubric required evidence — a
   contradiction buried in one large prompt.
4. **Coupled project-local and global learning.** Stack discovery is a workflow,
   not a universal invariant; keeping it always-on encouraged repo details to
   leak into the global profile.

The rule set is therefore split into one always-on core plus intelligent,
intent-scoped rules, with Skills owning the workflows.

## Runtime rule set

Keep distributed rules under `rules/`, because the plugin manifest packages that
directory into every project where Learning Tutor is installed.

### `tutor-core.mdc` — Always Apply

Small (roughly 15–25 lines). Responsibilities:

- Establish the tutor role.
- Use `LEARNING-PROFILE` to calibrate explanation depth.
- Never invent learning history.
- Distinguish ordinary repository work from a learning event.
- Route explicit study requests to the relevant Skill.
- State the invariant that global learning must be transferable.

It must **not** include the CLI catalog, marker syntax, project stack scanning,
probe scoring, or the deep-study workflow. Calibration and the normal-work vs
learning-event distinction must be available before the agent can decide whether
any other policy is relevant, which is why this rule is always-on.

Routing responsibilities specific to core:

- An empty profile is directed to `study-log` (which owns first writes), not to
  `study-plan`.
- Self-attestation or study-completion phrasing (“I think I understand …”, “I
  already read the docs”, “I finished studying …”) routes to `study-probe`.
- A request for a curated study track routes to `study-deep`.

### `concept-gap-capture.mdc` — Apply Intelligently

Suggested description:

> Capture a transferable study topic when the user asks a conceptual question
> such as what something is, how it works, or how two concepts differ.

Responsibilities:

- Detect a genuine conceptual question.
- Exclude questions about repository symbols and implementation details.
- Select at most one main transferable topic.
- Apply anti-noise and deduplication rules.
- Persist a `want` through the recording policy.
- Provide visible feedback.

This policy is intent-based, not file-based, so it should not load for
implementation-only requests.

### `learning-recording.mdc` — Apply Intelligently

Suggested description:

> Persist Learning Tutor queue or covered updates when a learning event,
> explicit study-log request, or successful assessment requires a profile write.

This rule is the single canonical persistence contract. It is the only place
that spells out how to write to the profile:

- The stable CLI as the preferred write path, with the minimum `want` and
  `covered` command forms.
- The marker fallback for when the CLI is unavailable.
- The required concise feedback line after a successful write.

Two invariants keep it consistent with the evidence model:

- A new `covered` entry is accepted **only** when it carries one-topic probe
  evidence (see the evidence policy below). It is never inferred from
  self-report or from having explained a concept in chat.
- The marker fallback can create **only** `want`. There is no `covered` marker;
  the historical `LEARNING-LOG` marker is retired.

Recording is a Rule rather than a Skill because it is a shared sub-step of
capture, log, and probe — the policy must arrive whenever a write is needed,
without relying on anyone remembering to open a reference file. Because the rule
is Apply Intelligently it might not load during a Skill run; the accepted
mitigation is to keep its description targeted at write situations and to have
Skills say “persist through the recording policy” (a strong retrieval signal),
rather than duplicating CLI blocks into Skills.

### `project-learning-boundary.mdc` — Apply Intelligently

Suggested description:

> Separate transferable learning from repository-specific context when project
> code, stack, symbols, or local candidates influence a study decision.

This rule is the single owner of the transferability test. Every write path —
capture, plan, probe, and log — defers to it. Responsibilities:

- Apply the test: “Would this still be useful without opening this repository?”
- Keep symbols, paths, environment variables, and class names project-local.
- Generalize a local example into the broader concept when that concept is the
  real learning target, and queue the generalized topic rather than the symbol.
- Allow `.cursor/learning/project.md` to hold local context; candidates there
  are not the global queue.
- Never auto-promote project candidates into the global queue; promote only on a
  real gap (a conceptual question, a probe, or an explicit request).

Relevance is intent-scoped: it applies when a study decision involves project
context, not on every Agent turn.

## Persistence and evidence policy

The core behavioral rule of the plugin is that **evidence, not exposure,
attests knowledge**.

- Saying “I understand X”, “I learned X”, reading an explanation, completing a
  study track, or finishing an operational task must **not** create a `covered`
  entry.
- `study-probe` is the only workflow that can attest new knowledge as
  `covered`.

The probe is always scoped to **one topic** — never a multi-topic exam across
the queue or stack:

- It selects exactly one transferable topic (user-supplied, `queue-next`, or an
  explicit choice).
- It asks **5 to 10** short practical questions about that single topic. There
  is no lighter mode with fewer questions; a probe with fewer than five
  questions is incomplete and cannot write `covered`.
- It waits for answers, then scores with the assessment rubric.
- If at least **50%** of that topic’s answers are correct, it records `covered`
  for that topic with a short evidence note. Otherwise the topic stays or enters
  the queue as `want`; `covered` is not written.
- To attest several topics, run separate one-topic probes. Scores from unrelated
  topics are never aggregated into a single pass.

## Skills catalog and ownership

Learning Tutor ships four Skills under `skills/`:

| Skill | Invocation | Owns |
|---|---|---|
| `study-log` | Explicit only (`disable-model-invocation: true`) | Manual queue writes, profile creation (`init`), corrections |
| `study-plan` | Explicit or auto from progress intent | Read-only snapshot + missing-sheet `project-sync`; no profile writes |
| `study-probe` | Explicit or auto from assessment intent | One-topic evidence-based assessment and resulting profile writes |
| `study-deep` | Explicit or auto from deep-study intent | Curated track via the `study-researcher` subagent |

### `study-log`

`study-log` is the explicit, manual write path — never auto-invoked, because it
writes to the profile. It owns:

- Creating the profile from scratch (`init`) and the empty-profile onboarding
  (overall level, focus, first topics). Onboarding lives here, not in
  `study-plan`.
- Adding `want` items on explicit request.

It defers the *how* of writing to `learning-recording` (no CLI copy for
`want`/`covered`; `init` is the one command that stays in the Skill). It obeys
`project-learning-boundary` before any global write: a transferable topic is
queued normally; a repo-local symbol/path/env var is generalized to the broader
concept (which is what gets queued) or kept in `.cursor/learning/project.md`,
never written raw to the global profile. It does not attest `covered`: a request
to mark something as learned routes to a one-topic probe. If the CLI is missing,
it emits a `LEARNING-WANT` marker rather than only telling the user to open a
new chat.

### `study-plan`

`study-plan` is strictly read-only. It answers “what do I already know?”, “what
is queued?”, and “what should I study next?” from existing state, and it never
runs `init`, `want`, or `covered`.

- With an existing profile it returns a concise snapshot (solid / in progress /
  queue / project context / gaps / prioritized next steps) and hands off to
  `study-probe` or `study-deep`.
- With an empty profile it reports that in one short message and directs the
  user to `/study-log`; it does not onboard.
- Listing a gap is not a write: it recommends `/study-log` (or lets
  `concept-gap-capture` queue it later), but never calls `want` itself.
- It may run `show` / `project-show` and, only when the project sheet is missing
  or empty, a one-time `project-sync` for stack and candidates — a local-sheet
  read/discovery action, not a global learning write.
- It keeps at most a one-line reminder of the transferability boundary; the full
  test lives in the boundary rule.

### `study-probe`

`study-probe` is the only path to `covered`, implementing the evidence policy
above (one topic, 5–10 questions, wait, ≥50% → `covered`, else `want`). It reads
`assessment-rubric.md` before writing questions or scoring. It defers `want` /
`covered` to the recording policy and keeps only the probe-specific commands
`project-drop` and `project-sync --probe-summary`. It applies the boundary rule
so questions and scoring stay on transferable concepts rather than repo trivia.
Its report distinguishes global learning from project-local context.

### `study-deep`

`study-deep` delegates curated research to the `study-researcher` subagent and
returns the track, keeping heavy research out of the main chat. It resolves the
topic (user-supplied, else `queue-next`, else ask) and reads the level from the
profile. Finishing a track is explicitly **not** evidence and must not write
`covered`; after presenting the track it always continues into a one-topic
`study-probe` for that topic rather than merely offering one. Any optional `want`
defers to the recording policy.

### Cross-skill integration map

```text
concept_gap (rule) ──want──► queue
                │
                ▼
         study-plan ──offers──► study-probe ──covered/want──► profile
                │                      ▲
                └──offers──► study-deep ──always──► study-probe (same topic)
                                   │
                                   └── optional want if not queued

study-log ── explicit want / init ──► profile
          └── request to attest learning ──► study-probe ──► covered/want

self-attestation phrases ("I think I understand", "finished studying", …)
          └──► study-probe (one topic)
```

Shared dependencies every Skill assumes:

- Stable CLI at `~/.cursor/learning/cli.py` (installed by `sessionStart`).
- Optional injected `LEARNING-PROFILE` / `LEARNING-PROJECT`.
- Global profile for queue/covered; project sheet for local context only.

## Single-owner map

Each concern has exactly one canonical owner; everything else points at it with
at most a short reminder.

| Concern | Canonical owner | Others |
|---|---|---|
| How to persist `want` / `covered` (CLI, markers, feedback) | `learning-recording.mdc` | Skills point at it; keep only flow-specific commands (`init`, `project-drop`, `project-sync --probe-summary`) |
| Transferability (local vs global) | `project-learning-boundary.mdc` | Rubric and Skills apply it; rubric keeps only probe examples/scoring |
| Auto-`want` on conceptual questions | `concept-gap-capture.mdc` | — |
| Probe scoring / evidence rubric | `study-probe` + `references/assessment-rubric.md` | — |
| Snapshot / missing-sheet `project-sync` (read) | `study-plan` | — |
| Manual queue write + first `init` | `study-log` | — |
| Research delegation to subagent | `study-deep` | — |
| Routing to `/study-*` | `tutor-core` (short pointers) | each Skill `description` |

## What should not live in rules

| Content | Owner | Reason |
|---|---|---|
| Project stack scan / `project-sync` workflow | `study-plan` (and `study-probe` for `--probe-summary`) | Multi-step, on-demand workflow |
| Probe scoring | `study-probe/references/assessment-rubric.md` | Detailed reference loaded only when needed |
| Deep research delegation | `study-deep` Skill | Specialized orchestration |
| Onboarding questions / first `init` | `study-log` Skill | Write path; `study-plan` stays read-only |
| Full CLI catalog | README / CLI help | Not required in prompt context |
| Marker implementation details | `learning-recording.mdc` only | Single canonical persistence contract |

## Runtime rules vs maintainer rules

Two different audiences must not be mixed:

1. `rules/` — shipped by the plugin and applied to users of Learning Tutor.
2. `.cursor/rules/` — guidance for contributors editing this repository.

Optional maintainer-only rules, added only if the same mistakes recur while
developing the plugin:

- `.cursor/rules/plugin-components.mdc` (glob `rules/**/*.mdc, skills/**/SKILL.md,
  agents/**/*.md`) — enforce English copy and component boundaries.
- `.cursor/rules/hooks-python.mdc` (glob `hooks/**/*.py`) — enforce
  backward-compatible profile migrations and CLI validation.

## Why not globs for tutoring policies

Concept gaps and learning decisions are triggered by conversation semantics and
can occur while any file type is open. A `**/*.py` or `**/*.ts` glob would scope
the policy to the implementation language rather than to the user's intent. Use
descriptive intelligent rules for tutoring policies; reserve globs for
maintainer rules tied to files in this repository.

## Target structure

```text
rules/
├── tutor-core.mdc
├── concept-gap-capture.mdc
├── learning-recording.mdc
└── project-learning-boundary.mdc

skills/
├── study-log/SKILL.md
├── study-plan/SKILL.md
├── study-probe/
│   ├── SKILL.md
│   └── references/assessment-rubric.md
└── study-deep/SKILL.md

agents/
└── study-researcher.md

.cursor/rules/                    # optional, maintainer-only
├── plugin-components.mdc
└── hooks-python.mdc
```

## Implementation plan

The rule split (always-on `tutor-core` plus the three intelligent rules, with
`tutor.mdc` removed and `project-sync` discovery moved into `study-plan`) is
already in place. The remaining work aligns rule and Skill bodies with the
recommendations above, in an order that prevents mid-refactor conflicts. Later
phases assume earlier contracts are already true.

### Phase A — freeze the write contracts (rules first)

Every Skill change points at these rules, so they must be correct before the
Skills change.

| Step | Change |
|---|---|
| A1 | `learning-recording.mdc`: `covered` only from one-topic probe evidence; retire the `LEARNING-LOG` marker; keep the `LEARNING-WANT` marker fallback and CLI-missing behavior; keep the feedback line |
| A2 | `project-learning-boundary.mdc`: confirm it is the sole transferability policy; no Skill may restate the full gate |
| A3 | `tutor-core.mdc`: empty profile → `/study-log`; self-attestation / “finished studying” → `study-probe`; deep-study requests → `study-deep` |

Exit criteria: only one always-on rule; recording and boundary text match the
policy above; no Skill edited yet beyond core routing.

### Phase B — make `study-probe` the only path to `covered`

The evidence policy is the center of gravity; log, deep, and plan all hand off to
the probe, so the probe must be correct first.

| Step | Change |
|---|---|
| B1 | Rewrite the `study-probe` description: assessment intent plus self-attestation and post-deep handoff triggers |
| B2 | Rewrite `study-probe/SKILL.md`: exactly one topic; 5–10 questions; wait; ≥50% → `covered`, else `want`; no multi-topic exam |
| B3 | Rewrite `assessment-rubric.md`: point at `project-learning-boundary` for the transferability test; keep question design, examples, scoring, the 5–10 range, and the ≥50% bar |
| B4 | Replace duplicated `want`/`covered` CLI in the probe with a pointer to the recording policy; keep `project-drop` and `project-sync --probe-summary` |

Exit criteria: `/study-probe` and “I think I understand X” run a one-topic 5–10
question probe; self-report never writes `covered`.

### Phase C — align the other Skills

Each Skill either routes to the probe, writes only `want`/`init`, or stays
read-only. Doing this before Phase B would leave broken handoffs.

| Step | Change |
|---|---|
| C1 | `study-log`: route “I learned X” → one-topic probe; keep `init` + manual `want`; apply the boundary before global writes; emit a `LEARNING-WANT` marker when the CLI is missing; point at the recording policy (no `covered`/`want` CLI copy) |
| C2 | `study-plan`: remove onboarding `init`/`want`; empty profile → point to `/study-log`; never auto-`want` gaps; tighten the description to read-only intent; keep at most a one-line boundary reminder; keep `show` / `project-show` / missing-sheet sync |
| C3 | `study-deep`: after the track, always hand off to a one-topic `study-probe`; state that finishing a track is not evidence; optional `want` via the recording policy |

Exit criteria: empty `/study-plan` writes nothing; `/study-log` cannot force-log
raw repo symbols; `/study-deep` always ends in a probe.

### Phase D — dedupe verification and hooks

| Step | Change |
|---|---|
| D1 | Assert no `cli.py want` / `cli.py covered` outside `learning-recording.mdc` |
| D2 | Assert no full transferability gate outside `project-learning-boundary.mdc` (Skills/rubric may point + keep examples) |
| D3 | Update `afterAgentResponse` / capture hooks if they still treat `LEARNING-LOG` as covered; markers create `want` only |
| D4 | Automated checks: valid `.mdc` frontmatter; at most one `alwaysApply: true` runtime rule; the two assertions above |

Exit criteria: checks pass; hooks agree with the want-only marker policy.

### Phase E — install, verify, release

| Step | Change |
|---|---|
| E1 | Install the plugin locally; inspect active rules/context on ordinary coding vs learning turns |
| E2 | Run the full scenario matrix below |
| E3 | Bump the plugin version and update the CHANGELOG (evidence policy + Skill/rule ownership) |
| E4 | Add maintainer `.cursor/rules/` only if the same editing mistakes recur |

Do not reorder A → B → C. In particular, do not route `study-log` to the probe
before the probe is one-topic / 5–10 / ≥50%; do not strip CLI copies from Skills
before `learning-recording` carries the marker and evidence text; and do not
teach the rubric a new transferability gate while the boundary rule is the
intended sole owner.

## Scenario matrix

### Rules-focused

| Prompt | Expected rules | Expected result |
|---|---|---|
| “Fix this failing test” | core only | No learning write |
| “What is HTTP keep-alive?” | core + concept capture + recording | One transferable `want` |
| “What does `MediaUploadEngineMixin` do?” | core + project boundary | Repo answer, no global write |
| “Test whether I understand Cursor rules” | core; `study-probe` | Evidence-based assessment |
| “Build a deep Docker study track” | core; `study-deep` | Research delegated to subagent |
| “Add this topic to my queue” | core + recording | Explicit `want` |

### Skills-focused

| Prompt | Expected Skill | Expected result |
|---|---|---|
| `/study-log` + “I learned Docker” | `study-log` → one-topic `study-probe` | No immediate write; ≥50% on Docker → `covered` |
| “What is saved for study?” | `study-plan` | Snapshot; no quiz |
| “What should I study next?” | `study-plan` | Read-only next steps |
| “Test me on Docker” | `study-probe` + rubric | One-topic assessment |
| “What do I know about Docker?” | Clarify | Ask snapshot vs assessment |
| `/study-plan` in repo without project sheet | `study-plan` | Optional one-time `project-sync` |
| `/study-probe` | `study-probe` + rubric | One topic → 5–10 questions → wait → ≥50% → write |
| `/study-deep` with empty topic | `study-deep` → one-topic `study-probe` | Track then mandatory assessment |
| “I think I understand Docker” | `study-probe` | One-topic probe; no self-report `covered` |
| “I finished studying HTTP” | `study-probe` | One-topic probe |
| Empty profile + `/study-plan` | `study-plan` | Report empty; point to `/study-log`; no writes |
| Empty profile + `/study-log` | `study-log` | `init` + first `want` |

## Success criteria

- Only one small runtime rule is always applied.
- Ordinary coding requests do not load persistence or project-learning policy.
- Conceptual questions produce exactly one transferable queue item.
- Repository-specific questions never pollute the global profile.
- Skills remain the sole owners of multi-step study workflows.
- Each overlapping concern has a single canonical owner, with at most a short
  pointer elsewhere.
- `study-plan` and `study-probe` auto-invoke descriptions do not routinely
  collide.
- One evidence policy for `covered` is reflected in `study-log`, `study-probe`,
  and `learning-recording` without contradiction.
- Every probe assesses exactly one topic with 5–10 questions; the ≥50% threshold
  is scored for that topic only; multi-topic aggregate probes are not used.
- The active-context panel confirms the expected rules for every scenario above.
