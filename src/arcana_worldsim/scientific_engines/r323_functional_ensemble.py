from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import math

import numpy as np

STAGE = "v0.6D1-R3.23"
R322_STAGE = "v0.6D1-R3.22"
R322_PASS = "PASS_R322_GENERIC_FUNCTIONAL_PHENOTYPE_SPECIFICATION_TRADEOFF_GOVERNANCE_AND_REPLAY_INTERFACE_SEALED"
EXPECTED_R322_CHECKS = 74
EXPECTED_SPECIES = 134
EXPECTED_COMPONENTS = 295
EXPECTED_HISTORICAL_SPECIES = 348
EXPECTED_HISTORICAL_EVENTS = 2925
R319_JSON_SHA = "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71"
R319_NPZ_SHA = "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406"

TRAITS = [
    "M1_effector_independence", "M2_force_precision_span", "M3_workspace_control", "M4_sensorimotor_feedback",
    "L1_locomotor_mode_breadth", "L2_substrate_breadth", "L3_transition_control", "L4_effector_locomotor_decoupling",
    "C1_working_memory", "C2_inhibitory_control", "C3_relational_integration", "C4_causal_model_depth",
    "P1_acquisition_efficiency", "P2_retention_stability", "P3_cross_context_transfer", "P4_developmental_plasticity",
    "S1_social_tolerance", "S2_coordination_capacity", "S3_social_learning_fidelity", "S4_communication_bandwidth",
    "D1_resource_breadth", "D2_digestive_processing_breadth", "D3_resource_switching",
    "H1_maturation_duration", "H2_reproductive_output_rate", "H3_parental_investment", "H4_adult_survival_horizon",
    "G1_habitat_breadth", "G2_climatic_tolerance_breadth", "G3_disturbance_resilience", "G4_colonization_breadth",
]

DOMAINS = {
    **{x: "manipulative_capability" for x in TRAITS[0:4]},
    **{x: "locomotor_flexibility" for x in TRAITS[4:8]},
    **{x: "cognitive_capacity" for x in TRAITS[8:12]},
    **{x: "learning_plasticity" for x in TRAITS[12:16]},
    **{x: "sociality" for x in TRAITS[16:20]},
    **{x: "dietary_flexibility" for x in TRAITS[20:23]},
    **{x: "life_history" for x in TRAITS[23:27]},
    **{x: "ecological_generalism" for x in TRAITS[27:31]},
}

GUILD_NAMES = {
    1: "small_generalist_herbivore",
    2: "large_browser",
    3: "medium_low_vegetation_feeder",
    4: "small_reptiloid_generalist",
    5: "medium_carnivore",
    6: "apex_carnivore",
}

# Weak ecological descriptors. They are intentionally low-amplitude relative to root uncertainty.
GUILD_DESCRIPTORS = {
    1: {"size": -0.5, "generalist": 0.8, "predation": 0.0, "animal_resource": 0.0},
    2: {"size": 0.9, "generalist": -0.4, "predation": 0.0, "animal_resource": 0.0},
    3: {"size": 0.2, "generalist": 0.1, "predation": 0.0, "animal_resource": 0.0},
    4: {"size": -0.4, "generalist": 0.8, "predation": 0.1, "animal_resource": 0.2},
    5: {"size": 0.2, "generalist": 0.0, "predation": 0.8, "animal_resource": 1.0},
    6: {"size": 0.8, "generalist": -0.2, "predation": 1.0, "animal_resource": 1.0},
}

RATE_REGIMES = {
    "CONSERVATIVE": {"half_life_myr": 30.0, "diffusion_per_sqrt_myr": 0.085},
    "BASELINE": {"half_life_myr": 20.0, "diffusion_per_sqrt_myr": 0.115},
    "LABILE": {"half_life_myr": 12.0, "diffusion_per_sqrt_myr": 0.150},
}

EVIDENCE_SOURCES = {
    "AVONET": {"citation": "Tobias et al. 2022, Ecology Letters 25:581-597", "doi": "10.1111/ele.13898", "scope": "avian morphology/ecology"},
    "ELTONTRAITS": {"citation": "Wilman et al. 2014, Ecology 95:2027", "doi": "10.1890/13-1917.1", "scope": "bird/mammal diet, foraging, activity, body mass"},
    "PANTHERIA": {"citation": "Jones et al. 2009, Ecology 90:2648", "doi": "10.1890/08-1494.1", "scope": "mammal ecology and life history"},
    "AMNIOTE_LIFE_HISTORY": {"citation": "Myhrvold et al. 2015, Ecology 96:3109", "doi": "10.1890/15-0846R.1", "scope": "bird/mammal/reptile life history"},
    "MOUSSEAU_ROFF_1987": {"citation": "Mousseau & Roff 1987, Heredity 59:181-197", "doi": "10.1038/hdy.1987.113", "scope": "1120 heritability estimates across wild outbred animals"},
    "DOCHTERMANN_2019": {"citation": "Dochtermann et al. 2019, Journal of Heredity 110:403-410", "doi": "10.1093/jhered/esz023", "scope": "phylogenetically controlled behavioural heritability meta-analysis"},
    "ATLAS_COMPARATIVE_COGNITION": {"citation": "Atlas of Comparative Cognition", "doi": None, "scope": "systematic comparative cognition evidence coverage"},
    "ANIMAL_CULTURE_DATABASE": {"citation": "Basava & Roman-Palacios 2025, Ecology and Evolution 15:e71913", "doi": "10.1002/ece3.71913", "scope": "socially transmitted animal behaviour"},
}

