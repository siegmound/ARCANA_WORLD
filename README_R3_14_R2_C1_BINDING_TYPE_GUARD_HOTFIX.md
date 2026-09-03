# R3.14-R2 — C1 Binding Type-Guard Hotfix

This overlay formalizes the stale-class-reference repair discovered during the Windows R3.14 binding run.

## Root cause
`validate_30ma_binding()` referenced `ip.IntegratedLateCenozoicProviderC1`, but `IntegratedLateCenozoicProviderC1` is defined in `late_cenozoic/cha2_nested_50y.py` and imported directly by the R3.14 binding module. `integrated_provider.py` exposes `IntegratedLateCenozoicProvider`, not the C1 wrapper.

## R2 strengthening
Instead of merely referencing the correct class object, R2 validates the actual bound stack:

```python
if not isinstance(provider.parent, IntegratedLateCenozoicProviderC1):
    raise TypeError(...)
```

This is stronger evidence that the C2 provider passed to the 30 Ma validation is actually backed by the required C1 provider.

## Scientific scope
- No scientific parameter changes.
- No v0.6.1 sealed payload changes.
- No environmental field changes.
- No adaptive-clock changes.
- No biology advanced.
- R3.14-R1 numerical portability semantics remain unchanged.

## Verification
The R3.14/R3.13/R3.12 focused suite passes 24/24 in the reference environment.
