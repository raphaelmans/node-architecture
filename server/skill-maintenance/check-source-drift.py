#!/usr/bin/env python3
"""Validate curated server skill references against canonical source guides."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
MAINTENANCE_DIR = SCRIPT_PATH.parent
SERVER_DIR = MAINTENANCE_DIR.parent
SKILL_DIR = SERVER_DIR / "skill"
MANIFEST_PATH = MAINTENANCE_DIR / "source-map.json"
HASH_ALGORITHM = "sha256(path-null-file-sha256-newline, sources sorted by path)"
EXPECTED_SLICES = {
    "contracts",
    "data-flow",
    "foundations",
    "operations",
    "runtimes",
    "scaffolding",
    "security",
    "telemetry",
    "testing",
    "workspace",
}


class DriftError(RuntimeError):
    """Raised when the source mapping cannot be validated."""


def load_manifest() -> dict[str, Any]:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise DriftError(f"Missing manifest: {MANIFEST_PATH}") from error
    except json.JSONDecodeError as error:
        raise DriftError(f"Invalid JSON in {MANIFEST_PATH}: {error}") from error

    if manifest.get("version") != 2:
        raise DriftError("source-map.json must use version 2")
    if manifest.get("hashAlgorithm") != HASH_ALGORITHM:
        raise DriftError(f"source-map.json must use {HASH_ALGORITHM!r}")
    if not isinstance(manifest.get("sourceRoot"), str):
        raise DriftError("source-map.json must declare sourceRoot")
    if not isinstance(manifest.get("slices"), dict):
        raise DriftError("source-map.json must declare a slices object")
    if not isinstance(manifest.get("leaves"), dict):
        raise DriftError("source-map.json must declare a leaves object")
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


def reference_entries(manifest: dict[str, Any]) -> dict[str, Any]:
    slices = manifest["slices"]
    leaves = manifest["leaves"]
    duplicate_names = set(slices) & set(leaves)
    if duplicate_names:
        raise DriftError(
            "Names must be unique across slices and leaves: "
            + ", ".join(sorted(duplicate_names))
        )
    for name, entry in leaves.items():
        parents = entry.get("parents") if isinstance(entry, dict) else None
        if (
            not isinstance(parents, list)
            or not parents
            or not all(isinstance(parent, str) for parent in parents)
        ):
            raise DriftError(f"Convention leaf {name!r} must declare non-empty slice parents")
        if len(parents) != len(set(parents)):
            raise DriftError(f"Convention leaf {name!r} declares duplicate slice parents")
        unknown = set(parents) - set(slices)
        if unknown:
            raise DriftError(
                f"Convention leaf {name!r} has unknown slice parents: "
                + ", ".join(sorted(unknown))
            )
    return {**slices, **leaves}


def resolve_repo_root(manifest: dict[str, Any], override: str | None) -> Path:
    root = (
        Path(override).expanduser().resolve()
        if override
        else (MAINTENANCE_DIR / manifest["sourceRoot"]).resolve()
    )
    if not (root / ".git").exists() or not (root / "server" / "README.md").is_file():
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
        raise DriftError(f"Reference {name!r} must be an object")

    reference = entry.get("reference")
    sources = entry.get("sources")
    expected = entry.get("fingerprint")

    if not isinstance(reference, str) or not (repo_root / reference).is_file():
        raise DriftError(f"Reference {name!r} has a missing reference: {reference!r}")
    if not (repo_root / reference).resolve().is_relative_to(
        (repo_root / "server/skill/references").resolve()
    ):
        raise DriftError(f"Reference {name!r} must stay inside server/skill/references")
    if not isinstance(sources, list) or not sources or not all(
        isinstance(value, str) for value in sources
    ):
        raise DriftError(f"Reference {name!r} must declare a non-empty source list")
    if len(sources) != len(set(sources)):
        raise DriftError(f"Reference {name!r} declares duplicate source paths")
    if any(
        (
            not source.startswith("server/")
            and not source.startswith("monorepo/")
        )
        or source.startswith("server/skill/")
        or source.startswith("monorepo/skill/")
        or ".." in Path(source).parts
        or not source.endswith(".md")
        for source in sources
    ):
        raise DriftError(f"Reference {name!r} contains an invalid source path")
    if not isinstance(expected, str) or len(expected) != 64:
        raise DriftError(f"Reference {name!r} must declare a 64-character fingerprint")
    try:
        bytes.fromhex(expected)
    except ValueError as error:
        raise DriftError(f"Reference {name!r} fingerprint must be hexadecimal") from error

    return source_fingerprint(repo_root, sources)


def canonical_sources(repo_root: Path) -> set[str]:
    return {
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "server").rglob("*.md")
        if (repo_root / "server/skill").resolve() not in path.resolve().parents
    }


def validate_coverage(repo_root: Path, references: dict[str, Any]) -> None:
    mapped = {
        source
        for entry in references.values()
        if isinstance(entry, dict) and isinstance(entry.get("sources"), list)
        for source in entry["sources"]
        if isinstance(source, str)
    }
    canonical = canonical_sources(repo_root)
    missing = canonical - mapped
    external = {source for source in mapped if source.startswith("monorepo/")}
    unknown = mapped - canonical - external
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
        description="Check or refresh server skill source fingerprints."
    )
    parser.add_argument(
        "--repo-root",
        help="Override the node-architecture repository root.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("check", help="Check mappings and fingerprints (default).")
    refresh = subparsers.add_parser(
        "refresh", help="Refresh reviewed slice or convention-leaf fingerprints."
    )
    refresh.add_argument("references", nargs="+", help="Reviewed slice or convention-leaf names.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    command = args.command or "check"
    try:
        manifest = load_manifest()
        repo_root = resolve_repo_root(manifest, args.repo_root)
        slices: dict[str, Any] = manifest["slices"]
        leaves: dict[str, Any] = manifest["leaves"]
        references = reference_entries(manifest)

        actual = {
            name: validate_entry(repo_root, name, entry)
            for name, entry in sorted(references.items())
        }
        validate_coverage(repo_root, references)

        requested = set(getattr(args, "references", []))
        if command == "refresh":
            unknown = requested - set(references)
            if unknown:
                raise DriftError(f"Unknown reference(s): {', '.join(sorted(unknown))}")
            for name in sorted(requested):
                references[name]["fingerprint"] = actual[name]
                print(f"Refreshed server reference {name}: {actual[name]}")
            write_manifest(manifest)

        drifted = [
            name
            for name in sorted(references)
            if name not in requested
            and references[name]["fingerprint"] != actual[name]
        ]
        if drifted:
            print("Server skill references require review:", file=sys.stderr)
            for name in drifted:
                print(
                    f"  {name}: expected current fingerprint {actual[name]}",
                    file=sys.stderr,
                )
            print(
                "Review each affected reference, then run refresh REFERENCE [REFERENCE ...].",
                file=sys.stderr,
            )
            return 1

        if command == "check":
            print(
                f"Server skill source map is current "
                f"({len(slices)} slices, {len(leaves)} convention leaves, "
                f"{len(canonical_sources(repo_root))} guides)."
            )
        return 0
    except DriftError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