HERITABILITY_PRIORS = {
    "MORPHOLOGY_LIKE": {"mean_h2": 0.461, "source": "MOUSSEAU_ROFF_1987"},
    "BEHAVIOURAL": {"mean_h2": 0.235, "source": "DOCHTERMANN_2019"},
    "FORAGING": {"mean_h2": 0.196, "source": "DOCHTERMANN_2019"},
    "LIFE_HISTORY": {"mean_h2": 0.262, "source": "MOUSSEAU_ROFF_1987"},
}


class R323GateError(RuntimeError):
    pass


@dataclass(frozen=True)
class R323Config:
    replicates_per_regime: int = 32
    seed: int = 230823
    latent_clip_abs_z: float = 4.0
    root_prior_sd: float = 0.72
    component_local_sd: float = 0.16


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _manifest_close(directory: Path, manifest_name: str) -> None:
    p = directory / manifest_name
    if not p.is_file():
        raise R323GateError(f"Missing manifest: {p}")
    data = load_json(p)
    rows = data.get("files", data)
    if not isinstance(rows, dict) or not rows:
        raise R323GateError(f"Malformed manifest: {p}")
    for name, meta in rows.items():
        if not isinstance(meta, dict):
            continue
        fp = directory / name
        if not fp.is_file():
            raise R323GateError(f"Manifest file missing: {fp}")
        if meta.get("sha256") and sha256_file(fp) != meta["sha256"]:
            raise R323GateError(f"Manifest hash mismatch: {fp.name}")
        if meta.get("bytes") is not None and fp.stat().st_size != int(meta["bytes"]):
            raise R323GateError(f"Manifest size mismatch: {fp.name}")


def validate_inputs(root: Path) -> dict[str, Any]:
    root = Path(root)
    seal_dir = root / "outputs" / "v0_6D1_R3_22_SEAL"
    r322_dir = root / "outputs" / "v0_6D1_R3_22"
    r321_dir = root / "outputs" / "v0_6D1_R3_21"

    audit_p = seal_dir / "R3_22_FINAL_SEAL_AUDIT.json"
    if not audit_p.is_file():
        raise R323GateError(f"Missing R3.22 seal: {audit_p}")
    audit = load_json(audit_p)
    if audit.get("stage") != R322_STAGE or audit.get("status") != R322_PASS or audit.get("verdict") != "SEALED":
        raise R323GateError("R3.22 parent seal mismatch")
    if int(audit.get("checks_passed", -1)) != EXPECTED_R322_CHECKS or int(audit.get("checks_failed", -1)) != 0:
        raise R323GateError("R3.22 parent seal check-count mismatch")

    for d in (r322_dir, r321_dir):
        if not d.is_dir():
            raise R323GateError(f"Required output directory missing: {d}")
    _manifest_close(r322_dir, "R3_22_OUTPUT_MANIFEST.json")
    _manifest_close(r321_dir, "R3_21_OUTPUT_MANIFEST.json")

    comp = load_json(r321_dir / "R3_21_PRESENT_COMPONENT_REGISTRY.json")
    lin = load_json(r321_dir / "R3_21_PRESENT_LINEAGE_REGISTRY.json")
    hist = load_json(r321_dir / "R3_21_HISTORICAL_LINEAGE_CLOSURE.json")
    traits = load_json(r322_dir / "R3_22_PRIMITIVE_TRAIT_CATALOG.json")
    derived = load_json(r322_dir / "R3_22_DERIVED_CAPABILITY_GRAPH.json")

    if len(comp.get("components", [])) != EXPECTED_COMPONENTS:
        raise R323GateError("R3.21 component count mismatch")
    if len(lin.get("lineages", [])) != EXPECTED_SPECIES:
        raise R323GateError("R3.21 present species count mismatch")
    if len(hist.get("historical_species_registry", [])) != EXPECTED_HISTORICAL_SPECIES:
        raise R323GateError("R3.21 historical species count mismatch")
    if len(hist.get("historical_events", [])) != EXPECTED_HISTORICAL_EVENTS:
        raise R323GateError("R3.21 historical event count mismatch")
    if [x.get("trait_id") for x in traits.get("traits", [])] != TRAITS:
        raise R323GateError("R3.22 trait order mismatch")

    source = comp.get("source_checkpoint", {})
    if source.get("json_sha256") != R319_JSON_SHA or source.get("npz_sha256") != R319_NPZ_SHA:
        raise R323GateError("R3.21/R3.19 source provenance mismatch")

    return {
        "seal_audit": audit,
        "r322_dir": r322_dir,
        "r321_dir": r321_dir,
        "components": comp["components"],
        "lineages": lin["lineages"],
        "historical_species": hist["historical_species_registry"],
        "historical_events": hist["historical_events"],
        "r322_traits": traits,
        "r322_derived": derived,
        "source_checkpoint": source,
    }


