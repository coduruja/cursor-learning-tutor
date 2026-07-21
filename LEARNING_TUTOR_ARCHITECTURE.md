# Learning Tutor Architecture

## Goal

Make Learning Tutor reliable without injecting the full tutoring, recording,
project-discovery, and workflow policy into every Agent request.

This document covers the **runtime architecture of Learning Tutor**: how Rules
and Skills divide responsibility, when each loads, and how to avoid duplicated
or conflicting policy. It began as a rules-focused proposal and now also
records Skills ownership analysis, per-Skill inspection findings, and open
integration questions that still need decisions.

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

## What Cursor rules actually do

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

## What Cursor skills actually do

Agent Skills are packages under `skills/<name>/SKILL.md`. Cursor discovers them
from the plugin `skills/` path. Unlike always-on rules, a Skill loads when:

- the user invokes it explicitly (for example `/study-log`), or
- the model matches the Skill `description` to the user intent (unless
  `disable-model-invocation: true`)

Skills may carry progressive disclosure via `references/` (loaded only when the
Skill needs them). That makes Skills the right home for long procedures and
rubrics that should not sit in every Agent turn.

### Rule vs Skill — ownership test

| Keep in a **Rule** | Keep in a **Skill** |
|---|---|
| Short policy (“when X, do / do not Y”) | Multi-step workflow (load → decide → act → report) |
| Must apply outside any `/study-*` invocation | Only meaningful when that Skill is active |
| Shared contract used by several flows | Operational detail of one flow |
| Always-on or intent-scoped invariants | Scripts, checklists, optional references |

A useful shorthand from the refactor discussions:

- **Rule** ≈ “write always like this” / “never do that”
- **Skill** ≈ “run this study task end-to-end”
- **Reference** ≈ “read this detailed doc only when the Skill needs it”

`learning-recording` is a Rule (not a Skill) because persistence is a shared
policy, not a user-invoked study task. `assessment-rubric.md` stays a Skill
reference because scoring detail is only needed during `study-probe`.

## Current architecture audit

### Historical problem (monolithic always-on rule)

The distributed runtime rule `rules/tutor.mdc` was ~98 lines and always applied.
It combined at least six concerns:

1. Tutor identity and profile calibration
2. User-intent classification
3. Concept-gap capture and anti-noise policy
4. Project stack discovery and synchronization
5. CLI and fallback-marker reference
6. Skill catalog and routing

This created four problems.

#### 1. Unnecessary context cost

CLI syntax, marker formats, project synchronization, and skill descriptions are
loaded even for ordinary coding requests that contain no learning event.

#### 2. Rule/Skill responsibility overlap

`study-log`, `study-plan`, `study-probe`, and `study-deep` already contain their
own workflows. Repeating those procedures in an always-on rule increases drift
and creates multiple sources of truth.

#### 3. Policy conflicts become harder to see

The monolithic rule permitted recording a concept as covered after it was taught.
The probe rubric requires evidence of understanding. A monolithic rule lets
these policies evolve independently inside one large prompt instead of exposing
the contradiction as a deliberate boundary.

#### 4. Project-local and global learning are coupled

Project stack discovery is a workflow, not a universal tutoring invariant.
Keeping it always-on encourages repo details to leak into the global learning
profile.

### Implementation status (rules split)

Steps 1–2 of the migration are done:

| Rule | Mode | Status |
|---|---|---|
| `tutor-core.mdc` | Always Apply | Implemented |
| `concept-gap-capture.mdc` | Apply Intelligently | Implemented |
| `learning-recording.mdc` | Apply Intelligently | Implemented |
| `project-learning-boundary.mdc` | Apply Intelligently | Implemented |

`rules/tutor.mdc` has been removed. `project-sync` discovery now lives in the
`study-plan` Skill. Remaining work is mainly **deduplicating Skill/rule overlap**
and locking one evidence policy for `covered`.

## Recommended runtime rule set

Keep distributed rules under `rules/`, because the plugin manifest packages
that directory into every project where Learning Tutor is installed.

### 1. `tutor-core.mdc` — Always Apply

Target: roughly 15–25 lines.

Responsibilities:

