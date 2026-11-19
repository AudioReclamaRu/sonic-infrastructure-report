from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.validate_evidence_id_registry import validate_registry


class EvidenceIdRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "evidence").mkdir()
        self.registry = self.root / "evidence" / "ID_REGISTRY.csv"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_card(self, evidence_id: str) -> str:
        path = f"evidence/{evidence_id}.md"
        (self.root / path).write_text(
            f"---\nid: {evidence_id}\ntype: evidence\n---\n\nEvidence body.\n",
            encoding="utf-8",
        )
        return path

    def write_registry(self, rows: list[dict[str, str]]) -> None:
        fields = ("evidence_id", "path", "allocated_branch", "notes")
        with self.registry.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def row(self, evidence_id: str, owner: str = "main") -> dict[str, str]:
        return {
            "evidence_id": evidence_id,
            "path": f"evidence/{evidence_id}.md",
            "allocated_branch": owner,
            "notes": "test allocation",
        }

    def test_existing_main_card_passes(self) -> None:
        evidence_id = "E-2026-011"
        self.write_card(evidence_id)
        self.write_registry([self.row(evidence_id)])
        self.assertEqual(validate_registry(self.root), [])

    def test_reserved_pr_card_passes_for_allocating_branch(self) -> None:
        evidence_id = "E-2026-107"
        path = self.write_card(evidence_id)
        self.write_registry([self.row(evidence_id, "fix/evidence-id-registry-20261119")])
        self.assertEqual(
            validate_registry(
                self.root,
                branch_name="fix/evidence-id-registry-20261119",
                added_paths=[path],
            ),
            [],
        )

    def test_frontmatter_with_utf8_bom_passes(self) -> None:
        evidence_id = "E-2026-017"
        path = f"evidence/{evidence_id}.md"
        (self.root / path).write_text(
            "\ufeff---\\nid: E-2026-017\\ntype: evidence\\n---\\n",
            encoding="utf-8",
        )
        self.write_registry([self.row(evidence_id)])
        self.assertEqual(validate_registry(self.root), [])

    def test_duplicate_registry_ids_fail(self) -> None:
        evidence_id = "E-2026-011"
        self.write_card(evidence_id)
        self.write_registry([self.row(evidence_id), self.row(evidence_id, "another-branch")])
        errors = validate_registry(self.root)
        self.assertTrue(any("duplicate registry ID" in error for error in errors))

    def test_unregistered_evidence_file_fails(self) -> None:
        self.write_card("E-2026-012")
        self.write_registry([self.row("E-2026-011")])
        errors = validate_registry(self.root)
        self.assertTrue(any("not allocated" in error for error in errors))

    def test_filename_frontmatter_mismatch_fails(self) -> None:
        path = self.write_card("E-2026-013")
        (self.root / path).write_text(
            "---\nid: E-2026-014\ntype: evidence\n---\n",
            encoding="utf-8",
        )
        self.write_registry([self.row("E-2026-013")])
        errors = validate_registry(self.root)
        self.assertTrue(any("does not match filename" in error for error in errors))

    def test_main_allocation_requires_file(self) -> None:
        self.write_registry([self.row("E-2026-014")])
        errors = validate_registry(self.root)
        self.assertTrue(any("main allocation has no evidence file" in error for error in errors))

    def test_wrong_branch_cannot_use_reserved_id(self) -> None:
        evidence_id = "E-2026-015"
        path = self.write_card(evidence_id)
        self.write_registry([self.row(evidence_id, "branch-a")])
        errors = validate_registry(
            self.root,
            branch_name="branch-b",
            added_paths=[path],
        )
        self.assertTrue(any("not current branch" in error for error in errors))

    def test_new_file_requires_reservation(self) -> None:
        evidence_id = "E-2026-016"
        path = self.write_card(evidence_id)
        self.write_registry([])
        errors = validate_registry(
            self.root,
            branch_name="branch-a",
            added_paths=[path],
        )
        self.assertTrue(any("not reserved" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