def trait_calibration_registry() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tid in TRAITS:
        domain = DOMAINS[tid]
        if domain in {"manipulative_capability", "locomotor_flexibility"}:
            hclass = "MORPHOLOGY_LIKE"
            sources = ["AVONET", "ELTONTRAITS", "MOUSSEAU_ROFF_1987"]
            epistemic = "B_COMPARATIVE_PRIOR_PLUS_WEAK_WORLD_PROXY"
        elif domain in {"cognitive_capacity", "learning_plasticity"}:
            hclass = "BEHAVIOURAL"
            sources = ["DOCHTERMANN_2019", "ATLAS_COMPARATIVE_COGNITION"]
            epistemic = "C_COMPARATIVE_PRIOR_HIGH_UNCERTAINTY"
        elif domain == "sociality":
            hclass = "BEHAVIOURAL"
            sources = ["DOCHTERMANN_2019", "ANIMAL_CULTURE_DATABASE", "PANTHERIA"]
            epistemic = "C_COMPARATIVE_PRIOR_HIGH_UNCERTAINTY"
        elif domain == "dietary_flexibility":
            hclass = "FORAGING"
            sources = ["ELTONTRAITS", "PANTHERIA", "DOCHTERMANN_2019"]
            epistemic = "A_COMPARATIVE_PLUS_WORLD_ECOLOGICAL_PROXY"
        elif domain == "life_history":
            hclass = "LIFE_HISTORY"
            sources = ["AMNIOTE_LIFE_HISTORY", "PANTHERIA", "MOUSSEAU_ROFF_1987"]
            epistemic = "A_COMPARATIVE_PLUS_WORLD_DIRECT_PROXY"
        else:
            hclass = "BEHAVIOURAL"
            sources = ["ELTONTRAITS", "PANTHERIA", "AVONET", "DOCHTERMANN_2019"]
            epistemic = "A_COMPARATIVE_PLUS_WORLD_ECOLOGICAL_PROXY"
        rows.append({
            "trait_id": tid,
            "domain": domain,
            "epistemic_class": epistemic,
            "empirical_source_set": sources,
            "observable_to_latent_mapping": "STANDARDIZED_MONOTONE_LATENT_Z_WITH_WEAK_WORLD_PROXY_CONDITIONING",
            "uncertainty_model": "THREE_MACROEVOLUTIONARY_RATE_REGIMES_PLUS_ROOT_AND_COMPONENT_PRIOR_NOISE",
            "heritability_or_va_model": {
                "type": "HERITABILITY_PRIOR_METADATA_ONLY_NOT_COMPONENT_VA",
                "class": hclass,
                "mean_h2_reference": HERITABILITY_PRIORS[hclass]["mean_h2"],
                "source": HERITABILITY_PRIORS[hclass]["source"],
            },
            "cost_model_if_non_negligible": "NOT_USED_AS_DIRECT_FITNESS_TARGET_IN_R3_23;_R3_22_TRADEOFFS_REMAIN_GOVERNING_SEMANTICS",
            "validation_result": "COMPARATIVE_PRIOR_WITH_EXPLICIT_EPISTEMIC_CLASS;_FICTIONAL_LINEAGES_HAVE_NO_DIRECT_OBSERVED_FUNCTIONAL_LABELS",
        })
    return rows


