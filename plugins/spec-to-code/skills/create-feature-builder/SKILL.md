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

## Optional argument — scope to a subfolder

The skill accepts an optional **target subfolder** (e.g. the user says "for `server/`" or
passes it as the argument). When present, treat that folder as the project root for
**everything**: stack detection, exploration, discovered paths, and the commands baked into
the generated agent. Use it for **monorepos** where each service has its own stack and there
is no single root config.

When a scope folder is given:
- Detect and explore **only inside that folder** (Phase 1 and 2). Ignore config in sibling
  services and at the repo root.
- Record it as `{{SCOPE_ROOT}}` and make the generated agent operate within it — its commands
  run from that folder and its discovered paths are relative to it.
- Expect to generate **several builders** in a monorepo, so disambiguate the name: propose a
  name derived from the service folder (e.g. `server-feature-builder`,
  `discord-bot-feature-builder`) rather than the bare stack, and **ask the user to confirm or
  override** before generating.

When no folder is given, behave exactly as before: detect from the repo root and set
`{{SCOPE_ROOT}}` to the repo root (`.`).

## Phase 1 — Detect the stack

Read the config files **at the scope root** (repo root, or the target subfolder if one was
given) and identify the framework from actual dependencies, not just file presence:

- `composer.json` → check `require` for `laravel/framework`, `symfony/*`, etc.
- `package.json` → check dependencies for `express`, `next`, `@nestjs/*`, `react`, etc.
- `go.mod`, `pyproject.toml` / `manage.py` (Django) / `requirements.txt`, `Cargo.toml`, `Gemfile` (Rails).

When detection is clear, carry on: the stack is confirmed together with everything else in
Phase 3, so the user is asked once. Ask now only when you cannot proceed without an answer:

- **No detection**: if no known config is present or the signal is ambiguous, ask the user
  to name the stack, then proceed with that assumption.
- **Polyglot repo**: list the stacks found and let the user choose. `<stack>` is the
  **backend framework**; the frontend approach is recorded in the agent's implementation
  notes, not in the name. One run generates one builder.

## Phase 2 — Explore the repo (tiered specialization)

Explore like `spec-builder` Step 1, proportional to what the template needs, **confined to
the scope root** if one was given. Capture two tiers of values (paths recorded relative to
the scope root):

**Authoritative (stable) — hardcode as directives:**
- Test command (e.g. `composer test`, `./vendor/bin/pest`, `pytest`, `go test ./...`, `npm test`).
- Formatter command (e.g. Pint, Black/Ruff, gofmt, Prettier), if configured.
- Static-analysis command (e.g. PHPStan/Larastan, mypy, golangci-lint, ESLint), if configured.

**Topology (volatile) — emit as dated seed hints:**
- Architecture (MVC / DDD / layered / modular).
- Real paths of models, controllers/handlers, routes, tests.
- 2–3 existing features closest to typical stories (the precedent to read).
- Naming conventions, frontend approach, authorization mechanism.

**Engineering concerns — how this project handles each one** (feeds `{{FRAMEWORK_IMPL_NOTES}}`):
- Persistence: ORM or query layer, migrations, how indexes and constraints are declared.
- Validation: where input is validated and with what (form requests, schemas, serializers, DTOs).
- Authorization: the mechanism and where it is invoked.
- Interface layer: controllers/handlers/components and where business logic lives.
- Side effects: transactions, async jobs/queues, how outbound HTTP is made.
- Errors: the project's error types and central handling.
- Tests: test DB setup, factories/fixtures, how time and external services are faked.

Find each in the precedent features — grep for the mechanism rather than reading whole
directories. Stop at config files plus the 2–3 precedents; do not survey the whole repo. A
concern the project has no equivalent for (no database, no queue) is recorded as "not
applicable", not filled with a stack default.

If a command or tool isn't configured, leave its placeholder as the language default the
template already implies, and note "not configured" rather than inventing one. Remember the
gap for Phase 3: the tool this stack would normally use (e.g. Ruff, ESLint, PHPStan). Never
install or configure it yourself.

## Phase 3 — Check collisions and confirm

- The collision check uses the **confirmed agent name** (`<stack>-feature-builder`, or the
  service-scoped name from the optional-argument step). In a monorepo, a same-stack builder
  for a *different* service is not a refresh — it's a distinct agent, which is exactly why the
  scoped name disambiguates it.
- If `.claude/agents/<name>.md` **already exists** for the same target, treat this run as a
  **refresh**: regenerate it, summarize what changed (new test command, moved paths), and
  ask the user to confirm before overwriting.
- Also check `~/.claude/agents/<name>.md`. Agent `name` fields must be unique across scopes,
  so on a global collision warn the user or offer a distinct name.
- A missing `STORIES/` structure does **not** block generation (it's only needed when the
  generated agent runs). If it's absent, suggest the `stories-init` skill (or note that
  `run-stage` creates it on first use).

**Confirm once, then generate.** Show the user a compact summary and wait for an ok or
corrections:
- the stack and the agent name (and whether this is a refresh of an existing builder);
- the test / formatter / static-analysis commands, flagging any "not configured" with the
  tool you would suggest;
