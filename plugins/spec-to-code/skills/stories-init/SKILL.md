---
name: stories-init
description: >-
  Create the STORIES/ workspace the spec-to-code pipeline needs (SPECS/, TODO/,
  COMPLETED/ with .gitkeep files, and an empty COMPLETED.md), adding only what is
  missing. Use once per project, or when the STORIES folder is absent or incomplete.
allowed-tools: Bash(ls:*), Bash(mkdir:*), Bash(touch:*)
---

# stories-init

Ensure this structure exists in the project root (the current working directory):

```
STORIES/
  SPECS/.gitkeep
  TODO/.gitkeep
  COMPLETED/.gitkeep
  COMPLETED.md
```

This is a skill rather than an agent on purpose: the whole job is two shell commands, and a
subagent would cost a cold start plus a permanent entry in every session's agent list.

## Steps

1. Record what already exists: `ls -A STORIES STORIES/SPECS STORIES/TODO STORIES/COMPLETED`
   (errors for missing paths are expected).
2. Create what is missing. Both commands are idempotent and never modify content —
   `mkdir -p` skips existing folders, `touch` on an existing file only updates its
   timestamp, so an existing `COMPLETED.md` keeps its entries:

   ```bash
   mkdir -p STORIES/SPECS STORIES/TODO STORIES/COMPLETED
   touch STORIES/SPECS/.gitkeep STORIES/TODO/.gitkeep STORIES/COMPLETED/.gitkeep STORIES/COMPLETED.md
   ```

3. Report in two or three lines: what you created, what already existed, and the next step
   — write a draft in `STORIES/SPECS/<feature>.md`, then run `run-stage` with `spec-builder`
   on it. If no feature-builder exists for this project yet, mention the
   `create-feature-builder` skill.

## Rules

- Never delete, overwrite, or truncate anything, and never write outside `STORIES/`.
- Do not inspect or name the project's stack — this step has no reason to know it, and a
  wrong guess misleads the user.
