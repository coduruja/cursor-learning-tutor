# Assessment rubric

Use evidence of understanding, not exposure.

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

## Transferability gate

Before testing or recording a topic, ask:

> Would this knowledge still be useful without opening the current repository?

- **Yes** → eligible for the global profile
- **No** → keep as project context
- **Partly** → rename to the broader transferable concept before testing

Examples:

| Local detail | Transferable concept |
|---|---|
| `LOCAL_BOT_API_URL` | Service discovery or environment-based configuration |
| `MediaUploadEngineMixin` | Mixin composition and separation of responsibilities |
| `ConnectTimeout` in one call | Connection establishment vs connection reuse |

## Scoring

### Covered

The answer is substantially correct and includes at least one of:

- Correct reasoning
- A fitting example
- Correct application to a new scenario
- A meaningful trade-off or limitation

Record `covered` with a short evidence note. Choose level:

- `beginner`: explains the core idea correctly
- `intermediate`: applies it and explains when/why
- `advanced`: reasons about trade-offs, failure modes, or design alternatives

### Partial

The core intuition is present but the answer has an important gap, confusion, or
cannot transfer to a new scenario. Keep/add it in the queue with a concise
reinforcement note. Do not record `covered`.

### Gap

The user says they do not know, guesses without reasoning, or gives a materially
incorrect answer. Add it to the queue with a concise gap note.

## Evidence note

Write what demonstrated understanding, not merely “passed probe.”

Good:

> Chose a rule for persistent guidance and a skill for an on-demand workflow,
> then explained the context-cost trade-off.

Weak:

> Answered correctly.
