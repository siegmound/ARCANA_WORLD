# SI1/BW1 F2B-D1B — Geographic Component-Basis Provenance Audit

**Decision:** `DOF_COMPONENT_BASIS_SOURCE_VERIFIED__F2AV_GEOGRAPHIC_ATTRIBUTION_UNADJUDICATED`

**Mapping statuses:**

- `DOF_MAPPING_PARTIAL` — D1A-attested raw-DOF → reordered node/component slot → original node chain, combined with this source audit, supports the ShellSet component-basis meaning.
- `DOF_MAPPING_UNVERIFIED` — any claim assigning the ten F2A-V asymmetry pairs to geographic positions, named places, plates, or physical causes. This audit does not perform or authorize that attribution.

**Scope:** static source/provenance audit only. No Fair, MPI, Solver, factorization, assembly, gauge, simulation, or canonical-state operation was run.

## 1. Source identity and provenance chain

- Repository branch at audit: `r6/si1-bandwidth-f2av`.
- Repository HEAD at audit: `d539a9ffa281d3dac8489db4820715cb136e9ae6`.
- Historical F2A-V execution/source commit: `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`; it is an ancestor of the audit HEAD. Its direct parent is `6b6ea8418b5044935c2797e69f14624e653e48d5`.
- Historical source paths and Git blob IDs at that commit:
  - `external/ShellSet-v1.1.0/src/MOD_Shells.f90` — `d036e5d2559738a83c0a42d6922bd457551012c8`
  - `external/ShellSet-v1.1.0/src/DMods.f90` — `f2cf93101a385873949295648bdaf16512cb6070`
  - `external/ShellSet-v1.1.0/src/SHELLS_v5.0.f90` — `171a9284e5509da7b5a2db637df4af7fc19d8821`
- The source was read from Git objects at the execution commit, rather than inferred from the current working copy. The run/evidence identity and its preserved blocked status are recorded in the F2A-V source/recovery records and D1A chain. D1A remains the authority for numeric raw-DOF and node/permutation association; this D1B report supplies the missing source semantics for the component basis.
- The prior F2A-V run intentionally stopped before `Solver`; this report makes no claim about a solved velocity field.

## 2. Source findings and evidence

All line numbers below refer to the exact historical commit `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`.

### 2.1 Coordinates and global reference axes

`MOD_Shells.f90:4905–4927` reads FEG longitude and north latitude, sets `theta=(90°−latitude)` in radians as `xNode`, and sets east longitude in radians as `yNode`. It does not normalize the input longitude at this read site. It rejects latitude magnitude above 90.01° and rejects nodes with `abs(latitude)>89.99°` as singular (`4917–4925`).

The independent spherical utility documents `theta` as colatitude from the North Pole and `phi` as east longitude from Greenwich (`DMods.f90:531–545`). Its Cartesian mapping is `r=(sinθ cosφ, sinθ sinφ, cosθ)` and explicitly identifies +X=(0°E,0°N), +Y=(90°E,0°N), +Z=North Pole (`DMods.f90:765–781`). These are source-defined coordinate conventions, not ARCANA-specific geography.

### 2.2 Component basis and orientation

The source explicitly defines `DLocal_Theta` as the local **South-pointing** unit vector and `DLocal_Phi` as local **East-pointing** (`DMods.f90:494–529`). Their Cartesian constructions are, respectively,

`e_theta=(cosθ cosφ, cosθ sinφ, −sinθ)` and `e_phi=(−sinφ, cosφ, 0)`.

The same basis is constructed in the ShellSet runtime path when projecting angular-velocity-derived Cartesian motion: `MOD_Shells.f90:1840–1860` forms `Ω×r`, creates +theta/+phi unit vectors, takes dot products, and stores `vM(1)=vTheta`, `vM(2)=vPhi`. The second related branch repeats the construction at `1995–2019`; the reference-frame subtraction projects through the same vectors at `2028–2065`.

Most decisively for the solved nodal array, the ShellSet node-velocity report labels the east component and north component and assigns `vE=v(2,i)` and `vN=−v(1,i)` (`MOD_Shells.f90:7462–7492`). Therefore the source-supported interpretation is:

