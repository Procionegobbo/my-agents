# Agents — Developer Guide

This repo contains a set of Claude Code agents that cover the full lifecycle of a feature: from rough idea to implemented code. The agents are designed to work together in a defined sequence, each handing off to the next.

---

## Agents overview

| Agent | Model | Purpose |
|---|---|---|
| `stories-init` | haiku | One-time setup — creates the required folder structure |
| `spec-builder` | opus | Expands a rough draft into a complete, implementation-ready specification |
| `story-creator` | sonnet | Breaks a specification into INVEST-compliant user stories with acceptance criteria |
| `laravel-feature-builder` | opus | Implements a story end-to-end in a Laravel codebase |

> **Note:** `laravel-feature-builder` is the first of a family of feature-builder agents. Future agents (`go-feature-builder`, `python-feature-builder`, `express-feature-builder`, etc.) will share the same folder structure and conventions and can be dropped in without changes to the other agents.

---

## Installation

Agent files (`.md`) must be placed in a specific directory so Claude Code can discover them automatically.

### Option A — Project-specific (recommended)

Use this when the agents are relevant to one repo only. The files are checked into version control and shared with the whole team.

```
your-repo/
  .claude/
    agents/
      stories-init.md
      spec-builder.md
      story-creator.md
      laravel-feature-builder.md
```

Copy the agent files from this repo into `.claude/agents/` at the root of the target project:

```bash
mkdir -p your-repo/.claude/agents
cp *.md your-repo/.claude/agents/
```

### Option B — Global (personal use)

Use this when you want the agents available across all your projects without adding them to each repo individually.

```bash
mkdir -p ~/.claude/agents
cp *.md ~/.claude/agents/
```

### Activation

Claude Code scans both locations automatically at session start — no configuration or CLAUDE.md entry is needed. If you add or edit an agent file while a session is already running, **restart the session** to pick up the changes.

> **Important:** Each agent is identified by the `name` field in its frontmatter, not by its filename. Keep `name` values unique across all agents in the same scope to avoid silent conflicts.

---

## Folder structure

All agents operate on a shared `STORIES/` directory at the root of your project. Run `stories-init` once to create it.

```
STORIES/
  SPECS/        ← draft and completed specifications live here
  TODO/         ← stories ready to be implemented
  COMPLETED/    ← stories that have been implemented and moved here
  COMPLETED.md  ← index of all completed stories, appended by feature-builder agents
```

---

## Workflow

```
Your idea / draft
      │
      ▼
 stories-init        ← run once per project
      │
      ▼
  spec-builder        ← write a draft in STORIES/SPECS/, then run this
      │
      ▼
  story-creator       ← run on the completed spec
      │
      ▼
 feature-builder      ← run on each story in STORIES/TODO/
      │
      ▼
   STORIES/COMPLETED/ ← story is moved here when done
```

---

## Step-by-step instructions

### 1. Set up the folder structure

Run this once per project, before using any other agent.

```
> Run stories-init
```

The agent will:
- Create `STORIES/SPECS/`, `STORIES/TODO/`, and `STORIES/COMPLETED/`, each with a `.gitkeep` so they are tracked by Git.
- Create an empty `STORIES/COMPLETED.md` index file.
- Create only what is missing and never touch existing files, so it is safe to re-run on a complete or partial structure.

---

### 2. Write a feature draft

Create a new markdown file in `STORIES/SPECS/`. The filename should be short and descriptive.

```
STORIES/SPECS/user-search.md
```

Your draft can be as rough as you like — bullet points, a paragraph, half-formed ideas. The spec-builder resolves anything missing using the codebase as precedent and records its choices in the spec's *Assumptions & Decisions* section for you to review. At minimum, describe:

- What the feature does
- Who it is for
- Any constraints or business rules you already know

---

### 3. Expand the draft into a full specification

```
> Run spec-builder on STORIES/SPECS/user-search.md
```

The agent will:
1. Read your draft.
2. Explore the codebase to detect the framework, architecture patterns, naming conventions, and existing tests.
3. Resolve any ambiguities itself using the codebase as precedent, recording every judgment call in an *Assumptions & Decisions* section for you to review (it never blocks waiting for input).
4. Overwrite the draft with a complete specification that includes:
   - Feature name and description
   - Assumptions & decisions — every open point it resolved, with reasoning
   - Architecture / design overview
   - Configuration (if needed)
   - Data model (if needed)
   - Impact on existing code — specific file paths
   - Framework-specific sections (routes, policies, components, handlers, etc.)
   - Validation rules
   - Authorization and security
   - Testing — specific test cases, not just categories
   - Suggested story breakdown — ordered vertical slices as a starting point for story-creator
   - Success criteria

