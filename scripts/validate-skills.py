#!/usr/bin/env python3
"""Validate the installable skills as packages that consumers install in isolation.

Checks what skill installers (Codex skill-installer, Claude Code, skillshare) rely on:
frontmatter shape, install name, description limits, agent metadata, self-contained
relative links, content that skillshare's install audit treats as high severity, and
repository-wide content that its CRITICAL rules would block in a tracked install.
Standard library only. Exit status 1 when any error is found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = {"client": "client/skill", "server": "server/skill", "monorepo": "monorepo/skill", "development": "development/skill"}
ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
ALLOWED_ENTRIES = {"SKILL.md", "agents", "references"}
OPENAI_FIELDS = ("display_name", "short_description", "default_prompt")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TRIGGER_RE = re.compile(r"(?i)(use\s+(this\s+)?(skill\s+)?when|trigger\s+when|activate\s+when|invoke\s+when|use\s+for)")
# Mirrors skillshare's built-in audit rule prompt-injection-2 (HIGH): placeholders such as
# `system` in angle brackets read as agent directive tags, so use descriptive placeholders.
DIRECTIVE_TAG_RE = re.compile(r"(?i)</?(system|instructions|override|prompt|rules)\b[^>]*>")
# Mirrors skillshare's blocking prompt-injection rules. A tracked install (`--track`) audits
# every file in the repository, so these apply repository-wide; quote object keys such as
# `"admin":` in code samples rather than starting a line with `admin:`.
REPO_AUDIT_RULES = {
    "prompt-injection-0": re.compile(r"(?i)(ignore\s+(all\s+)?previous\s+instructions|disregard\s+(all\s+)?rules|you\s+are\s+now\b|forget\s+everything|override\s+safety)"),
    "prompt-injection-1": re.compile(r"(?im)^\s*(SYSTEM|OVERRIDE|IGNORE|ADMIN|ROOT):"),
    "prompt-injection-3": re.compile(r"(?im)^\s*(DEV(ELOPER)?[\s_]*MODE|JAILBREAK|DAN[\s_.]*MODE)\b"),
    # HIGH, not CRITICAL, but it blocks tracked installs run with `-T high`.
    "prompt-injection-2": DIRECTIVE_TAG_RE,
}
# Skillshare's own project configuration is not audited as skill content.
REPO_SCAN_EXCLUDES = {".git", ".skillshare", "node_modules"}
REPO_SCAN_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".sh", ".txt", ".html", ".ts", ".tsx", ".js"}
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.S)
# Directories that hold tooling state or installed third-party skills, not repository skills.
DISCOVERY_EXCLUDES = {".git", ".skillshare", ".agents", ".claude", ".opencode", "node_modules"}


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str]:
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not match:
        return None, text
    fields: dict[str, str] = {}
    key = None
    for line in match.group(1).splitlines():
        top = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if top:
            key, value = top.group(1), top.group(2).strip()
            fields[key] = "" if value in {"|", ">", "|-", ">-"} else value.strip("\"'")
        elif key and line.startswith((" ", "\t")):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields, match.group(2)


def check_skill(name: str, rel: str) -> list[str]:
    errors: list[str] = []
    skill_dir = REPO_ROOT / rel
    root = skill_dir.resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{rel}: missing SKILL.md"]

    fields, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    if fields is None:
        errors.append(f"{rel}/SKILL.md: missing or unterminated YAML frontmatter")
        fields = {}
    unexpected = set(fields) - ALLOWED_KEYS
    if unexpected:
        errors.append(f"{rel}/SKILL.md: unexpected frontmatter keys {sorted(unexpected)}")
    skill_name = fields.get("name", "")
    if skill_name != name:
        errors.append(f"{rel}/SKILL.md: name {skill_name!r} must equal install name {name!r}")
    if not NAME_RE.match(skill_name) or len(skill_name) > 64:
        errors.append(f"{rel}/SKILL.md: name must be hyphen-case and at most 64 characters")
    description = fields.get("description", "")
    if not description:
        errors.append(f"{rel}/SKILL.md: missing description")
    if len(description) > 1024:
        errors.append(f"{rel}/SKILL.md: description has {len(description)} characters (limit 1024)")
    if "<" in description or ">" in description:
        errors.append(f"{rel}/SKILL.md: description must not contain angle brackets")
    if description and not TRIGGER_RE.search(description):
        errors.append(f"{rel}/SKILL.md: description needs a trigger phrase such as 'Use when' or 'Use for'")
    if not body.strip():
        errors.append(f"{rel}/SKILL.md: body is empty")

    for entry in skill_dir.iterdir():
        if entry.name not in ALLOWED_ENTRIES:
            errors.append(f"{rel}: unexpected entry {entry.name!r} would be installed with the skill")

    openai = skill_dir / "agents" / "openai.yaml"
    if not openai.is_file():
        errors.append(f"{rel}: missing agents/openai.yaml")
    else:
        text = openai.read_text(encoding="utf-8")
        if not re.match(r"^interface:\s*$", text.splitlines()[0] if text else ""):
            errors.append(f"{rel}/agents/openai.yaml: must start with an interface mapping")
        for field in OPENAI_FIELDS:
            if not re.search(rf"^\s+{field}:\s*\S", text, re.M):
                errors.append(f"{rel}/agents/openai.yaml: missing interface.{field}")
        if f"${name}" not in text:
            errors.append(f"{rel}/agents/openai.yaml: default_prompt should invoke ${name}")

    for path in sorted(skill_dir.rglob("*")):
        shown = path.relative_to(REPO_ROOT)
        if path.is_symlink():
            errors.append(f"{shown}: symlinks are not portable in installed skills")
            continue
        if not path.is_file() or path.suffix not in {".md", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            tag = DIRECTIVE_TAG_RE.search(line)
            if tag:
                errors.append(f"{shown}:{lineno}: {tag.group(0)!r} is flagged by skillshare audit as an agent directive tag")
        if path.suffix != ".md":
            continue
        for match in LINK_RE.finditer(FENCE_RE.sub("", text)):
            target = match.group(1)
            if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            resolved = (path.parent / target_path).resolve()
            if resolved != root and root not in resolved.parents:
                errors.append(f"{shown}: link {target!r} leaves the skill directory and breaks when installed")
            elif not resolved.exists():
                errors.append(f"{shown}: link {target!r} does not resolve")
    return errors


def check_discovery() -> list[str]:
    expected = {(REPO_ROOT / rel / "SKILL.md").resolve() for rel in SKILLS.values()}
    errors = []
    for path in REPO_ROOT.rglob("SKILL.md"):
        parts = set(path.relative_to(REPO_ROOT).parts)
        if parts & DISCOVERY_EXCLUDES:
            continue
        if path.resolve() not in expected:
            errors.append(f"{path.relative_to(REPO_ROOT)}: unexpected SKILL.md would be discovered by repository installers")
    return errors


def check_repository_content() -> list[str]:
    errors = []
    for path in sorted(REPO_ROOT.rglob("*")):
        rel = path.relative_to(REPO_ROOT)
        if set(rel.parts) & REPO_SCAN_EXCLUDES or path.is_symlink() or not path.is_file():
            continue
        if path.suffix not in REPO_SCAN_SUFFIXES and path.name not in {"LICENSE"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        for rule, pattern in REPO_AUDIT_RULES.items():
            for match in pattern.finditer(text):
                lineno = text.count("\n", 0, match.start()) + 1
                errors.append(f"{rel}:{lineno}: matches skillshare audit rule {rule} ({match.group(0).strip()!r}) that would block a tracked install")
    return errors


def main() -> int:
    errors = check_discovery()
    errors.extend(check_repository_content())
    for name, rel in SKILLS.items():
        errors.extend(check_skill(name, rel))
    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"  {error}")
        return 1
    print(f"Skills are valid ({', '.join(SKILLS)}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
