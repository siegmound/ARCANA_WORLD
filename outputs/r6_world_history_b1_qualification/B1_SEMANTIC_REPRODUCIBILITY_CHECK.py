"""Recheck cross-root semantic and WHY ordering invariants for B1."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path("tests").resolve()))
from test_r6_world_history_b0_h import _integrated_lifecycle  # noqa: E402
from arcana_worldsim.r6.query import HistoryQueryService  # noqa: E402
from arcana_worldsim.r6.storage import (  # noqa: E402
    AccountingRoot, AccountingScope, StorageCategory, account_storage,
)


def _why_order(result):
    query = HistoryQueryService(result["reopened"])
    why = query.why(str(result["bundle"]["expected"].state_id))
    child_id = str(result["expected_children"][0][0].state_id)
    child_why = query.why(child_id)
    def ids(rows, attr):
        return tuple(str(getattr(row, attr)) for row in rows)
    return {
        "states": ids(why.state_lineage, "state_id"),
        "provenance": ids(why.provenance_records, "record_id"),
        "events": ids(why.events, "record_id"),
        "forcings": ids(why.forcings, "forcing_id"),
        "checkpoints": ids(why.checkpoints, "checkpoint_id"),
        "replay_recipes": ids(why.replay_recipes, "recipe_id"),
        "external_references": why.external_references,
        "unresolved": why.unresolved_references,
        "child_states": ids(child_why.state_lineage, "state_id"),
        "refinement_branches": ids(child_why.refinement_branches, "branch_id"),
        "refinement_recipes": ids(child_why.refinement_recipes, "recipe_id"),
        "child_external_references": child_why.external_references,
        "child_unresolved": child_why.unresolved_references,
    }


def _storage_categories(root):
    categories = tuple(StorageCategory)
    roots = []
    for category in categories:
        path = root / category.value.lower()
        path.mkdir(parents=True)
        (path / "one.bin").write_bytes(b"x")
        roots.append(AccountingRoot(path, category, label=category.value))
    measured = account_storage(AccountingScope(tuple(roots)), hard_cap_bytes=2)
    assert all(measured.categories[c.value].file_count == 1 for c in categories)
    assert measured.canonical_persistent_bytes == 2
    assert measured.within_hard_cap is False  # exact cap is rejected (strict <)
    below = account_storage(AccountingScope(tuple(roots)), hard_cap_bytes=3)
    assert below.within_hard_cap is True


with TemporaryDirectory(prefix="arcana-r6-b1-") as temporary:
    root = Path(temporary)
    first = _integrated_lifecycle(root / "build-a")
    second = _integrated_lifecycle(root / "build-b", reverse=True)
    assert first["final_ids"] == second["final_ids"]
    assert first["main_history"] == second["main_history"]
    assert _why_order(first) == _why_order(second)
    _storage_categories(root / "category-scopes")
    print("B1_TWO_ROOT_SEMANTIC_REBUILD=PASS")
    print("B1_HISTORY_ORDERING=PASS")
    print("B1_WHY_ORDERING=PASS")
    print("B1_REPLAY_REFINEMENT_RETENTION_STORAGE=PASS")
    print("B1_STORAGE_CATEGORY_SEPARATION_AND_STRICT_CAP=PASS")