- Establish the tutor role
- Use `LEARNING-PROFILE` to calibrate explanation depth
- Never invent learning history
- Distinguish ordinary repository work from a learning event
- Route explicit study requests to the relevant Skill
- State the invariant that global learning must be transferable

Do not include:

- CLI command catalog
- Marker syntax
- Project stack scanning
- Probe scoring
- Deep-study workflow

Why always-on: calibration and the distinction between normal work and learning
events must be available before the agent can decide whether another policy is
relevant.

### 2. `concept-gap-capture.mdc` — Apply Intelligently

Suggested description:

> Capture a transferable study topic when the user asks a conceptual question
> such as what something is, how it works, or how two concepts differ.

Responsibilities:

- Detect a genuine conceptual question
- Exclude questions about repository symbols and implementation details
- Select at most one main transferable topic
- Apply anti-noise and deduplication rules
- Ask the recording policy to persist a `want`
- Provide visible feedback

Why intelligent: this policy is based on user intent, not file paths. It should
not load for implementation-only requests.

### 3. `learning-recording.mdc` — Apply Intelligently

Suggested description:

> Persist Learning Tutor queue or covered updates when a learning event,
> explicit study-log request, or successful assessment requires a profile write.

Responsibilities:

- Define the stable CLI as the preferred write path
- Include only the minimum `want` and `covered` command forms
- Define marker fallback behavior
- Require concise feedback after a successful write
- Never infer `covered` without the evidence policy chosen by the project

Why separate: all capture and assessment flows need one canonical persistence
contract. Skills should call this contract instead of duplicating storage rules.

Why a Rule (not a Skill): recording is a sub-step of capture, log, and probe —
not a user-facing study task with its own invocation. The policy must arrive
when a write is needed, without relying on someone remembering to open a
reference file.

### 4. `project-learning-boundary.mdc` — Apply Intelligently

Suggested description:

> Separate transferable learning from repository-specific context when project
> code, stack, symbols, or local candidates influence a study decision.

Responsibilities:

- Apply the transferability test:
  “Would this still be useful without opening this repository?”
- Keep symbols, paths, environment variables, and class names project-local
- Generalize local examples into broader concepts when possible
- Allow `.cursor/learning/project.md` to hold local context
- Prevent automatic promotion from project candidates to the global queue

Why intelligent: this is relevant when a study decision involves project
context, not on every Agent turn.

## Skills catalog and ownership

Learning Tutor ships four Skills under `skills/`:

| Skill | Invocation | Owns |
|---|---|---|
| `study-log` | Explicit only (`disable-model-invocation: true`) | Manual corrections / deliberate profile writes |
| `study-plan` | Explicit or auto from progress intent | Snapshot, onboarding, missing-sheet `project-sync` |
| `study-probe` | Explicit or auto from assessment intent | Evidence-based quiz, scoring, profile updates from evidence |
| `study-deep` | Explicit or auto from deep-study intent | Curated track via `study-researcher` subagent |

### Overlap map (rule ↔ skill) and decisions

Step 3 of the migration is an **ownership pass**: find duplicated content,
choose one owner, and leave at most a short pointer in the other place.

| Content | Rule today | Skill today | Decision |
|---|---|---|---|
| CLI `want` / `covered` + write feedback | `learning-recording` | `study-log`, parts of `study-probe` / `study-deep` | **Rule** is the canonical persistence contract. Skills keep *when* to write for their flow; drop duplicated full CLI/marker blocks where safe, or point at the recording policy |
| Transferability / no global pollution | `project-learning-boundary` | `study-plan`, `study-probe` (+ assessment rubric) | **Rule** owns the invariant. Skills may keep a one-line reminder, not a second full policy |
| Auto-`want` on conceptual questions | `concept-gap-capture` | — | **Rule only** (not a Skill) |
| Probe scoring / evidence rubric | — | `study-probe` + `references/assessment-rubric.md` | **Skill + reference only** |
| Snapshot / onboarding / stack `project-sync` | — (removed from rules) | `study-plan` | **Skill only** |
| Research delegation to subagent | — | `study-deep` | **Skill only** |
| Routing to `/study-*` | `tutor-core` (short pointers) | each Skill `description` | **Rule** routes; **Skill** owns the workflow |

What “remove duplication” means in practice:

