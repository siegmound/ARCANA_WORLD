# v0.6D1-R3.3 Status

**Verdict:** `PASS_DEME_RECONNECTION_COALESCENCE_AND_FRAGMENTATION_HOMEOSTASIS_CANDIDATE__LONG_210_TO_150_RERUN_PENDING`

R3.3 closes the missing reverse demographic operator after persistent-vicariance fission. Coalescence is event-driven, same-species-only, persistent for 2 Myr, and uses exact population/first/second moment pooling. Different current species never merge.

Verification:
- new R3.3 tests: 8/8 PASS;
- complete inherited + R3.3 suite: 91/91 PASS;
- formal audit: 50/50 PASS;
- 210→206: 15 fissions, 3 coalescences, 145 components, 0 birth/extinction;
- 210→205: 18 fissions, 4 coalescences, 147 components, 0 birth/extinction;
- hard VA ceiling preserved and no ≥99% cap-contact in both validation windows.

**Not yet authorized:** using the old R3.2 150 Ma state or continuing 150→90 Ma. A fresh R3.3 210→150 run is required.
