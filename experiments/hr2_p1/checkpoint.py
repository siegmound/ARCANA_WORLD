"""Prepared full native checkpoint and bounded B0 pair adapter.

This is not the HR1 reference-array checkpoint and not a qualified crash/tail
controller. Original roots are never inputs to this explicit fixture adapter.
"""
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path

from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.identity import BranchId, HistoryId, content_hash, thaw_json
from arcana_worldsim.r6.state import AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport
from arcana_worldsim.r6.store import HistoryStore

from .model import canonical, digest, require, restore_native, source_identity

DOMAIN = "HR2_P1_MANUFACTURED_FULL_NATIVE_RESTART"


def save_exclusive(path, value):
    with Path(path).open("xb") as stream:
        stream.write(canonical(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def save_native(path, case):
    save_exclusive(path, case.checkpoint())


def load_native(path, *, expected_parameters=None, expected_mesh_sha256=None):
    return restore_native(json.loads(Path(path).read_bytes()), expected_parameters, expected_mesh_sha256)


class PairStore:
    """B0 publishes full native state plus a verified diagnostics prefix.

    Journal records hold numerical diagnostics and state digests. They do not
    claim stored full values at every internal substep. Full native values are
    present at every committed checkpoint; a separate archive contract may
    retain annual/substep states. No uncommitted tail is adopted or deleted.
    """

    def __init__(self, root, parameters, mesh_sha256, run_id, *,
                 initial_identity_sha256, reopen=False):
        self.root = Path(root)
        parameters.validate()
        self.parameters, self.mesh_sha256, self.run_id = parameters, mesh_sha256, run_id
        self.source = source_identity()
        self.context = {"run_id": run_id, "parameters": asdict(parameters),
                        "mesh_sha256": mesh_sha256, "source_identity": self.source,
                        "initial_identity_sha256": initial_identity_sha256,
                        "forcing": "DECLARED_MANUFACTURED_FIXED_BEDROCK_CLOSED_NO_SOURCES",
                        "scope": "MANUFACTURED_METHOD_TEST_ONLY"}
        self.history = str(HistoryId.from_payload(self.context))
        self.branch = str(BranchId.from_payload({"history_id": self.history}))
        if reopen:
            require(json.loads((self.root / "CONTEXT.json").read_bytes()) == self.context,
                    "PAIR_CONTEXT_MISMATCH")
        else:
            self.root.mkdir(parents=True, exist_ok=False)
            (self.root / "journal").mkdir()
            save_exclusive(self.root / "CONTEXT.json", self.context)
        self.store = HistoryStore(self.root / "b0")
        self.parent_id = None
        self.prefix_head = None
        self.last_ordinal = -1
        self.last_year = 0.0
        with self.store.read_view() as view:
            self.parent_view = view.view_id
        if reopen:
            self.read_latest()

    def commit(self, case, records, *, expected_parent_view_id=None):
        checkpoint = case.checkpoint()
        restore_native(checkpoint, self.parameters, self.mesh_sha256)
        require(digest(case.initial_identity) == self.context["initial_identity_sha256"],
                "PAIR_INITIAL_CONDITION_IDENTITY_MISMATCH")
        require(records and type(records) is list, "EMPTY_DIAGNOSTIC_PREFIX")
        previous_time = self.last_year
        for offset, record in enumerate(records):
            require(record["ordinal"] == self.last_ordinal + 1 + offset, "PREFIX_ORDINAL_MISMATCH")
            when = record["time_year"]
            require(math.isfinite(when) and previous_time <= when <= case.year,
                    "PREFIX_CLOCK_INVALID")
            previous_time = when
        require(records[-1]["time_year"] == case.year, "PREFIX_NATIVE_CLOCK_MISMATCH")
        prefix = {"schema": DOMAIN, "context_sha256": digest(self.context),
                  "parent_prefix_sha256": self.prefix_head, "records": records}
        prefix_sha = digest(prefix)
        path = self.root / "journal" / (prefix_sha + ".json")
        save_exclusive(path, prefix)
        HistoryStore._fsync_directory(path.parent)
        descriptor = {"schema": DOMAIN, "native_checkpoint": checkpoint,
                      "native_sha256": checkpoint["sha256"], "prefix_sha256": prefix_sha,
                      "parent_prefix_sha256": self.prefix_head, "parent_checkpoint_id": self.parent_id,
                      "first_ordinal": self.last_ordinal + 1,
                      "last_ordinal": records[-1]["ordinal"], "year": case.year,
                      "context_sha256": digest(self.context), "scope": "MANUFACTURED_METHOD_TEST_ONLY"}
        state = DomainStateEnvelope.create(
            history_id=self.history, branch_id=self.branch, domain=DOMAIN,
            time_support=TimeSupport(f"MODEL_YEAR_{case.year}", "MANUFACTURED_MODEL_YEARS"),
            spatial_support=SpatialSupport(self.mesh_sha256, selector_kind="GLOBAL"),
            support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
            value=descriptor)
        cp = CheckpointEnvelope.create(
            history_id=self.history, branch_id=self.branch, time_key=f"MODEL_YEAR_{case.year}",
            restart_state_ids=(str(state.state_id),), retained_history_state_ids=(str(state.state_id),),
            runtime_identity=self.source, configuration=asdict(self.parameters),
            seed_lineage={"family": "EXPLICIT_MANUFACTURED_NO_RANDOM_DRAWS"},
            parent_checkpoint_id=self.parent_id, output_manifest={"descriptor_sha256": content_hash(descriptor)},
            restart_compatibility={"schema": DOMAIN, "full_native_state": True})
        expected = self.parent_view if expected_parent_view_id is None else expected_parent_view_id
        self.store.append_transaction((state, cp), expected_parent_view_id=expected)
        self.parent_id, self.prefix_head = str(cp.checkpoint_id), prefix_sha
        self.last_ordinal, self.last_year = records[-1]["ordinal"], case.year
        with self.store.read_view() as view:
            self.parent_view = view.view_id
        return self.parent_id

    def read_latest(self):
        with self.store.read_view() as view:
            cps = {str(cp.checkpoint_id): cp for cp in self.store.checkpoints()
                   if cp.history_id == self.history and cp.branch_id == self.branch}
            require(cps, "NO_COMMITTED_NATIVE_PAIR")
            leaves = set(cps) - {cp.parent_checkpoint_id for cp in cps.values()}
            require(len(leaves) == 1, "AMBIGUOUS_NATIVE_PAIR_LINEAGE")
            key, chain, seen = next(iter(leaves)), [], set()
            while key is not None:
                require(key in cps and key not in seen, "NATIVE_PAIR_PARENT_MISSING_OR_CYCLIC")
                seen.add(key)
                cp = cps[key]
                chain.append(cp)
                key = cp.parent_checkpoint_id
            require(len(seen) == len(cps), "DISCONNECTED_NATIVE_PAIR_HISTORY")
            ordinal, prefix_head, previous_year, selected = -1, None, 0.0, None
            for cp in reversed(chain):
                require(dict(cp.runtime_identity) == self.source
                        and cp.configuration_sha256 == content_hash(asdict(self.parameters))
                        and len(cp.restart_state_ids) == 1, "PAIR_SOURCE_CONFIG_INVALID")
                envelope = self.store.read_state(cp.restart_state_ids[0])
                d = thaw_json(envelope.value)
                require(envelope.domain == DOMAIN and d["schema"] == DOMAIN
                        and d["parent_checkpoint_id"] == cp.parent_checkpoint_id
                        and d["context_sha256"] == digest(self.context)
                        and thaw_json(cp.output_manifest) == {"descriptor_sha256": content_hash(d)},
                        "PAIR_DESCRIPTOR_INVALID")
                path = self.root / "journal" / (d["prefix_sha256"] + ".json")
                prefix = json.loads(path.read_bytes())
                require(digest(prefix) == d["prefix_sha256"]
                        and prefix["context_sha256"] == digest(self.context)
                        and prefix["parent_prefix_sha256"] == prefix_head == d["parent_prefix_sha256"],
                        "PAIR_JOURNAL_BINDING_INVALID")
                records = prefix["records"]
                require(records and d["first_ordinal"] == ordinal + 1, "PAIR_HIGH_WATER_INVALID")
                for record in records:
                    ordinal += 1
                    require(record["ordinal"] == ordinal and math.isfinite(record["time_year"])
                            and previous_year <= record["time_year"] <= d["year"],
                            "PAIR_PREFIX_ORDER_OR_CLOCK_INVALID")
                    previous_year = record["time_year"]
                require(ordinal == d["last_ordinal"] and previous_year == d["year"],
                        "PAIR_LAST_ORDINAL_OR_CLOCK_INVALID")
                selected = restore_native(d["native_checkpoint"], self.parameters, self.mesh_sha256)
                require(digest(selected.initial_identity) == self.context["initial_identity_sha256"],
                        "PAIR_INITIAL_CONDITION_IDENTITY_MISMATCH")
                require(selected.year == d["year"] and d["native_sha256"] == d["native_checkpoint"]["sha256"],
                        "PAIR_NATIVE_STATE_INVALID")
                prefix_head = d["prefix_sha256"]
            self.parent_view = view.view_id
        self.parent_id = str(chain[0].checkpoint_id)
        self.prefix_head, self.last_ordinal, self.last_year = prefix_head, ordinal, previous_year
        return selected
