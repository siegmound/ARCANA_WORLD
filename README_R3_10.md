# ARCANA WorldSim v0.6D1-R3.10

R3.10 crosses CHA-1 with the dedicated high-resolution event provider. It must
not be replaced by a normal 125 kyr biology step.

Run:

```powershell
.\run_v0_6D1_R3_10_cha1_highres_bridge.ps1
```

Expected canonical deterministic result:

```text
305 pre-impact species
212 direct CHA-1 extinctions
93 survivors
207 surviving components
65.5 Ma POST_CHA1_500KY restart checkpoint
```

The historical D2.2 31-survivor identity set is never used as a lookup. R3.10
reuses D2.2 event semantics and recovered quantitative evidence on the rebased
R3.9 state.

## Release state

**SEALED.** The canonical restart authority is `65.5 Ma POST_CHA1_500KY`. See `R3_10_FULL_CHA1_EVIDENCE_AUDIT.md` and `SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_10.json`.