- the `{{FRAMEWORK_IMPL_NOTES}}` bullets you are about to write.

Apply corrections before writing. If the user changes the stack, redo Phase 2 for it.

## Phase 4 — Generate the agent

Read `template.md` and write `.claude/agents/<agent-slug>-feature-builder.md` — at the
**repository root**, even when the agent is scoped to a subfolder, since that is where Claude
Code discovers project agents — filling every placeholder verbatim. Everything else in the
template, including the Engineering standards section and Step 5 onward, is copied unchanged:
those are pipeline invariants shared with `code-reviewer`.

| Placeholder | Value |
|---|---|
| `{{AGENT_SLUG}}` | the confirmed agent name prefix and filename — the bare stack (`express`) when unscoped, or the service-scoped name (`server`) confirmed with the user in a monorepo |
| `{{STACK}}` | the framework/language label used in prose (`Express`, `Node.js`, `Django`) — stays the technical stack even when `{{AGENT_SLUG}}` is service-scoped |
| `{{SCOPE_ROOT}}` | the folder the agent operates within — the target subfolder (e.g. `server`) when scoped, or `.` (repo root) when not |
| `{{COLOR}}` | see below |
| `{{DATE}}` | today's date, `YYYY-MM-DD` |
| `{{CONFIG_FILES}}` | the config files (under the scope root) that declare the stack |
| `{{TEST_FRAMEWORK}}` / `{{FORMATTER}}` / `{{STATIC_ANALYSIS}}` | tools observed |
| `{{TEST_COMMAND}}` / `{{FORMATTER_COMMAND}}` / `{{STATIC_ANALYSIS_COMMAND}}` | authoritative commands, written to run from the scope root (e.g. `npm test`, since the agent runs them inside `{{SCOPE_ROOT}}`) |
| `{{ARCHITECTURE}}` | detected architecture |
| `{{DISCOVERED_PATHS}}` | real layer paths, relative to the scope root (seed hints) |
| `{{SIMILAR_FEATURES}}` | 2–3 precedent features to read |
| `{{FRONTEND}}` / `{{AUTH_MECHANISM}}` | detected approaches |
| `{{FRAMEWORK_IMPL_NOTES}}` | one bullet per engineering concern from Phase 2, in the format below |

**`{{FRAMEWORK_IMPL_NOTES}}` format.** One bullet per concern, bold label first. Each names
the project's *actual* mechanism (with a precedent path when it helps) and says how it
satisfies the Engineering standards that touch that concern — validation at the boundary,
allow-listed writes, authorization on every action, escaping, transactions, N+1, async and
timeouts, test fakes. Use this stack's vocabulary, never another stack's. Do not restate the
standards themselves; the agent already carries them. Shape, from a hypothetical Django repo:

```
- **Validation**: DRF serializers in `api/serializers/`; write only `serializer.validated_data`, with explicit `fields` (never `__all__`) on writable serializers.
- **Authorization**: permission classes on every viewset (see `orders/views.py`); querysets filtered to `request.user` for object access.
- **Side effects**: `transaction.atomic()` around multi-model writes; email and webhooks via Celery tasks; `requests` calls always pass `timeout=`.
- **Tests**: pytest-django with `factory_boy` factories; `freezegun` for time, `responses` for outbound HTTP.
```

- **Color**: pick from the fixed palette `red, orange, yellow, green, blue, purple, cyan,
  pink` a value not already used by agents in the target repo's `.claude/agents/`; if all
  are taken, fall back to the first. (You only see the target repo's agents, not global ones.)
- **Model**: keep `sonnet`, matching `laravel-feature-builder`. The judgment-heavy work
  (spec and slicing) already happened upstream on opus; the builder executes a small,
  well-specified story and is checked by `code-reviewer`.
- **Description**: keep it to the one sentence the template carries. Agent descriptions are
  loaded into every session's context, so each extra line is paid on every conversation —
  and example dialogues that name the builder directly teach the main session to bypass
  `run-stage` and its review gate.

**Self-validation (mandatory) before finishing:**
- Re-read the generated file and confirm the frontmatter is valid YAML with all four fields present: `name`, `description`, `model`, `color`. Keep `description` a **double-quoted** scalar (the template already is) and escape any `"` you introduce as `\"` — an unquoted description with a `: ` in it silently drops the whole frontmatter at load time.
- Grep the file for `{{` and confirm no placeholder tokens remain.
- Confirm the Engineering standards section and everything from `## Step 5` on match `template.md` exactly.
- Fix any failure before reporting done.

## Phase 5 — Report

Report back:
1. The generated file and its path.
2. The scope it was tailored to (`{{SCOPE_ROOT}}`) when a subfolder was given.
3. The hardcoded specifics (test / formatter / static-analysis commands, key paths), and for
   any tool marked "not configured", the one you suggest adding.
4. That the generated agent expects an independent **code-reviewer** pass as a close-out gate (Step 5), orchestrated by the `run-stage` skill — subagents cannot spawn subagents, so the loop runs one level up. Tell the user to launch it via `run-stage` (`/spec-to-code:run-stage`) rather than invoking the agent directly, or the story closes out on a self-review instead of a real review.
5. That the user must **restart the Claude Code session** for the new agent to be discovered.
