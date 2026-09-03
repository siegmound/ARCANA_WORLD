from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Sequence
import csv
import json

import numpy as np
from scipy.optimize import least_squares


@dataclass(frozen=True)
class NemoQTLArchitectureSpec:
    """Engine-neutral additive diploid QTL ensemble used to seed NEMO references.

    The bridge model uses a diallelic additive locus with genotype count g in
    {0,1,2} and locus contribution a*(g-1). For allele frequency p:

        E[A_l]   = a*(2p-1)
        Var[A_l] = 2*a^2*p*(1-p)

    Shared effect sizes are used across patches; patch-specific allele
    frequencies encode genetically inherited mean differences. This is a
    reference mapping only and never changes ARCANA canonical state.
    """

    loci_per_trait: int = 64
    effect_headroom: float = 1.05
    allele_frequency_floor: float = 1.0e-4
    optimizer_tolerance: float = 1.0e-11
    optimizer_max_nfev: int = 20_000
    individual_sample_size: int = 2000

    def __post_init__(self) -> None:
        if self.loci_per_trait < 4:
            raise ValueError("loci_per_trait must be >=4")
        if self.effect_headroom < 1.0:
            raise ValueError("effect_headroom must be >=1")
        if not (0.0 < self.allele_frequency_floor < 0.5):
            raise ValueError("allele_frequency_floor must be between 0 and 0.5")
        if self.individual_sample_size < 20:
            raise ValueError("individual_sample_size must be >=20")


@dataclass(frozen=True)
class NemoQTLRealization:
    seed: int
    trait_axes: tuple[int, ...]
    effect_sizes: np.ndarray                 # trait x locus
    allele_frequencies: np.ndarray           # patch x trait x locus
    target_means: np.ndarray                 # patch x trait
    target_variances: np.ndarray             # patch x trait
    expected_means: np.ndarray               # patch x trait
    expected_variances: np.ndarray           # patch x trait
    sampled_means: np.ndarray                # patch x trait
    sampled_variances: np.ndarray            # patch x trait
    genotype_counts: tuple[np.ndarray, ...]  # each: n_i x trait x locus

    @property
    def semantic_sha256(self) -> str:
        h = sha256()
        h.update(str(int(self.seed)).encode("ascii"))
        h.update(json.dumps(list(self.trait_axes)).encode("ascii"))
        for arr in (
            self.effect_sizes, self.allele_frequencies, self.target_means,
            self.target_variances, self.expected_means, self.expected_variances,
            self.sampled_means, self.sampled_variances,
        ):
            x = np.ascontiguousarray(arr)
            h.update(str(x.dtype).encode("ascii")); h.update(str(x.shape).encode("ascii")); h.update(x.tobytes())
        for arr in self.genotype_counts:
            x = np.ascontiguousarray(arr)
            h.update(str(x.dtype).encode("ascii")); h.update(str(x.shape).encode("ascii")); h.update(x.tobytes())
        return h.hexdigest()