1. Choose the owner (rule or skill).
2. In the other place, delete the full procedure or leave a one-line pointer.
3. Ensure there are not two conflicting policies (especially for `covered`).

The noisiest remaining overlap is the **recording CLI** repeated across
`learning-recording` and Skills. Boundary wording in plan/probe is lighter and
can stay as a short reminder.

## Skills audit (inspection of `skills/` only)

This section inspects the four shipped Skills and the probe rubric as they
exist in the repository. It does **not** replace the rules analysis above.
Agents, hooks, and CLI internals were out of scope for this pass (except where
a Skill already names them).

### Inventory

| Path | Lines (approx.) | Auto-invoke | Progressive disclosure |
|---|---|---|---|
| `skills/study-log/SKILL.md` | ~35 | No (`disable-model-invocation: true`) | None |
| `skills/study-plan/SKILL.md` | ~63 | Yes (description match) | None |
| `skills/study-probe/SKILL.md` | ~59 | Yes | `references/assessment-rubric.md` |
| `skills/study-deep/SKILL.md` | ~43 | Yes | None (delegates to subagent) |

### `study-log` — findings

**Role as written:** explicit manual write path for corrections, overrides, and
deliberate profile updates.

**What works well**

- Explicit-only invocation matches a dangerous write surface (user must ask).
- Clear branch: learned → `covered`, study later → `want`, empty invoke → ask.
- Empty-profile path runs `init` then asks for a first topic.
- Refuses web search; points at `sessionStart` if CLI is missing.
- Short confirmation reply.

**Problems / risks**

- Restates the full `covered` / `want` / `init` CLI block. That duplicates the
  persistence contract that `learning-recording.mdc` is meant to own (for
  `want`/`covered`; `init` is intentionally skill-side today).
- **Evidence policy (decision made):** “User describes something they learned”
  is not enough to record `covered`. `/study-log` will no longer be an escape
  hatch for attesting knowledge: it must route the user to a one-topic
  `study-probe`, and that topic becomes `covered` only with at least 50%
  correct on its probe questions.
- No marker fallback if CLI is missing (recording rule has markers; this Skill
  only says open a new chat).
- No transferability check — the user can force-log a repo-local symbol into
  the global profile. That may be acceptable for an explicit override, but it
  is undocumented as such.
- Empty-profile onboarding overlaps `study-plan` (both can `init` + first
  topics). Ownership of onboarding is **not decided**.

### `study-plan` — findings

**Role as written:** passive snapshot of learning state; may sync a missing
project sheet; onboards when the profile is empty.

**What works well**

- Explicitly passive: do not test, do not search the web — clear vs probe.
- Loads global + project state (`show` / `project-show`) and prefers injected
  `LEARNING-PROFILE` / `LEARNING-PROJECT` when present.
- Labels project context as local; warns against promoting symbols/paths into
  the global plan.
- Ends by offering `/study-probe` or `/study-deep` — good handoff.
- Now owns missing-sheet `project-sync` (moved out of the old always-on rule).

**Problems / risks**

- Restates a shortened transferability / anti-promotion policy that also lives
  in `project-learning-boundary.mdc` and again in the probe rubric.
- “Gaps” in the snapshot can surface transferable concepts that are neither
  queued nor covered. The Skill does **not** say whether to auto-`want` those
  gaps. Interaction with `concept-gap-capture` during a plan turn is unclear
  (**open**).
- Onboarding overlap with `study-log` (see above).
- Auto-invoke description includes phrases like “what they know” / “what to
  learn next”, which can collide with probe intent (“verify what they know”) —
  **open** whether descriptions need sharper disambiguation.
- `project-sync` for stack/candidates is here; probe uses `project-sync` only
  for `--probe-summary`. That split is reasonable but not spelled out as an
  ownership contract anywhere except this document.

### `study-probe` — findings

**Role as written:** active assessment with evidence; updates covered/queue from
scored answers; uses an on-demand rubric.

**What works well**

- Strongest owner of “evidence = understanding” among the Skills.
- Forces reading `assessment-rubric.md` before questions/scoring.
- Topic selection prefers queue, focus, then generalized project candidates.
- Explicitly waits for answers before any profile write.
- Distinguishes global vs project-local in the final report.
- Uses `project-drop` / `project-sync --probe-summary` for local sheet hygiene.

