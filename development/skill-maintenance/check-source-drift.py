#!/usr/bin/env python3
"""Validate curated development skill references against canonical source guides."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
MAINTENANCE_DIR = SCRIPT_PATH.parent
DEVELOPMENT_DIR = MAINTENANCE_DIR.parent
SKILL_DIR = DEVELOPMENT_DIR / "skill"
MANIFEST_PATH = MAINTENANCE_DIR / "source-map.json"
HASH_ALGORITHM = "sha256(path-null-file-sha256-newline, sources sorted by path)"
EXPECTED_SLICES = {"init", "foundations", "portless", "nextjs", "nodejs"}


class DriftError(RuntimeError):
    """Raised when the source mapping cannot be validated."""


def load_manifest() -> dict[str, Any]:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise DriftError(f"Missing manifest: {MANIFEST_PATH}") from error
    except json.JSONDecodeError as error:
        raise DriftError(f"Invalid JSON in {MANIFEST_PATH}: {error}") from error

    if manifest.get("version") != 1:
        raise DriftError("source-map.json must use version 1")
    if manifest.get("hashAlgorithm") != HASH_ALGORITHM:
        raise DriftError(f"source-map.json must use {HASH_ALGORITHM!r}")
    if not isinstance(manifest.get("sourceRoot"), str):
        raise DriftError("source-map.json must declare sourceRoot")
    if not isinstance(manifest.get("slices"), dict):
        raise DriftError("source-map.json must declare a slices object")
    if set(manifest["slices"]) != EXPECTED_SLICES:
        missing = EXPECTED_SLICES - set(manifest["slices"])
        extra = set(manifest["slices"]) - EXPECTED_SLICES
        parts = []
        if missing:
            parts.append(f"missing: {', '.join(sorted(missing))}")
        if extra:
            parts.append(f"unexpected: {', '.join(sorted(extra))}")
        raise DriftError("Invalid slice set (" + "; ".join(parts) + ")")
    return manifest


def resolve_repo_root(manifest: dict[str, Any], override: str | None) -> Path:
    root = (
        Path(override).expanduser().resolve()
        if override
        else (MAINTENANCE_DIR / manifest["sourceRoot"]).resolve()
    )
    if not (root / ".git").exists() or not (root / "development" / "README.md").is_file():
        raise DriftError(
            f"Source repository not found at {root}. This maintainer-only check "
            "must run against the node-architecture source checkout."
        )
    return root


def source_fingerprint(repo_root: Path, sources: list[str]) -> str:
    digest = hashlib.sha256()
    for relative_path in sorted(sources):
        source_path = repo_root / relative_path
        if not source_path.is_file():
            raise DriftError(f"Missing source document: {relative_path}")
        file_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_digest.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def validate_entry(repo_root: Path, name: str, entry: Any) -> str:
    if not isinstance(entry, dict):
        raise DriftError(f"Slice {name!r} must be an object")

    reference = entry.get("reference")
    sources = entry.get("sources")
    expected = entry.get("fingerprint")

    if not isinstance(reference, str) or not (repo_root / reference).is_file():
        raise DriftError(f"Slice {name!r} has a missing reference: {reference!r}")
    if not reference.startswith("development/skill/references/"):
        raise DriftError(
            f"Slice {name!r} reference must stay inside development/skill/references"
        )
    if not isinstance(sources, list) or not sources or not all(
        isinstance(value, str) for value in sources
    ):
        raise DriftError(f"Slice {name!r} must declare a non-empty source list")
    if len(sources) != len(set(sources)):
        raise DriftError(f"Slice {name!r} declares duplicate source paths")
    if any(
        not source.startswith("development/")
        or source.startswith("development/skill/")
        or not source.endswith(".md")
        for source in sources
    ):
        raise DriftError(f"Slice {name!r} contains an invalid source path")
    if not isinstance(expected, str) or len(expected) != 64:
        raise DriftError(f"Slice {name!r} must declare a 64-character fingerprint")
    try:
        bytes.fromhex(expected)
    except ValueError as error:
        raise DriftError(f"Slice {name!r} fingerprint must be hexadecimal") from error

    return source_fingerprint(repo_root, sources)


def canonical_sources(repo_root: Path) -> set[str]:
    return {
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "development").rglob("*.md")
        if SKILL_DIR.resolve() not in path.resolve().parents
    }


def validate_coverage(repo_root: Path, slices: dict[str, Any]) -> None:
    mapped = {
        source
        for entry in slices.values()
        if isinstance(entry, dict) and isinstance(entry.get("sources"), list)
        for source in entry["sources"]
        if isinstance(source, str)
    }
    canonical = canonical_sources(repo_root)
    missing = canonical - mapped
    unknown = mapped - canonical
    if missing or unknown:
        parts = []
        if missing:
            parts.append("unmapped: " + ", ".join(sorted(missing)))
        if unknown:
            parts.append("not canonical: " + ", ".join(sorted(unknown)))
        raise DriftError("Invalid canonical source coverage (" + "; ".join(parts) + ")")


def write_manifest(manifest: dict[str, Any]) -> None:
    temporary_path = MANIFEST_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(MANIFEST_PATH)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check or refresh development skill source fingerprints."
    )
    parser.add_argument(
        "--repo-root",
        help="Override the node-architecture repository root.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("check", help="Check mappings and fingerprints (default).")
    refresh = subparsers.add_parser(
        "refresh", help="Refresh one reviewed slice fingerprint."
    )
    refresh.add_argument("slice", help="Reviewed slice name.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    command = args.command or "check"
    try:
        manifest = load_manifest()
        repo_root = resolve_repo_root(manifest, args.repo_root)
        slices: dict[str, Any] = manifest["slices"]

        validate_coverage(repo_root, slices)
        actual = {
            name: validate_entry(repo_root, name, entry)
            for name, entry in sorted(slices.items())
        }

        if command == "refresh":
            name = args.slice
            if name not in slices:
                raise DriftError(f"Unknown slice: {name}")
            slices[name]["fingerprint"] = actual[name]
            write_manifest(manifest)
            print(f"Refreshed development slice {name}: {actual[name]}")

        drifted = [
            name
            for name in sorted(slices)
            if name != getattr(args, "slice", None)
            and slices[name]["fingerprint"] != actual[name]
        ]
        if drifted:
            print("Development skill references require review:", file=sys.stderr)
            for name in drifted:
                print(
                    f"  {name}: expected current fingerprint {actual[name]}",
                    file=sys.stderr,
                )
            print(
                "Review each affected reference, then run refresh SLICE.",
                file=sys.stderr,
            )
            return 1

        if command == "check":
            print(
                f"Development skill source map is current "
                f"({len(slices)} slices, {len(canonical_sources(repo_root))} guides)."
            )
        return 0
    except DriftError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
