---
name: run-stage
description: >-
  Run a spec-to-code pipeline stage (spec-builder, story-creator, or any
  <stack>-feature-builder) together with its independent review gate. Use whenever the
  user asks to run one of those agents, to review a spec/story/implementation, or to take
  a feature through the STORIES pipeline — including when they ask to run one *without*
  review, which this skill also covers. The review loop must be orchestrated from the top
  level because subagents cannot spawn subagents.
---

# run-stage

Runs one pipeline stage as **producer → independent reviewer → fix → re-review**, up to
2 fix rounds for the blocking stage and 1 for the advisory ones (see *Round caps*).

Each producing agent used to spawn its own reviewer. It cannot: the harness exposes the
`Agent` tool only at the top level, so a subagent has no spawn primitive at all (`ToolSearch
select:Agent` returns nothing from inside one). The loop therefore runs here, in your
context, where `Agent` and `SendMessage` genuinely exist — but may be deferred rather than
already loaded.

**Load them before you judge whether you have them.** Not seeing `Agent` or `SendMessage` in
your currently loaded tools does not mean they are unavailable here — unlike inside a
subagent, where they are truly absent, at this level they may simply need loading. Run
`ToolSearch` with `select:Agent,SendMessage` first. Only if that call returns neither may
you treat them as unavailable and drop to "If you cannot spawn either" below.

**Run this skill inline.** Do not delegate the orchestration itself to a subagent — it
would land in the same position and be unable to spawn anything.

## Skipping the review gate

If the user explicitly asks for the producer **without** a review — "senza review", "no review
loop", "just run spec-builder", "solo il producer", "quick pass" — honour it. Do not run the
protocol below. Instead:

1. Spawn the producer exactly as in step 1, but **omit the `[run-stage:review-follows]`
   marker**. Its absence is the whole switch: the producer then takes its path B and runs a
   reinforced self-review against the matching reviewer's rubric before finishing.
2. Spawn no reviewer, send no follow-up. Report the producer's summary and state plainly that
   the artifact had no independent review — only the producer's own self-check.

This is a legitimate mode, not a degraded one: one agent, one run, no fix rounds. It is the
right trade when the draft is small, when you are iterating fast on wording, or when the user
has already reviewed the artifact themselves.

Two cautions, stated once and then respect the user's call:

- Path B is *self*-review, not *no* review. It is cheap — the agent already holds its codebase
  exploration — but it is the author grading their own work, which is exactly the blind spot
  the gate exists to cover.
- For a `<stack>-feature-builder` the gate is **blocking**, not advisory: it is what decides
  whether the story closes out, and it is the only thing that independently re-runs the test
  suite. Skipping it there means the story moves to `COMPLETED/` on the builder's own word that
  its tests pass. Say so before proceeding; if the user confirms, proceed.

If the user asks to skip the review for one stage of a chain but not the others, apply it only
to that stage.

## Stage map

| Producer | Reviewer | Artifact reviewed | Gate |
|---|---|---|---|
| `spec-builder` | `spec-reviewer` | the spec file in `STORIES/SPECS/` | advisory — never blocks |
| `story-creator` | `story-reviewer` | the stories in `STORIES/TODO/` for that spec | advisory — never blocks |
| `<stack>-feature-builder` | `code-reviewer` | the implementation + its story | **blocking** — gates close-out |

Agent names are namespaced when the pipeline is installed as a plugin
(`spec-to-code:spec-reviewer`). Use whichever form the `Agent` tool exposes; try the
namespaced name first, then the bare one.

## Protocol

### 1. Spawn the producer

Invoke it with `run_in_background: false` and **record the `agentId`** from its result —
you need it to send the verdict back. Include in its prompt:

- the artifact it must produce (draft path, spec path, or story path);
- the project root, if it is not the current working directory;
- the literal marker **`[run-stage:review-follows]`**, plus the instruction "do not close
  out (where applicable), and do not attempt to spawn a reviewer yourself." The marker is
  what switches the producer into review-gate mode — a fixed token no one would type by
  accident in an ordinary English request, unlike a sentence a direct invocation could
  coincidentally echo. Without it a producer invoked standalone falls back to its own
  reinforced self-review, which is correct behaviour but skips the gate.

If the producer reports it could not produce the artifact at all, stop here and report
that — there is nothing to review.

### 2. Spawn the reviewer

Before spawning it, confirm the producer's report actually shows path A (the artifact is
awaiting review) rather than a path B self-review it ran despite the marker. For a
feature-builder specifically: if the story has already moved to `STORIES/COMPLETED/`, path
A was not taken — stop, do not spawn the reviewer over work already closed out, and report
the bypass to the user instead.