**Problems / risks**

- Embeds a full CLI persistence block (`covered`, `want`, `project-drop`,
  `project-sync`). Overlaps `learning-recording` for `want`/`covered`; the
  project-* commands are probe-specific and probably should stay here.
- Repeats transferability guidance already present in the boundary rule and
  again (more fully) in the rubric.
- Does not mention coordinating with `learning-recording` or `concept-gap-
  capture` if those rules also load during a probe session (**open**
  integration behavior).
- Choosing 5–10 topics every run conflicts with the decided one-topic probe
  model (Decision 1A). Implementation must narrow selection to a single topic
  and ask multiple questions about that topic only.

### `study-probe/references/assessment-rubric.md` — findings

**Role as written:** question design, transferability gate, scoring bands
(covered / partial / gap), evidence-note quality.

**What works well**

- Progressive disclosure: detail loads only when probe needs it.
- Clear anti-patterns (definition trivia, repo identifiers, yes/no, exposure ≠
  proof).
- Scoring bands map cleanly to `covered` vs queue reinforcement.
- Level guidance for `covered` (beginner / intermediate / advanced).

**Problems / risks**

- The transferability gate text is nearly a second copy of
  `project-learning-boundary.mdc`. **Open:** keep a short reminder in the
  rubric (probe-local examples are useful) vs. point at the rule and keep only
  probe-specific examples/scoring here.
- This file is the canonical evidence policy for `covered`. The implementation
  must bind `study-log`, `study-probe`, and `learning-recording` to it: neither
  self-report nor an explanation in chat can create a `covered` entry.

### `study-deep` — findings

**Role as written:** resolve topic/level, delegate curated research to
`study-researcher`, return the track, optionally queue the topic.

**What works well**

- Keeps heavy research out of the main chat via subagent delegation.
- Falls back to `queue-next` when no topic is given; asks if queue empty.
- Uses project stack/candidates as context only, not as the selected topic.
- Finish step asks before `want` — does not silently mutate the queue.
- Persistence mention is light (“stable CLI `want`”) rather than a full catalog.

**Problems / risks**

- Does not point at `learning-recording` for the write contract (markers,
  feedback line, CLI-missing behavior).
- After delivering a track, does not offer `/study-probe` to attest learning —
  integration with evidence policy is missing (**open** whether deep should
  hand off to probe).
- Does not update `covered` (correct for a research Skill), but nothing in the
  Skill states that completion of a track is **not** evidence — easy for a
  model to drift if recording rules are soft.
- Depends on `agents/study-researcher.md` for quality; that agent was **not**
  inspected in this pass (deferred).

### Cross-skill integration map

How the Skills are intended to chain (as written today):

```text
concept_gap (rule) ──want──► queue
                │
                ▼
         study-plan ──offers──► study-probe ──covered/want──► profile
                │                      ▲
                └──offers──► study-deep ──optional want──► queue
                                   │
                                   └──(? open)──► study-probe

study-log ── explicit want/init ──► profile
          └── request to attest learning ──► study-probe ──► covered/want
```

Shared dependencies every Skill assumes:

- Stable CLI at `~/.cursor/learning/cli.py` (installed by `sessionStart`)
- Optional injected `LEARNING-PROFILE` / `LEARNING-PROJECT`
- Global profile for queue/covered; project sheet for local context only

### Skills decisions and implementation plan

#### Decision 1 — evidence required for `covered`

Self-report is not evidence. Saying “I understand X” or “I learned X”, receiving
an explanation, reading a study track, or completing an operational task must
not create a `covered` entry.

#### Decision 1A — one-topic probe; 50% applies to that topic

A probe is always about **one** topic, never a multi-topic exam across the
whole queue/stack. The 50% threshold is scored **for that topic only**.

If the user wants to attest several topics, run separate one-topic probes
(sequentially or on later turns). Never aggregate unrelated topics into one
score and then write multiple `covered` entries from that aggregate.

Implementation:

1. Make `study-probe` the only workflow that can attest new knowledge as
   `covered`.
2. Change `study-probe` topic selection: pick exactly one transferable topic
   (user-supplied, `queue-next`, or an explicit choice). Do not select 5–10
   topics in a single probe.
