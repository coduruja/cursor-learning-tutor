# Assessment rubric

Use evidence of understanding, not exposure. A valid probe covers **exactly one
topic** with **5 to 10** questions; fewer than five questions must not write
`covered`.

## Transferability

Only probe what would still be useful without opening this repository. Local
detail is a starting point, never the topic:

| Local detail | Transferable concept |
|---|---|
| `LOCAL_BOT_API_URL` | Service discovery or environment-based configuration |
| `MediaUploadEngineMixin` | Mixin composition and separation of responsibilities |
| `ConnectTimeout` in one call | Connection establishment vs connection reuse |

If the starting point is local, rename to the broader concept before testing.

## Question design

Prefer questions that require the user to:

- Choose between two approaches and justify the choice
- Predict behavior or consequences
- Explain a concept in their own words with an example
- Apply the concept to a small scenario outside the current repository

Avoid:

- Definition-only trivia
- Questions whose answer is a repo-specific identifier
- Leading yes/no questions
- Treating tool usage or having read an explanation as proof of understanding

## Scoring

Score each answer, then apply the **≥50%** bar across this topic’s questions.
Only when at least half are covered-quality may the topic be recorded as
`covered`.

### Covered (per answer)

The answer is substantially correct and includes at least one of:

- Correct reasoning
- A fitting example
- Correct application to a new scenario
- A meaningful trade-off or limitation

Choose level when the topic passes the 50% bar:

- `beginner`: explains the core idea correctly
- `intermediate`: applies it and explains when/why
- `advanced`: reasons about trade-offs, failure modes, or design alternatives

### Partial (per answer)

The core intuition is present but the answer has an important gap, confusion, or
cannot transfer to a new scenario. Counts against the 50% bar. Do not treat as
covered evidence.

### Gap (per answer)

The user says they do not know, guesses without reasoning, or gives a materially
incorrect answer. Counts against the 50% bar.

### Topic outcome

- ≥50% covered-quality answers → record `covered` for this topic with an
  evidence note.
- Otherwise keep/add `want` for the topic; do not record `covered`.

## Evidence note

Write what demonstrated understanding, not merely “passed probe.”

Good:

> Chose a rule for persistent guidance and a skill for an on-demand workflow,
> then explained the context-cost trade-off.

Weak:

> Answered correctly.