Invoke the matching reviewer with `run_in_background: false`, telling it the artifact path
(and, for `code-reviewer`, the project's test command so it can re-run the suite). Record
its `agentId` too.

Keep the reviewer prompt short: the artifact path, the project root if it differs, and the
test command. Do not paste the producer's report, the spec's contents, or your own summary
into it — the reviewer reads the artifact from disk, and re-sending it doubles the cost of
the gate. `spec-reviewer` and `story-reviewer` are read-only by construction (no `Write`,
`Edit`, or `Bash`): they audit the artifact's structural soundness and its congruence with
the existing code by reading, and cannot implement or test anything. Do not ask them to.

Its response carries a `VERDICT: APPROVED` or `VERDICT: CHANGES_REQUESTED` line, with
issues classified BLOCKING / NON-BLOCKING.

**Scan the whole response for the verdict line — do not require it to be the first thing.**
Reviewers are told to lead with it, but in practice they often emit a sentence of preamble
first. Prose before the verdict is not a malformed response. If the response contains more
than one `VERDICT:` line, the last one is the verdict.

- **APPROVED** → go to step 4.
- **CHANGES_REQUESTED** → go to step 3.
- **No `VERDICT:` line anywhere in the response** (the reviewer errored, or returned only
  prose) → spawn it once more. If the second attempt also returns no verdict, treat the
  review as unavailable: `SendMessage` the producer that the review could not be run at
  all, so it falls back to its own reinforced self-review, and say so in your report.

Judge only by the verdict line and the issues under it. A reviewer that lists non-blocking
findings under `VERDICT: APPROVED` has approved the work.

### 3. Fix and re-review

1. `SendMessage` the **producer** at its recorded `agentId` with the reviewer's issues
   verbatim, split into BLOCKING and NON-BLOCKING, and ask it to fix every blocking issue
   (plus non-blocking ones where the fix is cheap and clearly correct) and reply with what
   it changed. Continuing the same agent is deliberate — it still holds its codebase
   exploration, so the fix round is cheap.
2. `SendMessage` the **reviewer** at its recorded `agentId` to re-audit the updated
   artifact. Continuing it keeps its own prior findings in view, so it can confirm each was
   addressed rather than re-deriving the rubric from scratch.

**Round caps.** Stop as soon as you get `VERDICT: APPROVED`, and otherwise:

- **advisory stages** (`spec-builder`, `story-creator`) — at most **2** reviewer invocations:
  the initial review plus 1 re-review. Blocking issues that survive get written down as
  `## Review Notes (unresolved)` either way, so a third round buys tokens, not safety.
- **the blocking stage** (`<stack>-feature-builder`) — at most **3**: the initial review plus
  2 re-reviews. Here the extra round decides whether the story closes out, so it earns its
  cost.

### 4. Close out the stage

**`spec-builder` / `story-creator` — advisory.** Never block the pipeline. If BLOCKING
issues survive the last round, `SendMessage` the producer to append a
`## Review Notes (unresolved)` section listing them (to the spec file, or to each affected
story file), then report them so the user can decide. Downstream agents already know to
treat that section as advisory audit output rather than requirements.

**`<stack>-feature-builder` — blocking gate.** The story only moves on a pass:

- `VERDICT: APPROVED`, or only NON-BLOCKING issues remain → `SendMessage` the builder to
  run its close-out step: move the story from `STORIES/TODO/` to `STORIES/COMPLETED/` and
  append the entry to `STORIES/COMPLETED.md`.
- BLOCKING issues survive the last round → `SendMessage` the builder telling it which
  issues remain unresolved; it replies confirming the story stays in `STORIES/TODO/` with
  `COMPLETED.md` untouched. Report exactly which issues blocked it. Treat this like a
  failing test, not a formality.
- One exception: if the *only* remaining blocking issue is that the reviewer could not
  execute the test command in its environment, and the builder reported running the full
  suite green itself, record it as non-blocking and let close-out proceed.

### 5. Report

Give the user:

1. What the producer did (its summary).
2. The review outcome — approved in round N, or the unresolved blocking issues.
3. For a feature-builder: whether the story moved to `COMPLETED/`, and if not, why.

## Chaining stages

When the user asks for more than one stage ("take this draft to stories"), run each stage's
full loop to completion before starting the next. Do not start `story-creator` while the
spec still has unresolved blocking issues without saying so first.

## If you cannot spawn either

Only reach this if `ToolSearch select:Agent,SendMessage` genuinely returned neither tool —
not because they weren't already sitting in your loaded tool list. If so, run the
producer's work yourself against its agent definition, then audit the result against the
matching reviewer's rubric inline, and tell the user the pipeline ran without agent
isolation.