| ShellSet nodal slot | Positive direction | Geographic component |
|---|---|---|
| `v(1,node)` / odd raw DOF | increasing `theta` | South; equivalently negative North |
| `v(2,node)` / even raw DOF | increasing `phi` | East |

This conclusion comes from the historical source's comments, basis formulas, velocity projection, and output conversion; it is not an assumed slot convention.

### 2.3 DOF order and continuum/fault assembly

`AddFSt` maps node `nodeI` to `iry=2*nodeI`, `irx=iry−1`, and node `nodeJ` to `jcy=2*nodeJ`, `jcx=jcy−1` (`MOD_Shells.f90:230–253`). Its four 2×2 blocks place element component 1 at the odd DOF and component 2 at the even DOF. The source comment says each node velocity has two components (`57–65`).

The continuum path carries `v(2,mxNode)` and component-paired element arrays (`FEM` declarations at `3630–3671`); `FEM` builds the continuum force and stiffness, adds fault stiffness, applies `VBCs`, then calls `Solver` (`3716–3734`). When transferring a solution, it writes odd equation `2*i−1` to `v(1,i)` and even equation `2*i` to `v(2,i)` (`3743–3764`). These mappings agree with the `AddFSt` odd/even map and the output convention above.

Fault kinematics consume `v(1,*)` and `v(2,*)` through paired coefficient arrays (`MOD_Shells.f90:815–822`); ShellSet comments elsewhere call the two horizontal coordinates `X=+theta=South`, `Y=+phi=East` (`9912–9916`). The source therefore uses the same ordered pair for continuum unknowns and the fault-relative velocity calculations examined here.

### 2.4 Forcing, boundary conditions, and output

- `ReadBC` converts an azimuth clockwise from North into `vBCArg=(180°−azimuth)` radians for conditions 1, 2, and 5 (`MOD_Shells.f90:7187–7218`). `VBCs` forms the vector as `(magnitude*cos(arg), magnitude*sin(arg))` in odd/even component order (`10012–10110`). Combining these statements with `vN=−v1`, `vE=v2` proves the direction convention: azimuth 0° (North) maps to negative slot 1; azimuth 90° (East) maps to positive slot 2. This is a source-level derivation of the boundary-condition transform.
- Plate/angular velocity forcing constructs `Ω×r` in Cartesian and projects it onto the same `e_theta,e_phi` pair before populating slots 1/2 (`1840–1860`, `2028–2065`).
- Node output writes the two raw values in slot order (`7451–7458`) and separately reports their East/North conversion (`7462–7492`).
- The F2A-V case has `nFl=0` and `nCond=0` per its recorded run context, so these fault/BC branches are source-contract findings, not claims that fault forcing or geographic boundary conditions were exercised in that run. Assembly-path linkage is source-level; the diagnostic run stopped before Solver.

### 2.5 Poles and longitude branch

- The FEG reader rejects nodes within 0.01° of either pole (`MOD_Shells.f90:4921–4925`). This avoids the `sin(theta)` denominator used to construct `e_phi` and the meridional basis in several ShellSet routines; e.g. the nodal basal projection constructs and normalizes these vectors at `9753–9783` and uses `e_phi` at `9930–9958`.
- `DLocal_Phi` and `DLocal_Theta` also explicitly fail at the exact poles (`DMods.f90:494–529`). A separate compass helper supplies a conventional frame within 0.05° of a pole (`601–628`), but that helper does not override the FEG reader's narrower node rejection, nor does its existence establish that every mechanics path uses its convention.
- ShellSet's `Chord` helper interpolates angular values through unit-circle vectors and states that it is insensitive to cycle shifts of `2π` (`MOD_Shells.f90:1519–1556`). Coordinate-to-Cartesian formulas are trigonometric and hence periodic in longitude. `DThetaPhi_2_LonLat` canonicalizes output longitude to `(-180°,180°]` (`DMods.f90:750–763`). However, the FEG input path stores longitude directly in radians without an explicit range/canonicalization check (`MOD_Shells.f90:4915–4927`). Thus equivalent ±180° representations have the same mathematical basis, and a cycle-safe angular helper exists; a repository-wide proof that every coordinate-difference/diagnostic path handles the seam identically was not performed.

