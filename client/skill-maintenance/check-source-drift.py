#!/usr/bin/env python3
"""Validate curated client skill references against their source documents."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
MAINTENANCE_DIR = SCRIPT_PATH.parent
CLIENT_DIR = MAINTENANCE_DIR.parent
SKILL_DIR = CLIENT_DIR / "skill"
MANIFEST_PATH = MAINTENANCE_DIR / "source-map.json"


class DriftError(RuntimeError):
    """Raised when the source mapping cannot be validated."""


def find_repo_root() -> Path:
    for candidate in (MAINTENANCE_DIR, *MAINTENANCE_DIR.parents):
        source_manifest = candidate / "client" / "skill-maintenance" / "source-map.json"
        if (candidate / ".git").exists() and source_manifest.is_file():
            try:
                if source_manifest.samefile(MANIFEST_PATH):
                    return candidate
            except OSError:
                continue
    raise DriftError(
        "Source repository not found. This maintainer-only check must run from "
        "the node-architecture source checkout."
    )


def load_manifest() -> dict[str, Any]:
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise DriftError(f"Missing manifest: {MANIFEST_PATH}") from error
    except json.JSONDecodeError as error:
        raise DriftError(f"Invalid JSON in {MANIFEST_PATH}: {error}") from error

    if (
        data.get("version") != 2
        or not isinstance(data.get("slices"), dict)
        or not isinstance(data.get("leaves"), dict)
    ):
        raise DriftError(
            "source-map.json must contain version 2 with slices and leaves objects"
        )
    return data


def fingerprint(repo_root: Path, sources: list[str]) -> str:
    digest = hashlib.sha256()
    for relative_path in sorted(sources):
        source_path = repo_root / relative_path
        if not source_path.is_file():
            raise DriftError(f"Missing source document: {relative_path}")
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(source_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def validate_entry(repo_root: Path, kind: str, name: str, entry: Any) -> str:
    if not isinstance(entry, dict):
        raise DriftError(f"{kind} {name!r} must be an object")

    reference = entry.get("reference")
    sources = entry.get("sources")
    expected = entry.get("fingerprint")

    if not isinstance(reference, str) or not (repo_root / reference).is_file():
        raise DriftError(f"{kind} {name!r} has a missing reference: {reference!r}")
    if not isinstance(sources, list) or not sources or not all(
        isinstance(value, str) for value in sources
    ):
        raise DriftError(f"{kind} {name!r} must declare a non-empty source list")
    if len(sources) != len(set(sources)):
        raise DriftError(f"{kind} {name!r} declares duplicate source paths")
    if not isinstance(expected, str) or len(expected) != 64:
        raise DriftError(f"{kind} {name!r} must declare a 64-character fingerprint")
    try:
        bytes.fromhex(expected)
    except ValueError as error:
        raise DriftError(f"{kind} {name!r} fingerprint must be hexadecimal") from error

    return fingerprint(repo_root, sources)


def write_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check or refresh client skill source fingerprints."
    )
    refresh = parser.add_mutually_exclusive_group()
    refresh.add_argument(
        "--refresh",
        action="append",
        metavar="REFERENCE",
        help="Refresh one reviewed slice or convention leaf; repeat as needed.",
    )
    refresh.add_argument(
        "--refresh-all",
        action="store_true",
        help="Refresh every reviewed slice and convention leaf.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        repo_root = find_repo_root()
        manifest = load_manifest()
        slices: dict[str, Any] = manifest["slices"]
        leaves: dict[str, Any] = manifest["leaves"]

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
                or not all(isinstance(value, str) for value in parents)
            ):
                raise DriftError(
                    f"Convention leaf {name!r} must declare non-empty slice parents"
                )
            if len(parents) != len(set(parents)):
                raise DriftError(
                    f"Convention leaf {name!r} declares duplicate slice parents"
                )
            unknown_parents = set(parents) - set(slices)
            if unknown_parents:
                raise DriftError(
                    f"Convention leaf {name!r} has unknown slice parents: "
                    + ", ".join(sorted(unknown_parents))
                )

        references = {**slices, **leaves}

        requested = set(references) if args.refresh_all else set(args.refresh or [])
        unknown = requested - set(references)
        if unknown:
            raise DriftError(f"Unknown reference(s): {', '.join(sorted(unknown))}")

        drifted: list[tuple[str, str]] = []
        for kind, entries in (
            ("Slice", slices),
            ("Convention leaf", leaves),
        ):
            for name in sorted(entries):
                actual = validate_entry(repo_root, kind, name, entries[name])
                if name in requested:
                    entries[name]["fingerprint"] = actual
                    print(f"refreshed {name}: {actual}")
                elif entries[name]["fingerprint"] != actual:
                    drifted.append((name, actual))

        if requested:
            write_manifest(manifest)

        if drifted:
            print("Client skill references require review:", file=sys.stderr)
            for name, actual in drifted:
                print(f"  {name}: expected current fingerprint {actual}", file=sys.stderr)
            print(
                "Review each affected reference, then run --refresh REFERENCE.",
                file=sys.stderr,
            )
            return 1

        if not requested:
            leaf_label = "convention leaf" if len(leaves) == 1 else "convention leaves"
            print(
                "Client skill source map is current "
                f"({len(slices)} slices, {len(leaves)} {leaf_label})."
            )
        return 0
    except DriftError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
