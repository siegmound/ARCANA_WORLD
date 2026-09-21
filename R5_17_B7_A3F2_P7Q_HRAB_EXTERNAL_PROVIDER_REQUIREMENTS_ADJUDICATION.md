# R5.17-B7-A3F2-P7Q-HRAB External Provider Requirements

This package defines the scientific acquisition requirements for unresolved temporal parent-material reconstruction. It does not select, download, bind, or execute a provider.

The minimum defensible architecture is domain-specific: Quaternary fluvial/colluvial, coastal/marine event authority, lacustrine deposits, cryosphere/glacial deposits, aeolian deposits, organic/evaporitic formation records, and a targeted tephra/eruption authority for the single pyroclastic cell.

The HRAB clock remains a 280-point execution clock, not a requirement that providers supply 280 native snapshots. Dated intervals and event brackets may constrain HRAB without generating intermediate categorical states. Formation, persistence, removal, and reworking remain separate fields.

`UNKNOWN_MATERIAL` remains `UNKNOWN_PROPAGATION_ONLY` and is excluded from global provider search. No forward evolution is authorized, no provider is selected, and the 0 ka endpoint remains a constraint only.

Decision: `EXTERNAL_PROVIDER_REQUIREMENTS_DEFINED`  
Verdict: `READY_FOR_TARGETED_PROVIDER_RESEARCH`
