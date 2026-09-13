# R5.17-B7-A3F2-P7R

## Decision

**BIOME4_RUNTIME_READY_WITH_BUILD_ONLY_COMPATIBILITY_ADJUSTMENT**. The official `jedokaplan/BIOME4` source is pinned locally at `4ad9dff37eed339fce88c0fa5802757f86a3ef44`, distinct from the scientific numerical-core baseline `3c03014223a2dff3deb264e908e3fe44a3232541`. The pinned head changes plotting support only.

The source built reproducibly with WSL2 GCC/GFortran and netCDF-C/Fortran. The only adjustment was command-line linker-order/dependency placement (`make LDFLAGS= LIBS=\"$(nf-config --flibs)\"`); no BIOME4 scientific source was modified. The executable is retained outside the source tree with SHA256 `2d55d3e381cb22ea0b6734cde88e1c97669ffcdc3c3eacb4332cd140dc53b9cd`.

The bundled upstream sample is incompatible with the pinned driver because it lacks the separate `depth`/`dz`/`Ksat` soil schema. A separate `NON_SCIENTIFIC_BIOME4_RUNTIME_SMOKE_FIXTURE` using a 2x2x12 climate grid and six soil layers completed successfully. The output NetCDF is readable and contains finite-or-missing `NPP` values with shape 13x1x1 and units `g m-2`. This is runtime/interface evidence only, not ARCANA NPP or ecological validation.

No ARCANA input, paleo-CO2 authority, soil physical state, Madingley run, resource materialization, or production conversion was performed. Both P7C paleo-CO2 authority binding and P7S physical soil/pedotransfer authority gate remain independently required.