def _moments(effect: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    mean = float(np.sum(effect * (2.0 * p - 1.0)))
    var = float(np.sum(2.0 * effect * effect * p * (1.0 - p)))
    return mean, var


def _fit_patch_frequencies(
    effect: np.ndarray,
    target_mean: float,
    target_var: float,
    floor: float,
    tol: float,
    max_nfev: int,
) -> np.ndarray:
    """Fit a low-dimensional smooth allele-frequency profile to two moments.

    p_l = floor + (1-2*floor)*sigmoid(alpha + beta*s_l), where s_l is a
    symmetric locus coordinate. Two parameters are therefore sufficient to fit
    the target mean and additive variance while avoiding arbitrary per-locus
    overfitting.
    """
    if target_var < 0 or not np.isfinite(target_var):
        raise ValueError("target variance must be finite and non-negative")
    L = effect.size
    s = np.linspace(-1.0, 1.0, L, dtype=float)

    def logistic(x: np.ndarray) -> np.ndarray:
        # stable enough under bounded alpha/beta used below
        return 1.0 / (1.0 + np.exp(-x))

    def p_of(x: np.ndarray) -> np.ndarray:
        raw = logistic(x[0] + x[1] * s)
        return floor + (1.0 - 2.0 * floor) * raw

    mean_capacity = max(float(np.sum(np.abs(effect))), 1e-12)
    var_capacity = max(float(np.sum(0.5 * effect * effect)), 1e-12)

    # Uniform-p initial guess from mean only.
    a_sum = float(np.sum(effect))
    if abs(a_sum) < 1e-15:
        alpha0 = 0.0
    else:
        x = np.clip(target_mean / a_sum, -0.98, 0.98)
        p0 = 0.5 * (1.0 + x)
        raw0 = np.clip((p0 - floor) / (1.0 - 2.0 * floor), 1e-6, 1 - 1e-6)
        alpha0 = float(np.log(raw0 / (1.0 - raw0)))

    def residual(x: np.ndarray) -> np.ndarray:
        p = p_of(x)
        m, v = _moments(effect, p)
        return np.array([
            (m - target_mean) / mean_capacity,
            (v - target_var) / var_capacity,
        ], dtype=float)

    best = None
    # beta controls heterogeneity and lowers variance at a fixed broad mean.
    for beta0 in (0.0, 0.5, 1.5, 3.0, 6.0):
        res = least_squares(
            residual, np.array([alpha0, beta0], dtype=float),
            bounds=(np.array([-12.0, 0.0]), np.array([12.0, 18.0])),
            xtol=tol, ftol=tol, gtol=tol, max_nfev=max_nfev,
        )
        score = float(np.linalg.norm(res.fun))
        if best is None or score < best[0]:
            best = (score, res.x)
    assert best is not None
    p = p_of(best[1])
    m, v = _moments(effect, p)
    mean_err = abs(m - target_mean)
    var_err = abs(v - target_var)
    # Strict enough to ensure the *expected* QTL state faithfully represents
    # ARCANA moments while allowing harmless floating point noise.
    if mean_err > 2e-7 * max(1.0, abs(target_mean), mean_capacity):
        raise ValueError(f"QTL mean mapping did not converge: error={mean_err:g}")
    if var_err > 2e-7 * max(1.0, target_var, var_capacity):
        raise ValueError(f"QTL variance mapping did not converge: error={var_err:g}")
    return p


def _balanced_diploid_genotypes(rng: np.random.Generator, p: np.ndarray, n: int) -> np.ndarray:
    """Generate diploid genotypes while closely matching requested frequencies."""
    L = p.size
    out = np.empty((n, L), dtype=np.uint8)
    for li in range(L):
        alt = int(round(2 * n * float(p[li])))
        chrom = np.zeros(2 * n, dtype=np.uint8)
        chrom[:alt] = 1
        rng.shuffle(chrom)
        out[:, li] = chrom.reshape(n, 2).sum(axis=1)
    return out


def _effect_scale(target_means: np.ndarray, target_vars: np.ndarray, L: int, headroom: float) -> float:
    # For an equal-effect additive architecture, a sufficient condition for a
    # target (m,v) to lie below the maximum-variance envelope is
    # a^2 >= 2v/L + m^2/L^2. Add headroom so beta can lower variance smoothly.
    req = np.max(2.0 * target_vars / L + (target_means * target_means) / (L * L))
    return float(max(np.sqrt(max(req, 1e-18)) * headroom, 1e-9))


def build_qtl_realization(
    target_means: np.ndarray,
    target_variances: np.ndarray,
    *,
    trait_axes: Sequence[int],
    seed: int,
    spec: NemoQTLArchitectureSpec,
    individuals_per_patch: Sequence[int] | None = None,
) -> NemoQTLRealization:
    means = np.asarray(target_means, dtype=float)
    variances = np.asarray(target_variances, dtype=float)
    if means.ndim != 2 or variances.shape != means.shape:
        raise ValueError("target_means and target_variances must have matching patch x trait shape")
    if means.shape[1] != len(tuple(trait_axes)):
        raise ValueError("trait_axes length must equal target trait count")
    if np.any(~np.isfinite(means)) or np.any(~np.isfinite(variances)) or np.any(variances < 0):
        raise ValueError("targets must be finite and variances non-negative")

    nd, nt = means.shape
    L = spec.loci_per_trait
    effects = np.empty((nt, L), dtype=float)
    freqs = np.empty((nd, nt, L), dtype=float)
    exp_mean = np.empty((nd, nt), dtype=float)
    exp_var = np.empty((nd, nt), dtype=float)

    for ti in range(nt):
        a = _effect_scale(means[:, ti], variances[:, ti], L, spec.effect_headroom)
        # Equal positive effects keep the genetic model transparent and make
        # cross-engine reconstruction auditable.
        effects[ti] = a
        for di in range(nd):
            p = _fit_patch_frequencies(
                effects[ti], float(means[di, ti]), float(variances[di, ti]),
                spec.allele_frequency_floor, spec.optimizer_tolerance, spec.optimizer_max_nfev,
            )
            freqs[di, ti] = p
            exp_mean[di, ti], exp_var[di, ti] = _moments(effects[ti], p)

    if individuals_per_patch is None:
        ns = np.full(nd, spec.individual_sample_size, dtype=int)
    else:
        ns = np.asarray(individuals_per_patch, dtype=int)
        if ns.shape != (nd,) or np.any(ns < 20):
            raise ValueError("individuals_per_patch must provide >=20 individuals for each patch")

    rng = np.random.default_rng(int(seed))
    genotypes: list[np.ndarray] = []
    sample_mean = np.empty((nd, nt), dtype=float)
    sample_var = np.empty((nd, nt), dtype=float)
    for di in range(nd):
        patch = np.empty((int(ns[di]), nt, L), dtype=np.uint8)
        breeding = np.empty((int(ns[di]), nt), dtype=float)
        for ti in range(nt):
            g = _balanced_diploid_genotypes(rng, freqs[di, ti], int(ns[di]))
            patch[:, ti, :] = g
            breeding[:, ti] = (g.astype(float) - 1.0) @ effects[ti]
        genotypes.append(patch)
        sample_mean[di] = breeding.mean(axis=0)
        sample_var[di] = breeding.var(axis=0, ddof=0)

    return NemoQTLRealization(
        seed=int(seed), trait_axes=tuple(int(x) for x in trait_axes), effect_sizes=effects,
        allele_frequencies=freqs, target_means=means, target_variances=variances,
        expected_means=exp_mean, expected_variances=exp_var,
        sampled_means=sample_mean, sampled_variances=sample_var,
        genotype_counts=tuple(genotypes),
    )


def write_qtl_realization(realization: NemoQTLRealization, outdir: str | Path, patch_ids: Sequence[str]) -> dict[str, str]:
    root = Path(outdir)
    root.mkdir(parents=True, exist_ok=True)
    if len(patch_ids) != realization.allele_frequencies.shape[0]:
        raise ValueError("patch_ids length mismatch")

    with (root / "qtl_effects.tsv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["trait_local_index", "arcana_trait_axis", "locus", "additive_effect_a"])
        for ti, axis in enumerate(realization.trait_axes):
            for li, effect in enumerate(realization.effect_sizes[ti]):
                w.writerow([ti, axis, li, f"{float(effect):.17g}"])

    with (root / "qtl_patch_allele_frequencies.tsv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["patch_index", "patch_id", "trait_local_index", "arcana_trait_axis", "locus", "allele1_frequency"])
        for di, pid in enumerate(patch_ids):
            for ti, axis in enumerate(realization.trait_axes):
                for li, p in enumerate(realization.allele_frequencies[di, ti]):
                    w.writerow([di, pid, ti, axis, li, f"{float(p):.17g}"])

    with (root / "qtl_moment_audit.tsv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["patch_index", "patch_id", "trait_local_index", "arcana_trait_axis", "target_mean", "expected_mean", "sampled_mean", "target_va", "expected_va", "sampled_va"])
        for di, pid in enumerate(patch_ids):
            for ti, axis in enumerate(realization.trait_axes):
                w.writerow([
                    di, pid, ti, axis,
                    f"{realization.target_means[di,ti]:.17g}", f"{realization.expected_means[di,ti]:.17g}", f"{realization.sampled_means[di,ti]:.17g}",
                    f"{realization.target_variances[di,ti]:.17g}", f"{realization.expected_variances[di,ti]:.17g}", f"{realization.sampled_variances[di,ti]:.17g}",
                ])

    # Genotype realizations are kept as NPZ evidence. They are not silently
    # claimed to be an upstream NEMO import format.
    np.savez_compressed(
        root / "qtl_genotype_realization.npz",
        **{f"patch_{i:04d}": g for i, g in enumerate(realization.genotype_counts)},
    )
    np.savez_compressed(
        root / "qtl_expected_state.npz",
        effect_sizes=realization.effect_sizes,
        allele_frequencies=realization.allele_frequencies,
        target_means=realization.target_means,
        target_variances=realization.target_variances,
        expected_means=realization.expected_means,
        expected_variances=realization.expected_variances,
        sampled_means=realization.sampled_means,
        sampled_variances=realization.sampled_variances,
    )
    manifest = {
        "schema": "ARCANA_NEMO_QTL_ENSEMBLE_REALIZATION_V1",
        "seed": realization.seed,
        "semantic_sha256": realization.semantic_sha256,
        "trait_axes": list(realization.trait_axes),
        "patch_ids": [str(x) for x in patch_ids],
        "model": {
            "ploidy": 2,
            "locus_model": "DIALLELIC_ADDITIVE_REFERENCE",
            "genotype_count": "g_in_{0,1,2}",
            "locus_contribution": "a*(g-1)",
            "expected_mean": "sum_l a_l*(2*p_l-1)",
            "expected_additive_variance": "sum_l 2*a_l^2*p_l*(1-p_l)",
            "nemo_import_semantics": "REQUIRES_VERSION_VALIDATED_NEMO_2_4_2_TEMPLATE_OR_SOURCE_BINDING",
        },
        "authority": {
            "canonical_write_allowed": False,
            "species_identity_authority": False,
            "calibration_status": "REFERENCE_EVIDENCE_ONLY",
        },
    }
    (root / "qtl_ensemble_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "manifest": str(root / "qtl_ensemble_manifest.json"),
        "effects": str(root / "qtl_effects.tsv"),
        "allele_frequencies": str(root / "qtl_patch_allele_frequencies.tsv"),
        "moment_audit": str(root / "qtl_moment_audit.tsv"),
        "genotypes": str(root / "qtl_genotype_realization.npz"),
    }
