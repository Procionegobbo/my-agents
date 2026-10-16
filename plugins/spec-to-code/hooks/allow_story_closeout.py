#!/usr/bin/env python3
"""Auto-approve the feature-builder close-out commands, and nothing else.

Close-out is `mv` (or `git mv`) of one story from STORIES/TODO/ to STORIES/COMPLETED/,
and a one-line append to STORIES/COMPLETED.md. Anything that does not match exactly
falls through to the normal permission flow.
"""
import json
import re
import sys

STORY = r"STORIES/TODO/[A-Za-z0-9._-]+\.md"
MOVE = re.compile(rf"(?:git )?mv {STORY} STORIES/COMPLETED/")
APPEND = re.compile(
    r'echo "- \[[A-Za-z0-9._-]+\.md\]\(COMPLETED/[A-Za-z0-9._-]+\.md\)" >> STORIES/COMPLETED\.md'
)

command = json.load(sys.stdin).get("tool_input", {}).get("command", "").strip()
if MOVE.fullmatch(command) or APPEND.fullmatch(command):
    # Visible with `claude --debug`; tells an hook approval apart from the classifier's.
    print(f"allow_story_closeout: approved `{command}`", file=sys.stderr)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "spec-to-code story close-out",
        }
    }))
