# Handoff v0.6D1-R3.2 → R3.2 Long-Run Closure

1. Run H0 R3.2 from 210→150 Ma locally using `run_v0_6D1_R3_2_windows.ps1 -EndAgeMa 150 -Threads 12`.
2. Audit normalized VA: no value >0.05 and cap-contact fraction must not become a long-horizon attractor.
3. Audit fission count/depth, repeated fission of same parent/root, micro-deme abundance, 16/17 R3.1 near-threshold births, and ordinary extinction.
4. Compare R3.2 against R3.1 but do not require event identity: R3.2 deliberately changes causal transport/contact.
5. Only if the 150 Ma endpoint passes, promote it as canonical H0 continuation checkpoint and proceed 150→90 Ma.
