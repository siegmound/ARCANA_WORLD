# R3.7H diagnostic smoke audit

## 210→209 three-branch closed loop
- all branches valid: True
- all branches clear of ceiling: True
- peaks: {'K_LOW': 0.02196436286351262, 'K_CENTER': 0.02196436286351262, 'K_HIGH': 0.02196436286351262}

## 210→205 K_CENTER lifecycle smoke
- 40 biology steps
- peak q: 0.027517904071469212
- clipping contacts: 0
- events: {'paleogeographic_support_loss_remap': 24, 'deme_coalescence': 4, 'deme_fission': 18}
- closed-loop gate: True

This smoke exercises actual closed-loop VA feedback plus real fission and coalescence. It is not a substitute for the governed 210→150 LOW/CENTER/HIGH validation.
