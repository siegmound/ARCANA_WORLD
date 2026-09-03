# R3.18 Transport-Phase Operator Audit

The R3.17 audit showed that a 5-kyr partial biology step would violate the established operator cadence. R3.18 extends that reasoning to the final 125-kyr macrostep.

R3.8 performs migration twice per biology step (`125 kyr / 62.5 kyr = 2`) but both substeps currently receive the same environment object. In the recent 120 ka -> 0 interval this cannot be assumed adequate without evidence because shoreline, climate and forage vary on a much finer SEALED clock.

R3.18 therefore:

1. completes the exact recent environmental exposure integral;
2. inserts 62.5 ka as the exact transport coupling boundary;
3. materializes independent effective forcing for 125->62.5 and 62.5->0;
4. records support loss/gain and parent population mass exposed to endpoint support changes;
5. leaves all biological and transport operators frozen;
6. fails closed on production biology closure until a phase-aware operator passes constant-forcing equivalence in R3.19.

No scientific parameter is changed by this audit.
