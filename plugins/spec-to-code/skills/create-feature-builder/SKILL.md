---
name: create-feature-builder
description: >-
  Generate a repo-tailored <stack>-feature-builder agent for the STORIES pipeline.
  Use when the user asks to add a feature-builder, support a new stack, or scaffold
  the implementation agent for this repo.
allowed-tools: Read, Glob, Grep, Write
---

# create-feature-builder

Generate a `<stack>-feature-builder` agent tailored to the current repository. The
generated agent joins the STORIES pipeline (`stories-init` → `spec-builder` →
`story-creator` → `<stack>-feature-builder`) and implements one story at a time from
`STORIES/TODO/`.

The agent is written from `template.md` (sibling of this file). You fill its placeholders
with values discovered in the target repo. Run this skill inline so you can confirm the
stack with the user before generating — a subagent could not.

## Phase 1 — Detect the stack

Read the root config files and identify the framework from actual dependencies, not just
file presence:

- `composer.json` → check `require` for `laravel/framework`, `symfony/*`, etc.
- `package.json` → check dependencies for `express`, `next`, `@nestjs/*`, `react`, etc.
- `go.mod`, `pyproject.toml` / `manage.py` (Django) / `requirements.txt`, `Cargo.toml`, `Gemfile` (Rails).

**Propose the detected stack to the user and ask them to confirm** (they may override).

- **No detection**: if no known config is present or the signal is ambiguous, ask the user
  to name the stack, then proceed with that assumption.
- **Polyglot repo**: list the stacks found and let the user choose. `<stack>` is the
  **backend framework**; the frontend approach is recorded in the agent's implementation
  notes, not in the name. One run generates one builder.

## Phase 2 — Explore the repo (tiered specialization)

Explore like `spec-builder` Step 1, proportional to what the template needs. Capture two
tiers of values:

**Authoritative (stable) — hardcode as directives:**
- Test command (e.g. `composer test`, `./vendor/bin/pest`, `pytest`, `go test ./...`, `npm test`).
- Formatter command (e.g. Pint, Black/Ruff, gofmt, Prettier), if configured.
- Static-analysis command (e.g. PHPStan/Larastan, mypy, golangci-lint, ESLint), if configured.

**Topology (volatile) — emit as dated seed hints:**
- Architecture (MVC / DDD / layered / modular).
- Real paths of models, controllers/handlers, routes, tests.
- 2–3 existing features closest to typical stories (the precedent to read).
- Naming conventions, frontend approach, authorization mechanism.

If a command or tool isn't configured, leave its placeholder as the language default the
template already implies, and note "not configured" rather than inventing one.

## Phase 3 — Check collisions

- If `.claude/agents/<stack>-feature-builder.md` **already exists**, treat this run as a
  **refresh**: regenerate it, summarize what changed (new test command, moved paths), and
  ask the user to confirm before overwriting.
- Also check `~/.claude/agents/<stack>-feature-builder.md`. Agent `name` fields must be
  unique across scopes, so on a global collision warn the user or offer a distinct name.
- A missing `STORIES/` structure does **not** block generation (it's only needed when the
  generated agent runs). If it's absent, suggest running `stories-init`.

## Phase 4 — Generate the agent

Read `template.md` and write `.claude/agents/<stack>-feature-builder.md`, filling every
placeholder verbatim:

| Placeholder | Value |
|---|---|
| `{{STACK}}` | confirmed stack name (also the filename prefix) |
| `{{COLOR}}` | see below |
| `{{DATE}}` | today's date, `YYYY-MM-DD` |
| `{{CONFIG_FILES}}` | the config files that declare the stack |
| `{{TEST_FRAMEWORK}}` / `{{FORMATTER}}` / `{{STATIC_ANALYSIS}}` | tools observed |
| `{{TEST_COMMAND}}` / `{{FORMATTER_COMMAND}}` / `{{STATIC_ANALYSIS_COMMAND}}` | authoritative commands |
| `{{ARCHITECTURE}}` | detected architecture |
| `{{DISCOVERED_PATHS}}` | real layer paths (seed hints) |
| `{{SIMILAR_FEATURES}}` | 2–3 precedent features to read |
| `{{FRONTEND}}` / `{{AUTH_MECHANISM}}` | detected approaches |
| `{{FRAMEWORK_IMPL_NOTES}}` | concern-level bullets for this stack (persistence / validation / authorization / view layer) — **not** Laravel vocabulary like migrations or form requests unless this *is* Laravel |

- **Color**: pick from the fixed palette `red, orange, yellow, green, blue, purple, cyan,
  pink` a value not already used by agents in the target repo's `.claude/agents/`; if all
  are taken, fall back to the first. (You only see the target repo's agents, not global ones.)
- **Model**: keep `opus`.

**Self-validation (mandatory) before finishing:**
- The frontmatter parses as valid YAML and all four fields are present: `name`, `description`, `model`, `color`. Keep `description` a **double-quoted** scalar (the template already is) and escape any `"` you introduce as `\"` — an unquoted description with a `: ` in it silently drops the whole frontmatter at load time.
- No leftover `{{` tokens anywhere in the file (grep for `{{`).
- If Claude Code is on the machine, run `claude plugin validate` on the agent's directory as a final check.
- Fix any failure before reporting done.

## Phase 5 — Report

Report back:
1. The generated file and its path.
2. The hardcoded specifics (test / formatter / static-analysis commands, key paths).
3. That the user must **restart the Claude Code session** for the new agent to be discovered.
