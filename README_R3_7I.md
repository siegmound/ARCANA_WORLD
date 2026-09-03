# ARCANA World 1 — v0.6D1-R3.7I SEALED

Production Promotion Seal & Canonical Segregation-Aware Runtime.

R3.7I is now sealed from real R3.7H three-branch 210→150 closed-loop evidence. The canonical runtime is enabled only by the embedded promotion seal.

## Canonical runtime
```powershell
.\run_v0_6D1_R3_7I_canonical_runtime.ps1 -DiagnosticSmoke -EndAgeMa 209
```

The production binding uses `K_CENTER=38.470` only as the nominal reduced-order coordinate reference. `K_LOW=37.614` and `K_HIGH=41.002` remain mandatory release-validation sentinels. No scalar physical-K constant has been promoted.

## Evidence
- Real promotion review: 38/38 PASS.
- Production seal SHA-256: `9fd95e1849b7df3d9a5021b457cda723daca760fc782eb0ea2a6199ba70e4c9d`.
- Sealed formal audit: 32/32 PASS.
- Canonical post-seal smoke: 8/8 steps, zero clipping.

Use `R3_7I_REAL_PROMOTION_EVIDENCE_AUDIT.md` for exact provenance, including the distinction between the sealed source ZIP container hash and the later uploaded/repacked evidence ZIP hash.
