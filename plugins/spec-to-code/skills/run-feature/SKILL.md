---
name: run-feature
description: >-
  Take one spec all the way to STORIES/COMPLETED/: creates its stories (if not already
  created) and then runs every resulting <stack>-feature-builder, in dependency order,
  each through its independent code-reviewer gate — without the user invoking run-stage
  once per story. Use when the user wants a whole spec implemented end to end, or to
  resume a spec that already has some stories done or some stories stuck. Delegates
  every individual stage to the run-stage skill; use run-stage directly to run or review
  just one stage.
---

# run-feature

Loops `run-stage` over every story of one spec, back to back, from "no stories yet" (or
"some stories already done") through to every story in `STORIES/COMPLETED/`. Runs inline
for the same reason `run-stage` does: it spawns agents, and only the top-level session
can do that — do not delegate this skill's orchestration to a subagent.

## Inputs

- The **spec file** (`STORIES/SPECS/<spec-name>.md`), named or inferable from context.
- Optional: project root, if not the current working directory (monorepo).
- Optional: "no review" — same meaning as in `run-stage`, applied to every stage this
  skill runs. State the same caution `run-stage` states before honoring it for the
  feature-builder stages, since that gate is blocking there — then respect the user's
  call.

## Step 0 — Spec sanity

`run-stage`'s own step creates `STORIES/` the first time it runs, so this skill does not
duplicate that.

Skim the spec file. If it reads like an unexpanded draft (no **Suggested Story
Breakdown** / **Success Criteria** sections), stop and say so: run `spec-builder` on it
first, via `run-stage`. Do not invent a story breakdown yourself to work around this.

## Step 1 — Get the stories

1. Derive `<spec-name>` from the file's base name, exactly as `story-creator` does
   (`user-search.md` → `user-search`).
2. `Glob` `STORIES/TODO/<spec-name>-*.md` and `STORIES/COMPLETED/<spec-name>-*.md`.
3. **Nothing matches either folder** — this spec has no stories yet. Load the run-stage
   skill (`Skill` tool, `skill: "spec-to-code:run-stage"`, or bare `"run-stage"` on a
   manual-copy install) and follow its protocol for `story-creator` on the spec file,
   honoring "no review" if it was asked for. Wait for that stage to fully finish
   (including its fix/re-review rounds) before continuing.
4. **Something already matches** — stories exist for this spec already, from a prior
   `run-feature` call, a standalone `run-stage story-creator` run, or by hand. Do not
   re-run `story-creator`; go straight to building what is already in `TODO/`. Only if
   the user explicitly asked to add more stories to this spec, run `story-creator` via
   `run-stage` as in point 3 — it appends, numbering from the highest existing story for
   this spec, same as always.
5. Re-`Glob` `STORIES/TODO/<spec-name>-*.md`. This is the **pending set**. If it is empty
   (every story for this spec already sits in `COMPLETED/`), report the spec as already
   fully implemented and stop.

## Step 2 — Pick the feature-builder

`Glob` `.claude/agents/*-feature-builder.md` (project-level; plugin-provided builders are
tried by their `name`, namespaced first, the same way `run-stage` tries them).

- **Exactly one** → use it.
- **None** → stop. Tell the user to run `create-feature-builder` first; there is nothing
  to implement the stories with.
- **More than one** (a monorepo with several scoped builders) → ask the user which one
  applies to this spec. Do not guess which service a spec targets.

## Step 3 — Order the pending stories

Read every pending story's **Dependencies:** line. `story-creator` guarantees a
dependency only ever names a lower-numbered story in the same spec, so **ascending
numeric order already respects every dependency** — sort the pending set by its `<NNN>`
segment; no topological sort needed.

Keep each story's Dependencies list at hand — Step 4 needs it to decide what to skip if
an earlier story fails to close out.

## Step 4 — Run the chain

For each pending story, in that order, unless already marked **skipped** (see below):

1. Load the run-stage skill and follow its protocol for `<stack>-feature-builder` on
   this story — producer, the blocking `code-reviewer` gate, fix/re-review up to its
   round cap, close-out. This is exactly what `/spec-to-code:run-stage <builder> on
   <story>` would do by hand; running it here saves the user from typing it once per
   story.
2. Record the outcome:
   - **Closed out** (moved to `COMPLETED/`) → move on to the next story.
   - **Blocking issues survived the last round** (story still in `TODO/`) → mark it
     **failed**, with the issues `run-stage` reported for it. Then mark every
     not-yet-attempted pending story whose **Dependencies:** names this story — directly,
     or transitively through another story already marked failed or skipped — as
     **skipped: blocked by `<story>`**, and do not attempt it.
3. Continue to the next not-yet-attempted, not-skipped story. One story failing does not
   stop an unrelated, independent branch — only the stories that actually depend on it.

## Step 5 — Report

One line per pending story:

```
<story file> — completed | failed: <blocking issue summary> | skipped: blocked by <story>
```

Then state whether the spec is now fully in `COMPLETED/`, or which stories remain and
why. For anything failed, point at fixing it and re-running `run-stage` on that story
alone — or just running `run-feature` again, which will skip what already closed out and
retry only what is still pending. Do not re-paste each stage's own report; this is a
summary of the summaries.

## Rules

- Never touch `COMPLETED.md` or move a story file yourself — that only ever happens
  inside the `run-stage` protocol you are following for that story, exactly as it would
  standalone.
- Never skip a review gate silently. Unless "no review" was asked for, every stage here
  carries it, same as calling `run-stage` by hand for each one.
- Don't attempt a story whose dependency failed or was skipped, even if its own Gherkin
  looks self-contained — trust the **Dependencies:** field over your own read of whether
  it would actually work standalone.
