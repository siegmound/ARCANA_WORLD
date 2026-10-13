# INT-1D provider preflight blocked

Date: 2026-10-13
Repository: `siegmound/ARCANA_WORLD`
Branch: `r6/si1-bandwidth-f2av`
Source commit: `ffeb02e90abc4c3a542ac9a794c57ee8496b211b`

## Outcome

Decision: `INT1D_BLOCKED_PROVIDER_PREFLIGHT_EXTERNAL_INPUTS_UNAVAILABLE`.

The authorized INT-1D candidate requested boundary `R6BND-T0-27e4d497530e681071fb`, ordered pair 5:11. The final-commit provider audit was attempted using the current Python 3.12.14 / NumPy 2.3.5 environment. `ARCANA_EXTERNAL_ROOT` was not configured, and the audit stopped with the exact error:

`KinematicsAuthorityError: governed payload unavailable: CANONICAL_T0_PHYSICAL_PAYLOAD`

Provider/source-composite verification therefore did not complete. The governed input hashes, support identities, material classes, complete profiles and edge forcing were not re-attested for this source commit; boundary eligibility was not re-established by the required current provider audit. No fixture or substitute input was used.

## Execution and evidence boundary

- No numerical evolution was executed; the one-run authorization was not consumed by a numerical run.
- No INT-1D candidate output directory or supervisor evidence directory was created.
- Existing INT-0B R4 evidence was preserved unchanged.
- No new numerical evidence, source-composite identity, or retention result is claimed.
- Existing scientific and canonical gates remain unchanged, including the prohibition on Solver/mechanics qualification and canonical `WORLD_HISTORY` production.

The next action is governed-input location verification on Windows. Only if the authorized payload is located and the complete final-source provider preflight passes may the operator reassess the still-conditional INT-1D execution authorization. This report records a blocked preflight, not an experiment failure.
