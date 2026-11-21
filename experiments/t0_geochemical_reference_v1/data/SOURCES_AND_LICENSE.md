# Noncanonical Earth geochemical reference data

This folder contains **unaltered copies of three source tables** from the MIT-licensed `abuseki/georefdatar` repository, pinned to Git commit `e82b70de1b65d8e9cde52166b93ebc88a50934b2`. Original provenance, individual table Git blob SHA, publication DOI, and the MIT license follow.

| Local file | Original source path | Upstream Git blob SHA | Scientific reference |
|---|---|---|---|
| `CC__Rudnick_Gao__2014.csv` | `data-raw/CC__Rudnick_Gao__2014.csv` | `4127120d7499e3d9b62a22384465c39b8806aaf0` | Rudnick & Gao (2014), DOI 10.1016/B978-0-08-095975-7.00301-6 |
| `DM__Salters_Stracke__2004.csv` | `data-raw/DM__Salters_Stracke__2004.csv` | `262447b687f5cae36fde836ffd12c7d439a9f16b` | Salters & Stracke (2004), DOI 10.1029/2003GC000597 |
| `Sun_McDonough__1989.csv` | `data-raw/Sun_McDonough__1989.csv` | `10e8fce96afa6ddd2b50f0f8a43d783f60d5c34c` | Sun & McDonough (1989), DOI 10.1144/GSL.SP.1989.042.01.19 |

Upstream: https://github.com/abuseki/georefdatar/tree/e82b70de1b65d8e9cde52166b93ebc88a50934b2/data-raw

**Scope:** Earth reference values only. The continental table supplies upper/middle/lower/bulk *Earth continental crust* mean oxides and trace elements. This does not establish ARCANA upper/lower crust layering. The Sun & McDonough table contributes *N-type MORB melt trace elements only*: no bulk-oceanic-crust composition, and no unit is supplied in this particular CSV, so the code does not apply a guessed ppm/ppb conversion. The depleted mantle table is an **Earth mantle reservoir model**, not an observation or a 210 Ma ARCANA mantle sample. Its H₂O figure is a model abundance (ppm), **not a source ARCANA pore-pressure, water fugacity, or hydrated fault gouge**. Do not infer mineral phase fraction, oxide valence (FeO* denotes total iron expressed as FeO), ore deposit concentration, Deep accessibility, geothermal rock rheology, or ARCANA T0 composition from this data alone.

The compiler only reads these tables for library-level comparisons, checks original Git object SHAs and units, and emits an explicit unassigned/noncanonical research report. No code path writes WorldHistory, canonical state or new per-cell mineralogy.

## Reproduced upstream license

# MIT License

Copyright (c) 2022 georefdatar authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