The resulting spec is self-contained: a developer who has never seen the draft can implement the feature from it alone.

---

### 4. Create user stories

```
> Run story-creator on STORIES/SPECS/user-search.md
```

The agent will:
1. Read the completed specification.
2. Follow the spec's *Suggested story breakdown* as the default slicing, adjusting only where a slice violates INVEST.
3. Derive the spec name from the spec file's base name (`user-search.md` → `user-search`), then check `STORIES/TODO/` and `STORIES/COMPLETED/` for files sharing that prefix to determine the next available number for that spec.
4. Break the feature into INVEST-compliant user stories, each with:
   - Standard *As a / I want / So that* format
   - A `Spec:` reference back to the specification file
   - Gherkin acceptance criteria (Given / When / Then)
   - Technical notes — the spec fragments relevant to that slice (schema, validation rules, file paths)
   - The spec's test cases belonging to that slice
   - Priority and dependencies on other stories
5. Save each story as a markdown file in `STORIES/TODO/`, named `<spec-name>-<number>-<story-name>.md`. Numbering is scoped per spec and starts at `001`.

Example output (from a spec named `user-search`):
```
STORIES/TODO/user-search-001-basic.md
STORIES/TODO/user-search-002-filters.md
STORIES/TODO/user-search-003-autocomplete.md
```

---

### 5. Implement a story

Pick a story from `STORIES/TODO/` and run the appropriate feature-builder for your stack.

**Laravel:**
```
> Run laravel-feature-builder on STORIES/TODO/user-search-001-basic.md
```

The agent will:
1. Read the story, its acceptance criteria, and the spec referenced by its `Spec:` line.
2. Explore the codebase to detect the project's architecture, naming conventions, and existing patterns.
3. Implement the feature end-to-end: migrations, models, controllers or Livewire components, form requests, services, routes, policies, and views.
4. Write tests following the project's test conventions and run them until green, along with the formatter and static analysis if configured.
5. Verify every acceptance criterion is satisfied.
6. Only then: move the story file from `STORIES/TODO/` to `STORIES/COMPLETED/` and append an entry to `STORIES/COMPLETED.md`. If something cannot be completed, the story stays in `STORIES/TODO/` and the agent reports exactly what failed.

If requirements are ambiguous, the agent resolves them from the spec and codebase precedent and lists its judgment calls in the final report.

---

## Typical session

```
# First time
> Initialize the stories workspace
> Write my draft in STORIES/SPECS/asset-collection.md
> Run spec-builder on the asset-collection draft
> Run story-creator on the asset-collection spec

# Implementation
> Run laravel-feature-builder on STORIES/TODO/asset-collection-001-model.md
> Run laravel-feature-builder on STORIES/TODO/asset-collection-002-crud.md
```

---

## Adding a new feature-builder

To support a new language or framework, create a new agent file following the same conventions as `laravel-feature-builder.md`:

1. Name it `<stack>-feature-builder.md`.
2. Use the same frontmatter fields (`name`, `description`, `model`, `color`).
3. Instruct it to read stories from `STORIES/TODO/`, implement the feature, move the story to `STORIES/COMPLETED/`, and append to `STORIES/COMPLETED.md`.

The `stories-init`, `spec-builder`, and `story-creator` agents are stack-agnostic and require no changes.

---

## Working in parallel

The per-spec story numbering means multiple developers can work on different specs without filename collisions. To avoid stepping on each other in the working tree, follow a **branch-per-spec** convention:

1. Before running `story-creator` (or a feature-builder) for a spec, create a branch named `story/<spec-name>` — e.g. `story/user-search`.
2. Commit the generated stories, the implementation, and the `STORIES/` changes on that branch.
3. Open a PR and merge as usual.

Because story files are prefixed per spec, two branches never create files with the same name. The one shared file is `STORIES/COMPLETED.md`:

- It is **append-only**, so a concurrent edit shows up as a merge conflict that is always resolved by **keeping both sides** (each branch's appended lines). Never delete the other branch's entries when resolving.

---

## Notes

- **Story numbering** — stories are named `<spec-name>-<number>-<story-name>.md`, and numbering is scoped per spec (each spec starts at `001`). The story-creator checks both `STORIES/TODO/` and `STORIES/COMPLETED/` for files sharing the same spec-name prefix to find the highest existing number for that spec and increments from there. Because numbers are per-spec, multiple developers can work on different specs in parallel without story-number conflicts.
- **Spec overwrites draft** — `spec-builder` replaces the draft in-place. If you want to preserve the original, duplicate the file before running the agent.
- **COMPLETED.md is append-only** — feature-builder agents only append to this file. They never truncate or overwrite it.
- **Git tracking** — `.gitkeep` files ensure the empty folders are committed. They can be removed once real files exist in each folder.