## 3. Finding-by-finding status

| Question | Finding | Evidence status / limit |
|---|---|---|
| Physical meaning of slots 1/2 | Slot 1 is +South (+theta), slot 2 is +East (+phi); North is `−slot 1`. | **Demonstrated** by historical basis definitions, projected forcing, component-to-geography output conversion, and D1A's odd/even slot mapping. |
| Coordinate frame | Colatitude from North; east longitude from Greenwich; Cartesian axes +X at 0E/0N, +Y at 90E/0N, +Z north. | **Demonstrated** by source comments and equations. A separate ARCANA frame registration is not established by ShellSet alone. |
| Assembly consistency | Odd/even DOF and `v(1:2)` solution transfer match slots 1/2; fault velocity uses the same pair. | **Demonstrated statically** in the inspected path. F2A-V did not execute the mechanics solver. |
| Forcing/BC consistency | Angular velocity uses `Ω×r` projected onto +theta/+phi; BC azimuth is converted to that component pair. | **Demonstrated statically**. This does not establish that F2A-V's ten asymmetries originated in these pathways. |
| Output consistency | Raw pair is output as slot 1 then 2; diagnostic output maps East=`v2`, North=`−v1`. | **Demonstrated**. |
| Poles | Actual mesh nodes within 0.01° of poles are rejected; some independent helpers define a conventional near-pole basis. | **Demonstrated**, with no claim that every non-FEG helper shares one polar policy. |
| ±180° seam | Local tangent formulas are longitude-periodic; a cycle-shift-safe `Chord` and normalized longitude output exist. FEG ingestion itself does not normalize/check longitude range. | **Partially demonstrated**; universal seam behavior across every routine is not established. |
| Ten F2A-V asymmetry pairs | No geography, plate, coordinate, or physical cause assigned here. | `DOF_MAPPING_UNVERIFIED` for anomaly-to-geography/plate/physical interpretation. D1A index mapping plus this basis audit is not an operator/causality adjudication. |

## 4. Interpretation boundary and residual gaps

The historical ShellSet basis is sufficiently explicit to resolve the source-level component semantics. That does **not** prove that ShellSet's reference frame is an ARCANA-authorized geographic/world frame, nor that the two-component local basis is a global Cartesian vector frame. It is a node-local spherical tangent basis whose orientation varies with `(theta,phi)`.

This report does not:

1. map any of the ten asymmetric matrix pairs to a node's original FEG coordinate, plate, or boundary;
2. prove a physical cause for any asymmetry, or establish the operator's expected symmetry;
3. prove a universal longitude-seam policy outside the traced routines;
4. convert ShellSet's Earth-style names (North/East, Greenwich) into ARCANA scientific authority;
5. qualify the F2A-V result. Its historical decision remains `BLOCKED_F2AV_QUALIFICATION`.

If geographic/plate attribution of the census is later proposed, the next required work is a separate, controlled join of the original census DOF indices through the D1A-attested permutation/FEG record identity to coordinates and any independently governed plate frame, followed by an operator-level explanation. Until then retain `DOF_MAPPING_UNVERIFIED` for those relations and do not interpret the ten pairs geographically.

## 5. Audit verdict

**`DOF_COMPONENT_BASIS_SOURCE_VERIFIED__F2AV_GEOGRAPHIC_ATTRIBUTION_UNADJUDICATED`**

Component semantics are source-verifiable for the exact historical ShellSet source used by the F2A-V run: slot 1 is Southward (+colatitude) and slot 2 is Eastward (+longitude); output North is the negative of slot 1. The source basis, assembly ordering, forcing projection, boundary-condition transform, and output mapping agree in the inspected routines. Geographic interpretation of F2A-V anomalies, ARCANA frame authority, complete seam behavior, and any scientific/physical attribution remain outside this finding and unqualified.

**Preserved restrictions:** no Fair/MPI/Solver/factorization/assembly/gauge/simulation; no scientific source or canonical-state changes; `BLOCKED_F2AV_QUALIFICATION` retained; no Solver authorization.