def _guild_target(guild_id: int) -> np.ndarray:
    if guild_id not in GUILD_DESCRIPTORS:
        raise R323GateError(f"Unknown guild_id {guild_id}")
    d = GUILD_DESCRIPTORS[guild_id]
    size, gen, pred, animal = d["size"], d["generalist"], d["predation"], d["animal_resource"]
    z = np.zeros(len(TRAITS), dtype=float)
    ix = {t: i for i, t in enumerate(TRAITS)}
    vals = {
        "M1_effector_independence": 0.12*gen + 0.18*pred - 0.06*size,
        "M2_force_precision_span": 0.10*gen + 0.22*pred,
        "M3_workspace_control": 0.14*gen + 0.14*pred - 0.05*size,
        "M4_sensorimotor_feedback": 0.08*gen + 0.28*pred,
        "L1_locomotor_mode_breadth": 0.34*gen - 0.08*size,
        "L2_substrate_breadth": 0.40*gen - 0.08*size,
        "L3_transition_control": 0.22*gen + 0.18*pred,
        "L4_effector_locomotor_decoupling": 0.10*gen + 0.12*pred,
        "C1_working_memory": 0.06*gen + 0.12*pred,
        "C2_inhibitory_control": 0.05*gen + 0.14*pred,
        "C3_relational_integration": 0.07*gen + 0.12*pred,
        "C4_causal_model_depth": 0.07*gen + 0.13*pred,
        "P1_acquisition_efficiency": 0.08*gen + 0.10*pred,
        "P2_retention_stability": 0.05*gen + 0.08*pred,
        "P3_cross_context_transfer": 0.10*gen + 0.08*pred,
        "P4_developmental_plasticity": 0.12*gen,
        "S1_social_tolerance": 0.02*gen,
        "S2_coordination_capacity": 0.04*gen + 0.10*pred,
        "S3_social_learning_fidelity": 0.04*gen + 0.05*pred,
        "S4_communication_bandwidth": 0.04*gen + 0.04*pred,
        "D1_resource_breadth": 0.52*gen + 0.08*animal,
        "D2_digestive_processing_breadth": 0.36*gen - 0.05*animal,
        "D3_resource_switching": 0.48*gen,
        "H1_maturation_duration": 0.46*size + 0.10*pred,
        "H2_reproductive_output_rate": -0.50*size - 0.08*pred,
        "H3_parental_investment": 0.22*size + 0.05*pred,
        "H4_adult_survival_horizon": 0.42*size + 0.10*pred,
        "G1_habitat_breadth": 0.48*gen - 0.05*size,
        "G2_climatic_tolerance_breadth": 0.28*gen,
        "G3_disturbance_resilience": 0.24*gen + 0.04*size,
        "G4_colonization_breadth": 0.42*gen - 0.08*size,
    }
    for k, v in vals.items():
        z[ix[k]] = v
    return z


def _ou_step(x: np.ndarray, theta: np.ndarray, dt_myr: float, half_life_myr: float, diffusion: float, rng: np.random.Generator) -> np.ndarray:
    if dt_myr <= 0:
        return x.copy()
    k = math.log(2.0) / half_life_myr
    decay = math.exp(-k * dt_myr)
    # Stationary OU innovation scale under dx = k(theta-x)dt + diffusion dW.
    var = (diffusion * diffusion) * (1.0 - math.exp(-2.0 * k * dt_myr)) / (2.0 * k)
    return theta + (x - theta) * decay + math.sqrt(max(var, 0.0)) * rng.normal(size=x.shape)


def _zscore(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, float)
    finite = np.isfinite(v)
    out = np.zeros_like(v, float)
    if finite.sum() < 2:
        return out
    mu = float(v[finite].mean())
    sd = float(v[finite].std())
    if sd <= 1e-12:
        return out
    out[finite] = (v[finite] - mu) / sd
    return np.clip(out, -3.0, 3.0)


def _present_proxy_matrix(components: list[dict[str, Any]], lineages: list[dict[str, Any]], hist_species: list[dict[str, Any]]) -> tuple[np.ndarray, dict[str, Any]]:
    n = len(components)
    species_counts: dict[str, int] = {}
    lineage_depth = {x["species_id"]: int(x.get("lineage_depth", 0)) for x in lineages}
    for c in components:
        species_counts[c["species_id"]] = species_counts.get(c["species_id"], 0) + 1
    cha1 = {x["species_id"]: bool(x.get("cha1_survivor")) for x in hist_species}
    ancestry = {x["species_id"]: x.get("ancestry_chain_root_to_present", []) for x in lineages}

    body = np.array([float(c["legacy_ecological_trait_vector"][2]) for c in components])
    gen = np.log(np.array([max(float(c["generation_time_proxy_years"]), 1e-9) for c in components]))
    rng = np.log1p(np.array([float(c.get("range_grid_summary", {}).get("occupied_grid_cells", 0)) for c in components]))
    compn = np.log1p(np.array([species_counts[c["species_id"]] for c in components], float))
    va_breadth = np.array([float(np.mean(c["additive_variance_vector"][:2])) for c in components])
    depth = np.array([lineage_depth.get(c["species_id"], 0) for c in components], float)
    cha1_surv = np.array([
        1.0 if any(cha1.get(s, False) for s in ancestry.get(c["species_id"], [c["species_id"]])) else 0.0
        for c in components
    ])

    features = {
        "body_z": _zscore(body),
        "generation_time_z": _zscore(gen),
        "range_z": _zscore(rng),
        "component_count_z": _zscore(compn),
        "ecological_va_breadth_z": _zscore(va_breadth),
        "lineage_depth_z": _zscore(depth),
        "cha1_survivor": cha1_surv,
    }
    return np.column_stack(list(features.values())), {"feature_order": list(features), "features": features}


