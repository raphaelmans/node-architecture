"""Behavioral tests for slice/leaf drift and selective refresh in isolated fixtures."""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "server_source_drift", Path(__file__).with_name("check-source-drift.py")
)
assert SPEC is not None and SPEC.loader is not None
drift = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(drift)


class SourceDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="server-leaf-drift-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / ".git").mkdir()
        self.write("server/README.md", "# Shared canonical guide\n")
        self.write("server/core/access.md", "# Leaf canonical guide\n")
        self.manifest_path = self.root / "server/skill-maintenance/source-map.json"
        self.manifest = {
            "version": 2,
            "sourceRoot": "../..",
            "hashAlgorithm": drift.HASH_ALGORITHM,
            "slices": {
                name: self.entry(name, ["server/README.md"])
                for name in sorted(drift.EXPECTED_SLICES)
            },
            "leaves": {
                "security/access": {
                    **self.entry("security/access", ["server/core/access.md"]),
                    "parents": ["security"],
                }
            },
        }
        self.save()

    def write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def entry(self, name: str, sources: list[str]) -> dict:
        reference = f"server/skill/references/{name}.md"
        self.write(reference, f"# Curated {name}\n")
        return {
            "reference": reference,
            "sources": sources,
            "fingerprint": drift.source_fingerprint(self.root, sources),
        }

    def save(self) -> None:
        self.write(
            "server/skill-maintenance/source-map.json",
            json.dumps(self.manifest, indent=2) + "\n",
        )

    def run_check(self, *arguments: str) -> tuple[int, str]:
        output = io.StringIO()
        with (
            patch.object(drift, "MANIFEST_PATH", self.manifest_path),
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(output),
        ):
            status = drift.main(["--repo-root", str(self.root), *arguments])
        return status, output.getvalue()

    def test_current_slices_and_leaf_pass(self) -> None:
        self.assertEqual(self.run_check()[0], 0)

    def test_leaf_source_change_is_detected_without_changing_manifest(self) -> None:
        before = self.manifest_path.read_bytes()
        self.write("server/core/access.md", "# Changed access policy\n")
        status, output = self.run_check()
        self.assertEqual(status, 1)
        self.assertIn("security/access:", output)
        self.assertEqual(self.manifest_path.read_bytes(), before)

    def test_selective_refresh_preserves_slices_and_reports_other_drift(self) -> None:
        original_slices = copy.deepcopy(self.manifest["slices"])
        self.write("server/core/access.md", "# Reviewed leaf change\n")
        self.write("server/README.md", "# Unreviewed shared change\n")
        self.assertEqual(self.run_check("refresh", "security/access")[0], 1)
        updated = json.loads(self.manifest_path.read_text())
        self.assertEqual(updated["slices"], original_slices)
        self.assertEqual(
            updated["leaves"]["security/access"]["fingerprint"],
            drift.source_fingerprint(self.root, ["server/core/access.md"]),
        )
        self.assertEqual(
            self.run_check("refresh", *sorted(drift.EXPECTED_SLICES))[0], 0
        )
        self.assertEqual(self.run_check()[0], 0)

    def test_invalid_parents_are_rejected_before_refresh(self) -> None:
        for parents in ([], ["missing"], ["security", "security"], "security", [1]):
            with self.subTest(parents=parents):
                self.manifest["leaves"]["security/access"]["parents"] = parents
                self.save()
                before = self.manifest_path.read_bytes()
                self.assertEqual(self.run_check("refresh", "security/access")[0], 2)
                self.assertEqual(self.manifest_path.read_bytes(), before)

    def test_duplicate_slice_and_leaf_name_is_rejected(self) -> None:
        self.manifest["leaves"]["security"] = self.manifest["leaves"].pop("security/access")
        self.save()
        self.assertEqual(self.run_check()[0], 2)

    def test_unmapped_canonical_guide_is_rejected(self) -> None:
        self.write("server/core/unmapped.md", "# New policy\n")
        self.assertEqual(self.run_check()[0], 2)

    def test_missing_source_or_reference_is_rejected(self) -> None:
        entry = self.manifest["leaves"]["security/access"]
        for key, missing in (
            ("sources", ["server/core/missing.md"]),
            ("reference", "server/skill/references/missing.md"),
        ):
            with self.subTest(key=key):
                original = entry[key]
                entry[key] = missing
                self.save()
                self.assertEqual(self.run_check()[0], 2)
                entry[key] = original

    def test_unknown_refresh_target_does_not_write(self) -> None:
        before = self.manifest_path.read_bytes()
        self.assertEqual(self.run_check("refresh", "not-a-reference")[0], 2)
        self.assertEqual(self.manifest_path.read_bytes(), before)

    def test_reference_cannot_escape_skill_reference_directory(self) -> None:
        self.manifest["leaves"]["security/access"]["reference"] = (
            "server/skill/references/../../README.md"
        )
        self.save()
        self.assertEqual(self.run_check()[0], 2)


if __name__ == "__main__":
    unittest.main()
