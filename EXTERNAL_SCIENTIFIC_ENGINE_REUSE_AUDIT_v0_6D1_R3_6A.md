# External Scientific Engine Reuse Audit — v0.6D1-R3.6A

Verified 2026-08-28.

## Selected engines

### NEMO 2.4.2
Primary R3.6 quantitative-genetics oracle. Current upstream states that NEMO is forward-time, individual-based and genetically explicit, supports quantitative traits/QTL, custom dispersal matrices, spatial/temporal selection, patch fusion/fission and batch/MPI workflows. Version 2.4.2 was released 2026-08-03 and fixes a free-recombination bug affecting the `quant` architecture in 2.4.0/2.4.1. R3.6 therefore pins 2.4.2.

Upstream: `https://nemo2.sourceforge.io/`

### Geonomics 1.4.9
Selected as a later regional individual/genomic spatial backend candidate. Current PyPI release is 1.4.9 (2025-12-15), MIT licensed.

Upstream: `https://pypi.org/project/geonomics/`

### Madingley / MadingleyR
Selected as ecosystem/trophic-opportunity provider candidate. Exact executable/package version must be pinned in the evidence bundle before any production integration. It remains separated from ARCANA species authority.

Upstream: `https://madingleyr.github.io/MadingleyR/`

### CDMetaPOP 3.08
Selected as secondary multispecies/demogenetic oracle. Upstream README identifies version 3.08, release date 2025-09-18, Python 3.8, with 2- and 3-species competition examples. Isolated environment/subprocess integration is therefore preferred.

Upstream: `https://github.com/ComputationalEcologyLab/CDMetaPOP`

### RangeShifter 3.0
Selected as specialist dispersal/range-dynamics reference/backend candidate. Version 3.0 was released in 2026 and provides batch and R interfaces plus an expanded genetics module and parallel reproduction/dispersal option. It remains secondary for the global multispecies World 1 replay.

Upstream: `https://rangeshifter.github.io/software/rangeshifter/`

## Reuse decision

No engine replaces ARCANA WorldSim. The selected architecture is an orchestrator plus governed adapters. This maximizes reuse while preserving ARCANA-specific clocking, paleogeography, CHA events, Deep coupling, species identity, speciation authority, provenance, reproducibility and canon governance.