def _proxy_shift(features: dict[str, np.ndarray]) -> np.ndarray:
    n = len(next(iter(features.values())))
    shift = np.zeros((n, len(TRAITS)), dtype=float)
    ix = {t: i for i, t in enumerate(TRAITS)}
    b = features["body_z"]
    g = features["generation_time_z"]
    r = features["range_z"]
    cc = features["component_count_z"]
    vb = features["ecological_va_breadth_z"]
    dep = features["lineage_depth_z"]
    c1 = features["cha1_survivor"] - features["cha1_survivor"].mean()

    for t, w in {
        "H1_maturation_duration": 0.30*g + 0.18*b,
        "H2_reproductive_output_rate": -0.30*g - 0.18*b,
        "H3_parental_investment": 0.16*g + 0.08*b,
        "H4_adult_survival_horizon": 0.26*g + 0.16*b,
        "G1_habitat_breadth": 0.24*r + 0.12*cc,
        "G2_climatic_tolerance_breadth": 0.22*vb,
        "G3_disturbance_resilience": 0.12*dep + 0.12*c1,
        "G4_colonization_breadth": 0.20*r + 0.18*cc,
        "D1_resource_breadth": 0.12*r,
        "D3_resource_switching": 0.10*r,
        "L2_substrate_breadth": 0.08*r,
        "P4_developmental_plasticity": 0.10*g,
    }.items():
        shift[:, ix[t]] += w
    return shift


def _sigmoid(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, -30, 30)
    return 1.0 / (1.0 + np.exp(-x))


def _geomean(a: np.ndarray, axis: int) -> np.ndarray:
    return np.exp(np.mean(np.log(np.clip(a, 1e-9, 1.0)), axis=axis))


