# R3.7I Real Promotion Evidence Audit

**Verdict:** PASS — real R3.7H closed-loop evidence reviewed, explicit promotion approved, production seal materialized, and sealed canonical smoke passed.

## R3.7H evidence identity
- Seal source ZIP SHA-256: `0a736ea6b1b35ecd92416c968b34a5830167890ad7bbae6efffc06778fcf2287`
- Uploaded ZIP-container SHA-256: `3d223c68ae86a7e351f07a9b4e878c4509a836edb8188950e605d0be5c3dd2c3`
- The container hashes differ, so byte identity of the ZIP containers is **not** claimed.
- The four scientific JSON payload hashes (`summary`, `K_LOW`, `K_CENTER`, `K_HIGH`) match the hashes recorded in the production seal exactly. Therefore the scientific evidence content is identical to the promoted evidence.

## Promotion review
- Status: `PASS_R37H_FULL_EVIDENCE_REVIEW`
- Checks: **38/38 PASS**
- Promotion eligible: `True`

## Production seal
- Status: `PASS_PRODUCTION_PROMOTION_SEAL`
- Seal SHA-256: `9fd95e1849b7df3d9a5021b457cda723daca760fc782eb0ea2a6199ba70e4c9d`
- Canonical runtime binding authorized: `true`
- Segregation-aware gene-flow variance authorized: `true`
- Segregation-aware coalescence pooling authorized: `true`
- Scalar K as a physical constant: **not authorized**
- Changes to mu/b/ceiling: **not authorized**

## Canonical post-seal smoke
- 210→209 Ma, 8 biology steps
- `canonical_runtime_binding = true`
- peak q = `0.02196436286351262`
- clipping contacts = `0`
- runtime-reported seal hash equals the real seal hash.

## Supersession
The legacy whole-trait gene-flow and coalescence variance operators are retired **only as World-1 production variance authorities**. Other parent authorities remain unchanged.