3. Ask multiple short practical questions about that one topic; wait for
   answers; score with the rubric.
4. If at least 50% of that topic’s answers are correct → record `covered` for
   that topic with an evidence note. Otherwise keep/add `want` for the topic;
   do not write `covered`.
5. Change `study-log`: requests to mark knowledge as learned must route to a
   one-topic probe; `study-log` remains responsible for `want`, `init`, and
   profile correction workflows that do not attest new knowledge.
6. Change `learning-recording`: accept a new `covered` write only when it comes
   with one-topic probe evidence; never infer it from self-report or teaching
   exposure.
7. Change the assessment rubric to state: one topic per probe; ≥50% correct on
   that topic’s questions; evidence note required for every accepted
   `covered`.
8. Add scenarios/tests proving that self-report does not write `covered`, a
   failed one-topic probe keeps/adds `want`, a passing one-topic probe writes
   `covered` for that topic only, and multi-topic aggregation is forbidden.

### Open questions (Skills) — undecided, keep visible

These are recorded for later decisions. Do not treat them as resolved:

2. **Onboarding owner:** Empty profile → `study-plan`, `study-log`, or either
   with identical steps?
3. **Auto-invoke collision:** Tighten `study-plan` vs `study-probe`
   descriptions so “what I know” does not ambiguously trigger both?
4. **Plan gaps → queue:** May `study-plan` write `want` for listed gaps, or only
   recommend `/study-log` / wait for `concept-gap-capture`?
5. **Recording contract in Skills:** Replace duplicated CLI blocks with “follow
   `learning-recording`” plus skill-specific extras (`init`, `project-drop`,
   probe-summary), or keep CLI copies for Skills that must work even when the
   intelligent rule does not load?
6. **Transferability copies:** One canonical rule + short reminders, or allow
   the rubric to keep a full gate because probe examples are valuable there?
7. **Deep → probe handoff:** Should `study-deep` always offer a probe after the
   track? (If yes, that probe must still be one-topic, matching Decisions 1/1A.)
8. ~~**Probe light mode:** Support fewer than 5 questions for quick checks?~~
   **Superseded by Decision 1A:** probes are one-topic; question count is about
   depth on that topic, not how many topics to pack in. Exact question count
   per topic can still be tuned later, but multi-topic “light exams” are out.
9. **Marker fallback in Skills:** Should `study-log` / others emit markers when
   CLI is missing, or is “open a new chat” enough?
10. **Force-log of repo-local topics via `study-log`:** Allow, warn, or block?

## What should move out of rules

| Current content | Better owner | Reason |
|---|---|---|
| Project stack scan and `project-sync` workflow | `study-plan` / `study-probe` Skills | Multi-step, on-demand workflow |
| Probe scoring | `study-probe/references/assessment-rubric.md` | Detailed reference loaded only when needed |
| Deep research delegation | `study-deep` Skill | Specialized orchestration |
| Onboarding questions | `study-plan` and `study-log` Skills | Interactive workflow |
| Full CLI catalog | README / CLI help | Not required in prompt context |
| Marker implementation details | `learning-recording.mdc` only | Single canonical persistence contract |

## Runtime rules vs repository-maintainer rules

There are two different audiences:

1. `rules/` — shipped by the plugin and applied to users of Learning Tutor
2. `.cursor/rules/` — guidance for contributors editing this repository

Do not mix them.

Potential maintainer-only rules could include:

- `.cursor/rules/plugin-components.mdc`
  - Glob: `rules/**/*.mdc, skills/**/SKILL.md, agents/**/*.md`
  - Enforce English copy and component boundaries
- `.cursor/rules/hooks-python.mdc`
  - Glob: `hooks/**/*.py`
  - Enforce backward-compatible profile migrations and CLI validation

These would improve development of the plugin without being distributed as
tutor behavior.

## Why not use globs for the runtime tutoring policies

Concept gaps and learning decisions are triggered by conversation semantics.
They can occur while any file type is open. A `**/*.py` or `**/*.ts` glob would
scope the policy to the implementation language rather than to the user's
intent.

Use descriptive intelligent rules for tutoring policies. Reserve globs for
maintainer rules tied to files in this repository.

## Proposed target structure

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

The maintainer rules are optional and should be added only for recurring
mistakes observed while developing this repository.

