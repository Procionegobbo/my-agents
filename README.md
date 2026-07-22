# Agents — Developer Guide

This repo is a Claude Code **plugin** (`spec-to-code`) — a set of agents plus a skill that cover the full lifecycle of a feature: from rough idea to implemented code. The agents are designed to work together in a defined sequence, each handing off to the next. The repo doubles as its own plugin **marketplace** (`my-agents`), so it can be installed with one command.

---

## Agents overview

| Agent | Model | Purpose |
|---|---|---|
| `stories-init` | haiku | One-time setup — creates the required folder structure |
| `spec-builder` | opus | Expands a rough draft into a complete, implementation-ready specification |
| `spec-reviewer` | haiku | Independently audits a spec against a fixed rubric and returns a pass/fail verdict |
| `story-creator` | sonnet | Breaks a specification into INVEST-compliant user stories with acceptance criteria |
| `story-reviewer` | haiku | Independently audits the stories for coverage, INVEST, and faithfulness to the spec |
| `laravel-feature-builder` | opus | Implements a story end-to-end in a Laravel codebase |
| `code-reviewer` | sonnet | Independently reviews an implementation, re-running the tests and checking acceptance-criteria coverage |

> **Note:** `laravel-feature-builder` is the first of a family of feature-builder agents. Future agents (`go-feature-builder`, `python-feature-builder`, `express-feature-builder`, etc.) share the same folder structure and conventions and can be dropped in without changes to the other agents.

### Built-in review loop

Each producing agent runs a **generator → independent review** loop before finishing: after its own self-check, it invokes the matching reviewer agent (a separate agent, on a cheaper model, with a clean context) which audits the output against a fixed rubric and returns a structured `VERDICT: APPROVED` or `VERDICT: CHANGES_REQUESTED` (with issues classified BLOCKING / NON-BLOCKING). The producer fixes the blocking issues and re-reviews, up to **2 rounds**, then finishes.

- **spec-builder → spec-reviewer**, **story-creator → story-reviewer**: never block the pipeline. Any blocking issue left after the last round is recorded as a `Review Notes (unresolved)` note and surfaced in the final report for you to decide on.
- **feature-builder → code-reviewer**: the review is a real gate. A blocking issue that survives the last round (a failing test, an uncovered acceptance criterion) keeps the story in `STORIES/TODO/` — it is not moved to `COMPLETED/` — exactly like a failing test.

The loop runs automatically inside each step; you invoke the pipeline exactly as before. Reviewers can also be run standalone on an existing artifact. The loop needs a Claude Code version that exposes sub-agent dispatch to sub-agents (**v2.1.172+**); on older versions each agent falls back to a reinforced self-review against the same rubric and says so in its report.

## Skills

| Skill | Purpose |
|---|---|
| `create-feature-builder` | Generates a `<stack>-feature-builder` agent tailored to the current repo — detects the stack, explores the codebase, and writes the agent into `.claude/agents/`. Automates the manual process described in *Adding a new feature-builder*. |

Invoke it as a slash command. Installed as a plugin, skills are namespaced: `/spec-to-code:create-feature-builder`. Copied manually into `.claude/skills/`, it is `/create-feature-builder`.

---

## Installation

### Option A — Plugin (recommended)

Install the whole pipeline (all agents + the skill) in one step. This gives you versioned, updatable installs and works across every project.

```
/plugin marketplace add Procionegobbo/my-agents
/plugin install spec-to-code@my-agents
```

Update later with `/plugin marketplace update my-agents`, then `/plugin update spec-to-code`.

> **Note:** plugin skills are namespaced (`/spec-to-code:create-feature-builder`). Plugin agents keep their frontmatter `name` (`spec-builder`, `laravel-feature-builder`, …) and are invoked the same way as before. A same-named agent in the project's own `.claude/agents/` overrides the plugin's version.

### Option B — Manual copy

Use this when you want the files checked into a specific repo (or your global `~/.claude/`) without the plugin system. Copy from `plugins/spec-to-code/` in this repo:

```bash
# into a project (or swap the target for ~/.claude)
mkdir -p your-repo/.claude/agents your-repo/.claude/skills
cp plugins/spec-to-code/agents/*.md your-repo/.claude/agents/
cp -r plugins/spec-to-code/skills/create-feature-builder your-repo/.claude/skills/
```

Copied this way the skill is invoked as `/create-feature-builder` (no namespace).

### Activation

Claude Code discovers plugins, agents, and skills at session start — no configuration or CLAUDE.md entry is needed. If you install a plugin or add/edit an agent or skill file while a session is already running, **restart the session** (or run `/reload-plugins` for plugin changes) to pick them up.

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
      │  └─ spec-reviewer     (automatic review loop, ≤2 rounds)
      ▼
  story-creator       ← run on the completed spec
      │  └─ story-reviewer    (automatic review loop, ≤2 rounds)
      ▼
 feature-builder      ← run on each story in STORIES/TODO/
      │  └─ code-reviewer     (automatic review loop, ≤2 rounds — gates close-out)
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
5. Verify every acceptance criterion is satisfied, then run the project's full test suite once to catch regressions outside the touched areas.
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

To support a new language or framework, run the `create-feature-builder` skill in the target repo:

```
/spec-to-code:create-feature-builder
```

(Or `/create-feature-builder` if you installed via manual copy.)

The skill detects the stack from the project's config files (asking you to confirm), explores the codebase for its test command, formatter, architecture, and precedent features, then writes a `<stack>-feature-builder.md` agent into `.claude/agents/` — tailored to that repo and following the same conventions as `laravel-feature-builder.md`. **Restart the session** afterwards so Claude Code discovers the new agent.

### Monorepos — scoping to a subfolder

By default the skill detects the stack from the repository root. In a **monorepo** where each service has its own stack (and there may be no root config), pass the target subfolder and the skill confines everything — stack detection, exploration, the generated agent's paths and commands — to that folder:

```
/spec-to-code:create-feature-builder for server/
```

Because a monorepo produces several builders, the skill proposes a per-service name (e.g. `server-feature-builder`) and asks you to confirm it, so builders for different services don't collide. Run it once per service you want to support.

The `stories-init`, `spec-builder`, and `story-creator` agents are stack-agnostic and require no changes.

> Prefer to write it by hand? Copy `laravel-feature-builder.md`, rename it `<stack>-feature-builder.md`, keep the same frontmatter fields (`name`, `description`, `model`, `color`), and adapt the stack-specific steps. Keep Step 5 and the final report identical — they are pipeline invariants shared across all feature-builders.

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
- **Spec overwrites draft** — `spec-builder` replaces the draft in-place. If the draft is committed and unmodified, git preserves the original; otherwise the agent first copies it to `<name>.draft.md` so no work is lost.
- **COMPLETED.md is append-only** — feature-builder agents only append to this file. They never truncate or overwrite it.
- **Git tracking** — `.gitkeep` files ensure the empty folders are committed. They can be removed once real files exist in each folder.
