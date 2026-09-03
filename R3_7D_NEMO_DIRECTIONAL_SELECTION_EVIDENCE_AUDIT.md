# R3.7D NEMO Directional-Selection Evidence Audit

The repaired R3.7C-R1 full oracle completed 16/16 chains with 16/16 efficacy PASS.

R3.7D corrects the participation inference by using the selected-minus-neutral **allele-frequency displacement before squaring**, rather than subtracting two already-squared segregation-potential states.

Key observations from the 16-chain evidence:
- aggregate parent diagnostic K: ~35.87–69.88; values >64 expose the nonlinear subtraction problem;
- geometric matched K across all chains: ~11.92–41.00;
- N=500: median ~15.22, high stochastic spread;
- N=2000: median ~38.47, range ~37.61–41.00, CV ~2.85%;
- paired N=2000 minus N=500 effect: mean ~+21.61, exact two-sided sign-flip p=0.0078125;
- selection-variance 4 minus 1 effect: mean ~-0.71, p=0.6875;
- geometric adaptive-S retention after reconnection: median ~4.19%, range ~2.12–9.16%.

Interpretation: dynamic selection participation is process/state dependent and finite-N sensitive. The large-N oracle is stable enough for a shadow sensitivity envelope but not for a production scalar. No WorldSim population-size mapping is inferred.