## Migration sequence

1. ~~Extract the minimal always-on `tutor-core.mdc`.~~ **Done**
2. ~~Add the three intelligent runtime rules with specific descriptions.~~ **Done**
3. Remove duplicated workflows from runtime rules; keep them in Skills.
   (Ownership pass using the overlap map and the Skills audit open questions —
   decide per item, then edit; leave undecided items listed in the doc.)
4. Define one evidence policy for `covered` before changing recording behavior.
   **Decision made:** only a one-topic `study-probe` with at least 50% correct
   on that topic can attest new knowledge. Multi-topic probes are forbidden.
5. Add automated checks for:
   - valid `.mdc` frontmatter
   - at most one small `alwaysApply: true` runtime rule
   - no duplicated CLI blocks across runtime rules
   - Skills do not restate the full recording contract when a pointer suffices
6. Install the plugin locally and inspect the active context in new chats.
7. Test a scenario matrix before release.

## Scenario matrix

### Rules-focused scenarios

| Prompt | Expected rules | Expected result |
|---|---|---|
| “Fix this failing test” | core only | No learning write |
| “What is HTTP keep-alive?” | core + concept capture + recording | One transferable `want` |
| “What does `MediaUploadEngineMixin` do?” | core + project boundary | Repo answer, no global write |
| “Test whether I understand Cursor rules” | core; `study-probe` Skill | Evidence-based assessment |
| “Build a deep Docker study track” | core; `study-deep` Skill | Research delegated to subagent |
| “Add this topic to my queue” | core + recording | Explicit `want` |

### Skills-focused scenarios

| Prompt | Expected Skill | Expected result | Open risk |
|---|---|---|---|
| `/study-log` + “I learned Docker” | `study-log` → one-topic `study-probe` | No immediate write; ≥50% on Docker → `covered` | — |
| “What is saved for study?” | `study-plan` | Snapshot; no quiz | Description collision with probe (Q3) |
| `/study-plan` in repo without project sheet | `study-plan` | Optional `project-sync` once | — |
| `/study-probe` | `study-probe` + rubric | One topic → questions → wait → ≥50% → write | CLI overlap with recording rule (Q5) |
| `/study-deep` with empty topic | `study-deep` | `queue-next` or ask; subagent track | No probe handoff (Q7) |
| Empty profile + `/study-plan` | `study-plan` | Onboarding `init` + wants | Overlap with `study-log` onboarding (Q2) |
| Empty profile + `/study-log` alone | `study-log` | Onboarding `init` + ask topic | Same as above (Q2) |

## Success criteria

- Only one small runtime rule is always applied.
- Ordinary coding requests do not load persistence or project-learning policy.
- Conceptual questions still produce exactly one transferable queue item.
- Repository-specific questions never pollute the global profile.
- Skills remain the sole owners of multi-step study workflows.
- The active-context panel confirms expected rules for every scenario above.
- Rule behavior has no contradiction about what qualifies as `covered`.
- Each overlapping concern has a single canonical owner (rule or skill), with
  at most a short pointer elsewhere.
- Open Skill questions in this document are either decided with an explicit
  owner change, or left listed until a decision is made.
- Skill auto-invoke descriptions do not routinely collide (plan vs probe).
- One evidence policy for `covered` is documented and reflected in
  `study-log`, `study-probe`, and `learning-recording` without contradiction.
- Every probe assesses exactly one topic; the ≥50% threshold is scored for that
  topic only; multi-topic aggregate probes are not used.

## Recommendation

Proceed with the four-rule runtime split, but do not add every possible rule at
once. Implement the core and concept-capture split first, test it in real chats,
then add recording and project-boundary rules only where observed behavior
requires them.

This follows Cursor's guidance to start simple and codify repeated failures,
while still removing the current monolithic always-on context cost.

**Status note:** after extracting `tutor-core`, the three intelligent rules were
added together (step 2) so capture, recording, and project boundary could be
validated as one coherent set. A Skills-only inspection pass is recorded in
this document. Decisions 1 and 1A lock the evidence policy: only a one-topic
`study-probe` with ≥50% correct on that topic can write `covered`. Remaining
open Skill questions still need ownership decisions before code changes for
step 3/4. Agents/hooks inspection is still deferred.
