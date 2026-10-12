---
name: status
description: >-
  Report the current state of the STORIES/ pipeline for this project: every spec, its
  stage (draft or completed), how many stories are pending in TODO/ vs done in
  COMPLETED/, and any unresolved Review Notes left by spec-reviewer / story-reviewer.
  Read-only — no files are run, moved or written. Use when the user asks "where are we",
  wants an overview before picking what to run next, or is juggling several specs in
  parallel.
allowed-tools: Read, Glob, Grep
---

# status

A read-only snapshot of `STORIES/`. It never spawns an agent and never modifies
anything — every fact comes from filenames and a few targeted `Grep` checks, not from
re-running any stage. For what a *single* story or spec needs to progress, use
`run-stage` or `run-feature`; this skill only tells you where things stand.

## Step 0 — Workspace check

`Glob` for `STORIES/SPECS`, `STORIES/TODO`, `STORIES/COMPLETED`. If any is missing,
report that the workspace isn't set up yet and point at `stories-init`. Do not create it
yourself — this skill only reads.

## Step 1 — List the specs

`Glob` `STORIES/SPECS/*.md`, excluding any `*.draft.md` (those are `spec-builder`'s
preserved-draft backups, not specs in their own right — mention their count once, in the
summary, not per spec). For each remaining file, the spec name is its base name
(`user-search.md` → `user-search`).

For each spec, in one pass:

- **Stage.** `Grep` the file for `## Suggested Story Breakdown` and `## Success
  Criteria`. Both present → **completed**; either missing → **draft** (not yet expanded
  by `spec-builder`).
- **Unresolved review notes.** `Grep -l` for `## Review Notes (unresolved)`. Present →
  flag it; `spec-reviewer` left blocking issues the pipeline didn't block on.

## Step 2 — Count each spec's stories

For a **completed** spec only (a draft has no stories yet):

1. `Glob` `STORIES/TODO/<spec-name>-*.md` and `STORIES/COMPLETED/<spec-name>-*.md`.
2. Keep only names matching `<spec-name>-<3 digits>-` exactly — the same rule
   `story-creator` uses for numbering — so a spec named `user` never picks up
   `user-search-*` stories.
3. `Grep -l` the matched `TODO/` files for `## Review Notes (unresolved)` — issues
   `story-reviewer` left that the builder hasn't addressed.
4. A completed spec with **zero** matches in either folder has had `story-creator` run
   but produced nothing yet, or hasn't had it run at all — say so rather than reporting
   empty counts silently.

## Step 3 — Feature-builders on hand

`Glob` `.claude/agents/*-feature-builder.md`. List the stack slugs found (filename minus
the suffix). None found is worth surfacing: a completed spec with stories in `TODO/`
can't be implemented until `create-feature-builder` has run.

## Report

One block per spec, most actionable first (specs with pending `TODO/` stories or
unresolved review notes before fully completed ones), then a one-line summary:

```
<spec-name> — completed | draft (run spec-builder)
  TODO:      <n> pending  [— <filenames>, if ≤6; otherwise just the count]
  COMPLETED: <n> done
  Review notes: none | unresolved on <file(s)>

...

Feature-builders: <slug, slug, ...> | none found — run create-feature-builder
<N> spec(s), <M> stories pending, <K> unresolved review note(s). Draft backups
(*.draft.md): <count>.
```

Suggest the next command for the top entry only (`run-stage spec-builder on ...` for a
draft, `run-feature on ...` for a completed spec with pending stories, nothing for a spec
fully in `COMPLETED/` with no open notes). Keep the whole report scannable — this is a
dashboard, not a transcript of every file's contents.