def derived_capabilities(ensemble: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ix = {t: i for i, t in enumerate(TRAITS)}
    # Convert latent z to bounded functional availability. Scale 1.5 avoids a hard high/low threshold.
    p = _sigmoid(ensemble / 1.5)
    obj = _sigmoid((0.4*ensemble[:, :, ix["G1_habitat_breadth"]] +
                    0.3*ensemble[:, :, ix["D1_resource_breadth"]] +
                    0.3*ensemble[:, :, ix["L2_substrate_breadth"]]) / 1.5)
    nov = _sigmoid((0.4*ensemble[:, :, ix["G3_disturbance_resilience"]] +
                    0.3*ensemble[:, :, ix["G4_colonization_breadth"]] +
                    0.3*ensemble[:, :, ix["P4_developmental_plasticity"]]) / 1.5)
    tdeps = [
        "M1_effector_independence", "M2_force_precision_span", "M3_workspace_control", "M4_sensorimotor_feedback",
        "C3_relational_integration", "C4_causal_model_depth", "P1_acquisition_efficiency", "P3_cross_context_transfer",
    ]
    qdeps = [
        "C1_working_memory", "C2_inhibitory_control", "C3_relational_integration", "C4_causal_model_depth",
        "P1_acquisition_efficiency", "P2_retention_stability", "P3_cross_context_transfer", "P4_developmental_plasticity",
        "L2_substrate_breadth", "M4_sensorimotor_feedback",
    ]
    t_stack = np.stack([p[:, :, ix[x]] for x in tdeps] + [obj], axis=-1)
    q_stack = np.stack([p[:, :, ix[x]] for x in qdeps] + [nov], axis=-1)
    return _geomean(t_stack, axis=-1), _geomean(q_stack, axis=-1)


def _population_weighted_species_ensemble(ensemble: np.ndarray, components: list[dict[str, Any]], species_order: list[str]) -> np.ndarray:
    """Aggregate component-level ensemble to species using canonical component populations."""
    out = np.zeros((ensemble.shape[0], len(species_order), ensemble.shape[2]), dtype=float)
    by_species: dict[str, list[int]] = {}
    for i, c in enumerate(components):
        by_species.setdefault(str(c["species_id"]), []).append(i)
    for si, sid in enumerate(species_order):
        idx = by_species.get(str(sid), [])
        if not idx:
            raise R323GateError(f"Present species {sid} has no components for population-weighted aggregation")
        w = np.array([float(components[i]["population_total"]) for i in idx], dtype=float)
        if float(w.sum()) <= 0.0:
            w = np.ones_like(w)
        w /= w.sum()
        out[:, si, :] = np.sum(ensemble[:, idx, :] * w[None, :, None], axis=1)
    return out


def simulate_ensemble(inputs: dict[str, Any], cfg: R323Config = R323Config()) -> dict[str, Any]:
    hist = inputs["historical_species"]
    components = inputs["components"]
    lineages = inputs["lineages"]
    by_species = {r["species_id"]: r for r in hist}
    roots = [r for r in hist if r.get("parent_species_id") in (None, "", "None")]
    births = [r for r in hist if r.get("parent_species_id") not in (None, "", "None")]
    births.sort(key=lambda r: float(r.get("birth_age_ma") or 0.0), reverse=True)
    present_species = {x["species_id"] for x in lineages}
    present_index = {sid: i for i, sid in enumerate(sorted(present_species))}
    comp_species = [c["species_id"] for c in components]

    _, proxy_meta = _present_proxy_matrix(components, lineages, hist)
    proxy_shift = _proxy_shift(proxy_meta["features"])

    regimes: list[str] = []
    member_states: list[np.ndarray] = []
    species_member_states: list[np.ndarray] = []
    root_prior_records: list[dict[str, Any]] = []

    for regime_i, (regime, pars) in enumerate(RATE_REGIMES.items()):
        for rep in range(cfg.replicates_per_regime):
            member_seed = cfg.seed + regime_i * 1_000_003 + rep * 10_007
            rng = np.random.default_rng(member_seed)
            state: dict[str, np.ndarray] = {}
            last_age: dict[str, float] = {}
            for r in roots:
                gid = int(r["guild_id"])
                target = _guild_target(gid)
                state[r["species_id"]] = target + cfg.root_prior_sd * rng.normal(size=len(TRAITS))
                last_age[r["species_id"]] = 210.0
                if rep == 0 and regime_i == 0:
                    root_prior_records.append({
                        "species_id": r["species_id"], "guild_id": gid, "guild": GUILD_NAMES.get(gid),
                        "prior_center": target.tolist(), "prior_sd": cfg.root_prior_sd,
                    })

            for child in births:
                sid = child["species_id"]
                parent = str(child["parent_species_id"])
                if parent not in state:
                    raise R323GateError(f"Historical child {sid} missing active parent state {parent}")
                age = float(child.get("birth_age_ma") or 0.0)
                parent_gid = int(by_species[parent]["guild_id"])
                dt = max(last_age[parent] - age, 0.0)
                state[parent] = _ou_step(state[parent], _guild_target(parent_gid), dt, pars["half_life_myr"], pars["diffusion_per_sqrt_myr"], rng)
                last_age[parent] = age
                child_gid = int(child["guild_id"])
                # Child inherits parent at birth; small zero-mean founder perturbation preserves non-teleology.
                state[sid] = state[parent] + 0.06 * rng.normal(size=len(TRAITS))
                # If functional guild differs, the future OU target changes, but the birth state is inherited.
                last_age[sid] = age
                if child_gid not in GUILD_DESCRIPTORS:
                    raise R323GateError(f"Unknown child guild {child_gid}")

            species_state = np.zeros((len(present_index), len(TRAITS)), dtype=float)
            for sid, si in present_index.items():
                if sid not in state:
                    raise R323GateError(f"Present species {sid} missing simulated historical state")
                gid = int(by_species[sid]["guild_id"])
                dt = max(last_age[sid], 0.0)
                x = _ou_step(state[sid], _guild_target(gid), dt, pars["half_life_myr"], pars["diffusion_per_sqrt_myr"], rng)
                species_state[si] = x

            comp_state = np.zeros((len(components), len(TRAITS)), dtype=float)
            for ci, sid in enumerate(comp_species):
                si = present_index[sid]
                comp_state[ci] = species_state[si] + proxy_shift[ci] + cfg.component_local_sd * rng.normal(size=len(TRAITS))
            comp_state = np.clip(comp_state, -cfg.latent_clip_abs_z, cfg.latent_clip_abs_z)
            species_state = np.clip(species_state, -cfg.latent_clip_abs_z, cfg.latent_clip_abs_z)
            regimes.append(regime)
            member_states.append(comp_state)
            species_member_states.append(species_state)

    ensemble = np.stack(member_states, axis=0)
    # Species-level authority is the population-weighted aggregation of the
    # final component-conditioned ensemble, matching R3.22 species-summary semantics.
    species_ensemble = _population_weighted_species_ensemble(ensemble, components, sorted(present_species))
    tcap, qcap = derived_capabilities(ensemble)
    return {
        "ensemble": ensemble,
        "species_ensemble": species_ensemble,
        "tool_use": tcap,
        "problem_solving": qcap,
        "regimes": np.array(regimes, dtype="U16"),
        "root_prior_records": root_prior_records,
        "proxy_meta": {"feature_order": proxy_meta["feature_order"]},
        "present_species_order": sorted(present_species),
        "component_order": [c["component_id"] for c in components],
    }


def _q(x: np.ndarray, qs=(0.05, 0.5, 0.95)) -> list[float]:
    return [float(v) for v in np.quantile(x, qs)]


def build_summary(inputs: dict[str, Any], sim: dict[str, Any], cfg: R323Config) -> dict[str, Any]:
    ensemble = sim["ensemble"]
    tool = sim["tool_use"]
    qcap = sim["problem_solving"]
    comps = inputs["components"]
    lines = inputs["lineages"]
    line_by = {x["species_id"]: x for x in lines}
    component_rows = []
    for i, c in enumerate(comps):
        component_rows.append({
            "component_id": c["component_id"],
            "species_id": c["species_id"],
            "population_total": c["population_total"],
            "trait_mean_z": [float(x) for x in ensemble[:, i, :].mean(axis=0)],
            "trait_sd_z": [float(x) for x in ensemble[:, i, :].std(axis=0)],
            "tool_use_potential": {"mean": float(tool[:, i].mean()), "q05_q50_q95": _q(tool[:, i])},
            "environmental_problem_solving": {"mean": float(qcap[:, i].mean()), "q05_q50_q95": _q(qcap[:, i])},
        })

    species_rows = []
    comp_idx_by_species: dict[str, list[int]] = {}
    for i, c in enumerate(comps):
        comp_idx_by_species.setdefault(c["species_id"], []).append(i)
    for sid in sorted(comp_idx_by_species):
        idx = comp_idx_by_species[sid]
        w = np.array([float(comps[i]["population_total"]) for i in idx], float)
        if w.sum() <= 0:
            w = np.ones_like(w)
        w /= w.sum()
        # Population-weight components within each ensemble member, then summarize across members.
        member_z = np.sum(ensemble[:, idx, :] * w[None, :, None], axis=1)
        member_t = np.sum(tool[:, idx] * w[None, :], axis=1)
        member_q = np.sum(qcap[:, idx] * w[None, :], axis=1)
        species_rows.append({
            "species_id": sid,
            "guild_id": line_by[sid]["guild_id"],
            "component_count": len(idx),
            "population_total": float(sum(comps[i]["population_total"] for i in idx)),
            "trait_mean_z": [float(x) for x in member_z.mean(axis=0)],
            "trait_sd_z": [float(x) for x in member_z.std(axis=0)],
            "tool_use_potential": {"mean": float(member_t.mean()), "q05_q50_q95": _q(member_t)},
            "environmental_problem_solving": {"mean": float(member_q.mean()), "q05_q50_q95": _q(member_q)},
            "human_readiness_score": None,
        })

    return {
        "stage": STAGE,
        "status": "PASS_R323_FUNCTIONAL_ENSEMBLE_REPLAY_CANDIDATE",
        "ensemble": {
            "members": int(ensemble.shape[0]),
            "replicates_per_rate_regime": cfg.replicates_per_regime,
            "rate_regimes": list(RATE_REGIMES),
            "seed": cfg.seed,
            "latent_clip_abs_z": cfg.latent_clip_abs_z,
            "semantics": "EPISTEMIC_AND_MACROEVOLUTIONARY_PRIOR_ENSEMBLE_CONDITIONED_ON_FIXED_H0_HISTORY",
        },
        "traits": trait_calibration_registry(),
        "components": component_rows,
        "species": species_rows,
        "governance": {
            "present_species": len(species_rows),
            "present_components": len(component_rows),
            "historical_species": len(inputs["historical_species"]),
            "historical_events": len(inputs["historical_events"]),
            "deep_biological_coupling": False,
            "human_target": False,
            "human_readiness_ranking_executed": False,
            "h0_mutated": False,
            "cha2_mutated": False,
            "functional_va_materialized": False,
            "functional_gcov_materialized": False,
            "functional_plasticity_beta_materialized": False,
            "macroevolutionary_ensemble_variance_is_not_additive_genetic_variance": True,
            "functional_applicability_code_materialized": False,
            "applicability_semantics": "LATENT_FUNCTIONAL_POTENTIAL_CONDITIONAL_ON_GENERIC_D1_MACROFAUNAL_SCOPE;_NO_RETROACTIVE_ANATOMICAL_INNOVATION_CLAIM",
            "derived_capability_semantics": "CONDITIONAL_POTENTIAL_NOT_REALIZED_TOOL_BEHAVIOR_OR_HUMAN_READINESS",
            "source_checkpoint": inputs["source_checkpoint"],
        },
    }


def audit_result(inputs: dict[str, Any], sim: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    def ck(name: str, cond: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(cond), "detail": detail})

    e = sim["ensemble"]
    t = sim["tool_use"]
    q = sim["problem_solving"]
    ck("parent_r322_sealed_74", inputs["seal_audit"].get("checks_passed") == 74)
    ck("trait_count_exact_31", e.shape[2] == 31)
    ck("component_count_exact_295", e.shape[1] == 295)
    ck("ensemble_member_count_expected", e.shape[0] == 3 * summary["ensemble"]["replicates_per_rate_regime"], e.shape)
    ck("historical_species_exact_348", len(inputs["historical_species"]) == 348)
    ck("historical_events_exact_2925", len(inputs["historical_events"]) == 2925)
    ck("all_latent_finite", np.isfinite(e).all())
    ck("latent_bounds_respected", float(np.max(np.abs(e))) <= summary["ensemble"]["latent_clip_abs_z"] + 1e-12)
    ck("derived_tool_finite_bounded", np.isfinite(t).all() and np.all((t >= 0) & (t <= 1)))
    ck("derived_problem_finite_bounded", np.isfinite(q).all() and np.all((q >= 0) & (q <= 1)))
    ck("three_rate_regimes_present", sorted(set(sim["regimes"].tolist())) == sorted(RATE_REGIMES))
    regime_means = {r: float(e[sim["regimes"] == r].std()) for r in RATE_REGIMES}
    ck("rate_regimes_not_identical", len({round(x, 10) for x in regime_means.values()}) > 1, regime_means)
    ck("component_ids_unique", len(set(sim["component_order"])) == 295)
    recomputed_species = _population_weighted_species_ensemble(e, inputs["components"], sim["present_species_order"])
    ck("species_ensemble_population_weighted_exact", np.allclose(sim["species_ensemble"], recomputed_species, rtol=0.0, atol=1e-12))
    ck("present_species_order_exact_134", len(sim["present_species_order"]) == 134)
    ck("all_species_have_human_readiness_null", all(x.get("human_readiness_score") is None for x in summary["species"]))
    ck("no_human_target", summary["governance"]["human_target"] is False)
    ck("deep_off", summary["governance"]["deep_biological_coupling"] is False)
    ck("h0_not_mutated", summary["governance"]["h0_mutated"] is False)
    ck("cha2_not_mutated", summary["governance"]["cha2_mutated"] is False)
    ck("va_not_materialized", summary["governance"]["functional_va_materialized"] is False)
    ck("gcov_not_materialized", summary["governance"]["functional_gcov_materialized"] is False)
    ck("plasticity_not_materialized", summary["governance"]["functional_plasticity_beta_materialized"] is False)
    ck("ensemble_variance_not_called_va", summary["governance"]["macroevolutionary_ensemble_variance_is_not_additive_genetic_variance"] is True)
    ck("applicability_not_falsely_materialized", summary["governance"]["functional_applicability_code_materialized"] is False)
    ck("derived_capability_semantics_conditional", summary["governance"]["derived_capability_semantics"].startswith("CONDITIONAL_POTENTIAL"))
    ck("calibration_rows_exact_31", len(summary["traits"]) == 31)
    ck("calibration_trait_order_exact", [x["trait_id"] for x in summary["traits"]] == TRAITS)
    ck("each_trait_has_multiple_evidence_sources", all(len(x["empirical_source_set"]) >= 2 for x in summary["traits"]))
    ck("epistemic_classes_explicit", all(x.get("epistemic_class") for x in summary["traits"]))
    ck("source_checkpoint_exact", summary["governance"]["source_checkpoint"] == {"json_sha256": R319_JSON_SHA, "npz_sha256": R319_NPZ_SHA})
    ck("species_summary_count_exact", len(summary["species"]) == 134)
    ck("component_summary_count_exact", len(summary["components"]) == 295)
    ck("species_population_closure", math.isclose(sum(x["population_total"] for x in summary["species"]), 1217.2506240828814, rel_tol=0, abs_tol=2e-9))
    ck("component_population_closure", math.isclose(sum(x["population_total"] for x in summary["components"]), 1217.2506240828814, rel_tol=0, abs_tol=2e-9))
    # No named lineage appears in calibration mechanics/source registry.
    mechanics_text = json.dumps({"guild_descriptors": GUILD_DESCRIPTORS, "sources": EVIDENCE_SOURCES, "h2": HERITABILITY_PRIORS})
    ck("no_named_lineage_in_calibration_mechanics", not any(prefix in mechanics_text for prefix in ("HSG_", "BRW_", "LVF_", "RPT_", "CAR_", "APX_")))

    failed = [x for x in checks if not x["pass"]]
    return {
        "stage": STAGE,
        "audit": "INTEGRATED_R323_COMPARATIVE_PRIOR_ENSEMBLE_REPLAY_CLOSURE",
        "status": "PASS_R323_FUNCTIONAL_ENSEMBLE_REPLAY_CANDIDATE" if not failed else "FAIL_R323_INTEGRATED_AUDIT",
        "checks_passed": len(checks) - len(failed),
        "checks_total": len(checks),
        "checks_failed": len(failed),
        "checks": checks,
    }
