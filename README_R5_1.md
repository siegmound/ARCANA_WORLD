# ARCANA WorldSim v0.6D1-R5.1 candidate patch

Implements `EMERGENT_HOMINID_CRADLE_AND_ECOLOGICAL_NICHE_DISCOVERY` on top of the authoritative R5.0 SEALED baseline.

Run from project root:

```powershell
.\run_v0_6D1_R5_1.ps1
```

Production execution is strict: exact R5.0 final seal, exact R4.31 J14 seal + J14 NPZ, exact R3.27 macro replay/checkpoint, and exact R3.14 environmental-provider seal are required.

R5.1 performs no new NEMO/Geonomics/Madingley/RangeShifter/CDMetaPOP/SLiM execution. It emits an explicit engine-utility review. RangeShifter is deferred to expansion-corridor work; genomic engines are deferred until persistence/contact/admixture hypotheses exist.

Outputs are candidates only. Do not call R5.1 SEALED before a real local strict run and review of the resulting region registry.

## Post-candidate structure consolidation and external-engine adjudication

This patch extends the same R5.1 stage; it does not create R5.1A/B.

After the cradle-opportunity atlas is generated, R5.1 now:

- reconstructs every connected region exactly from the atlas;
- tracks nested connected-component descendants across the fixed 90/95/97.5/99% threshold family;
- creates threshold-robust region families without a weighted score or single-winner selector;
- measures J14 temporal support of each family's highest-threshold core across the exact 141-age authority;
- measures cross-lineage overlap of all-threshold cores;
- applies a fail-closed external-engine decision gate.

External-engine rule:

- if both human-cohort lineages retain at least one all-threshold family, no new external engine is required for R5.1 closure and RangeShifter remains deferred to R5.2 corridor validation;
- if either lineage lacks such a family, R5.1 must refine the ARCANA-internal spatial method first. RangeShifter is explicitly forbidden as a repair for an internal robustness gap because it may not become ARCANA target authority.

Additional outputs:

- `R5_1_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION.json`
- `R5_1_ROBUST_REGION_FAMILIES.json`
- `R5_1_REGION_FAMILY_TEMPORAL_SUPPORT.npz`
- `R5_1_STRUCTURE_ADJUDICATION_MANIFEST.json`

### Final seal

After the candidate and structure adjudication pass, the runner executes
`scripts/seal_v0_6D1_R5_1.py`. The final seal independently revalidates source and parent
authority, candidate/structure manifests, exact live scientific hashes, engine governance,
and reconstructs the structure outputs from the atlas/J14 authority before sealing.
Expected terminal line: `PASS_R51_INTEGRATED_AND_FINAL_SEAL_RUN`.
