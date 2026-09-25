#!/usr/bin/env python3
"""Consistency checks for the spec-to-code plugin. Run from the repo root.

Catches the drift that has bitten the pipeline before: invariant sections of the
feature-builders diverging, bloated agent descriptions (loaded into every session),
broken frontmatter, and the review-gate marker going missing on one side.
"""
import json
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "spec-to-code"
AGENTS = PLUGIN / "agents"
SKILLS = PLUGIN / "skills"
TEMPLATE = SKILLS / "create-feature-builder" / "template.md"

# Agent descriptions are always in context; keep each one a sentence or two.
DESCRIPTION_BUDGET = 400
MARKER = "[run-stage:review-follows]"
# Everything from this heading to the end of the file is shared by every feature-builder.
INVARIANT_START = "## Step 5"

errors = []


def fail(msg):
    errors.append(msg)


def frontmatter(path):
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        fail(f"{path}: missing frontmatter")
        return {}
    # Template placeholders are not valid YAML flow syntax; neutralize them.
    raw = re.sub(r"\{\{(\w+)\}\}", r"\1", m.group(1))
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        fail(f"{path}: invalid frontmatter YAML: {e}")
        return {}
    return data if isinstance(data, dict) else {}


def invariant(path):
    text = path.read_text()
    i = text.find(INVARIANT_START)
    if i < 0:
        fail(f"{path}: no '{INVARIANT_START}' section")
        return ""
    return text[i:]


for manifest in [ROOT / ".claude-plugin" / "marketplace.json", PLUGIN / ".claude-plugin" / "plugin.json"]:
    try:
        json.loads(manifest.read_text())
    except (OSError, json.JSONDecodeError) as e:
        fail(f"{manifest}: {e}")

names = {}
for path in sorted(AGENTS.glob("*.md")) + [TEMPLATE]:
    fm = frontmatter(path)
    for field in ("name", "description", "model", "color"):
        if not fm.get(field):
            fail(f"{path}: frontmatter missing '{field}'")
    desc = fm.get("description") or ""
    if len(desc) > DESCRIPTION_BUDGET:
        fail(f"{path}: description is {len(desc)} chars (budget {DESCRIPTION_BUDGET})")
    if "<example>" in desc:
        fail(f"{path}: description contains <example> blocks")
    if path != TEMPLATE:
        if "{{" in path.read_text():
            fail(f"{path}: unfilled template placeholder")
        name = fm.get("name")
        if name in names:
            fail(f"{path}: duplicate agent name '{name}' (also {names[name]})")
        names[name] = path

for path in sorted(SKILLS.glob("*/SKILL.md")):
    fm = frontmatter(path)
    for field in ("name", "description"):
        if not fm.get(field):
            fail(f"{path}: frontmatter missing '{field}'")

builders = sorted(AGENTS.glob("*-feature-builder.md"))
reference = invariant(TEMPLATE)
for path in builders:
    if invariant(path) != reference:
        fail(f"{path}: sections from '{INVARIANT_START}' to the end differ from {TEMPLATE.name}")

for path in [SKILLS / "run-stage" / "SKILL.md", AGENTS / "spec-builder.md", AGENTS / "story-creator.md", TEMPLATE, *builders]:
    if MARKER not in path.read_text():
        fail(f"{path}: review-gate marker {MARKER} missing")

if errors:
    print("\n".join(f"FAIL {e}" for e in errors))
    sys.exit(1)
print(f"OK: {len(names)} agents, {len(builders)} feature-builder(s) in sync with the template")
