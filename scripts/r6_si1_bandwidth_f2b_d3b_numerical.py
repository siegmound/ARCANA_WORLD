"""Solver-free numerical diagnostics for small synthetic general-band systems.

All finite binary64 inputs are converted to exact rational values before the
diagnostic arithmetic. Results that cannot be represented as binary64 are
reported as undefined instead of being rounded to zero or infinity silently.
The arithmetic is band-only: O(n*(kl+ku+1)) time and O(n+LDAB*n) working
space including the validated immutable copy of AB. Synthetic limits below
are operational safeguards, not numerical acceptance criteria.
"""

from __future__ import annotations

import math
from fractions import Fraction
import sys
from typing import Any, Sequence

OFFLINE_VALIDATOR_PASS = "OFFLINE_VALIDATOR_PASS"
INVALID_INPUT = "INVALID_INPUT"
NUMERICAL_DIAGNOSTIC_UNDEFINED = "NUMERICAL_DIAGNOSTIC_UNDEFINED"
THRESHOLD_UNJUSTIFIED = "THRESHOLD_UNJUSTIFIED"

# Operational limits for synthetic fixtures; these are not numerical acceptance thresholds.
MAX_SYNTHETIC_N = 2048
MAX_BAND_CELLS = 2_000_000
MAX_ARITHMETIC_TERMS = 2_000_000


class _InvalidInput(Exception):
    pass


def _finite_matrix(ab: Sequence[Sequence[float]], n: int, kl: int, ku: int) -> tuple[tuple[float, ...], ...]:
    if isinstance(ab, (str, bytes)) or len(ab) == 0:
        raise _InvalidInput("AB must be a nonempty two-dimensional sequence")
    ldab = 2 * kl + ku + 1
    if len(ab) != ldab:
        raise _InvalidInput(f"AB row count must equal LDAB={ldab}")
    rows: list[tuple[float, ...]] = []
    for row in ab:
        if isinstance(row, (str, bytes)) or len(row) != n:
            raise _InvalidInput("every AB row must contain exactly n columns")
        converted = tuple(_as_binary64(value, "AB coefficient") for value in row)
        if not all(math.isfinite(value) for value in converted):
            raise _InvalidInput("AB contains NaN or infinity")
        rows.append(converted)
    # Reject nonzero storage that does not encode any element of the original A.
    diagonal0 = kl + ku
    for row0, row in enumerate(rows):
        for col0, value in enumerate(row):
            matrix_row0 = row0 - diagonal0 + col0
            in_band = 0 <= matrix_row0 < n and -ku <= matrix_row0 - col0 <= kl
            if not in_band and value != 0.0:
                raise _InvalidInput("AB has a nonzero in a reserved or out-of-band slot")
    return tuple(rows)


def _fraction_vector(values: Sequence[float], n: int, name: str) -> tuple[Fraction, ...]:
    if isinstance(values, (str, bytes)) or len(values) != n:
        raise _InvalidInput(f"{name} length must equal n={n}")
    converted = tuple(_as_binary64(value, name) for value in values)
    if not all(math.isfinite(value) for value in converted):
        raise _InvalidInput(f"{name} contains NaN or infinity")
    return tuple(Fraction.from_float(value) for value in converted)


def _as_binary64(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _InvalidInput(f"{name} values must be real numeric scalars, not booleans/strings")
    try:
        return float(value)
    except (OverflowError, ValueError) as exc:
        raise _InvalidInput(f"{name} value is outside binary64 input range") from exc


def _to_binary64(value: Fraction, label: str) -> tuple[float, str]:
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ArithmeticError(f"{label} is not representable as finite binary64") from exc
    if not math.isfinite(result):
        raise ArithmeticError(f"{label} is not representable as finite binary64")
    if value and result == 0.0:
        raise ArithmeticError(f"{label} underflows binary64 to zero")
    exact = Fraction.from_float(result) == value
    if result != 0.0 and abs(result) < sys.float_info.min and not exact:
        raise ArithmeticError(f"{label} rounds inexactly to a binary64 subnormal")
    return result, "EXACT_BINARY64" if exact else "ROUNDED_NORMAL_BINARY64"


def _check_work_size(n: int, kl: int, ku: int, *, work_passes: int = 1) -> None:
    """Reject oversized fixtures before copying or converting input arrays."""
    if n < 1 or n > MAX_SYNTHETIC_N:
        raise _InvalidInput(f"synthetic dimension n must be in [1,{MAX_SYNTHETIC_N}]")
    width = min(n, kl + ku + 1)
    band_cells = (2 * kl + ku + 1) * n
    terms = work_passes * n * width
    if band_cells > MAX_BAND_CELLS:
        raise _InvalidInput(f"band storage cells exceed operational limit {MAX_BAND_CELLS}")
    if terms > MAX_ARITHMETIC_TERMS:
        raise _InvalidInput(f"band arithmetic terms exceed operational limit {MAX_ARITHMETIC_TERMS}")


def _band_arithmetic(
    band: tuple[tuple[float, ...], ...], x: tuple[Fraction, ...], kl: int, ku: int
) -> tuple[tuple[Fraction, ...], tuple[Fraction, ...]]:
    """Return exact A*x and absolute row sums using only original band entries."""
    n = len(x)
    diagonal0 = kl + ku
    ax: list[Fraction] = []
    row_abs_sums: list[Fraction] = []
    for i in range(n):
        total = Fraction(0)
        row_abs = Fraction(0)
        for j in range(max(0, i - kl), min(n - 1, i + ku) + 1):
            value = Fraction.from_float(band[diagonal0 + i - j][j])
            total += value * x[j]
            row_abs += abs(value)
        ax.append(total)
        row_abs_sums.append(row_abs)
    return tuple(ax), tuple(row_abs_sums)


def _band_component_denominator(
    band: tuple[tuple[float, ...], ...], x: tuple[Fraction, ...], b: tuple[Fraction, ...],
    i: int, kl: int, ku: int,
) -> Fraction:
    diagonal0 = kl + ku
    denominator = abs(b[i])
    for j in range(max(0, i - kl), min(len(x) - 1, i + ku) + 1):
        value = Fraction.from_float(band[diagonal0 + i - j][j])
        denominator += abs(value) * abs(x[j])
    return denominator


def band_matvec(ab: Sequence[Sequence[float]], x: Sequence[float], *, kl: int, ku: int) -> dict[str, Any]:
    """Multiply an original A encoded in DGBSV AB storage; no solver is used."""
    try:
        if isinstance(kl, bool) or not isinstance(kl, int) or kl < 0:
            raise _InvalidInput("kl must be a nonnegative integer")
        if isinstance(ku, bool) or not isinstance(ku, int) or ku < 0:
            raise _InvalidInput("ku must be a nonnegative integer")
        n = len(x)
        if n < 1 or kl >= n or ku >= n:
            raise _InvalidInput("n must be positive and kl/ku must be less than n")
        _check_work_size(n, kl, ku)
        band = _finite_matrix(ab, n, kl, ku)
        xv = _fraction_vector(x, n, "x")
        exact_values, _ = _band_arithmetic(band, xv, kl, ku)
        converted = [_to_binary64(value, f"matvec[{row}]") for row, value in enumerate(exact_values)]
        return {"status": OFFLINE_VALIDATOR_PASS, "solver_acceptance": THRESHOLD_UNJUSTIFIED,
                "values": [item[0] for item in converted],
                "result_exactness": [item[1] for item in converted],
                "arithmetic": "EXACT_RATIONAL_FROM_BINARY64_INPUTS"}
    except (ArithmeticError, _InvalidInput, TypeError, ValueError, OverflowError, IndexError) as exc:
        status = NUMERICAL_DIAGNOSTIC_UNDEFINED if isinstance(exc, ArithmeticError) else INVALID_INPUT
        return {"status": status, "reason": str(exc)}


def diagnose_system(
    ab: Sequence[Sequence[float]], b0: Sequence[float], x: Sequence[float], *, kl: int, ku: int
) -> dict[str, Any]:
    """Compute residual and backward errors without mutating A0/b0/x."""
    try:
        if isinstance(kl, bool) or not isinstance(kl, int) or kl < 0:
            raise _InvalidInput("kl must be a nonnegative integer")
        if isinstance(ku, bool) or not isinstance(ku, int) or ku < 0:
            raise _InvalidInput("ku must be a nonnegative integer")
        if isinstance(x, (str, bytes)) or len(x) < 1:
            raise _InvalidInput("x must be nonempty")
        n = len(x)
        if kl >= n or ku >= n:
            raise _InvalidInput("kl/ku must be less than n")
        _check_work_size(n, kl, ku, work_passes=2)
        band = _finite_matrix(ab, n, kl, ku)
        bv = _fraction_vector(b0, n, "b0")
        xv = _fraction_vector(x, n, "x")
        ax, row_abs_sums = _band_arithmetic(band, xv, kl, ku)
        residual = tuple(bv[i] - ax[i] for i in range(n))
        abs_residual = max((abs(value) for value in residual), default=Fraction(0))
        norm_a = max(row_abs_sums, default=Fraction(0))
        norm_x = max((abs(value) for value in xv), default=Fraction(0))
        norm_b = max((abs(value) for value in bv), default=Fraction(0))
        norm_denominator = norm_a * norm_x + norm_b
        if norm_denominator == 0:
            normwise = Fraction(0) if abs_residual == 0 else None
        else:
            normwise = abs_residual / norm_denominator

        componentwise_values: list[Fraction] = []
        for i in range(n):
            denominator = _band_component_denominator(band, xv, bv, i, kl, ku)
            numerator = abs(residual[i])
            if denominator == 0:
                if numerator != 0:
                    raise ArithmeticError(f"componentwise denominator is zero with nonzero residual at row {i}")
                componentwise_values.append(Fraction(0))
            else:
                componentwise_values.append(numerator / denominator)
        if normwise is None:
            raise ArithmeticError("normwise denominator is zero with nonzero residual")
        converted_metrics = {
            "absolute_residual_inf": _to_binary64(abs_residual, "absolute residual"),
            "backward_error_normwise": _to_binary64(normwise, "normwise backward error"),
            "backward_error_componentwise": _to_binary64(max(componentwise_values, default=Fraction(0)), "componentwise backward error"),
            "residual_vector": [_to_binary64(value, f"residual[{i}]") for i, value in enumerate(residual)],
            "matrix_inf_norm": _to_binary64(norm_a, "matrix infinity norm"),
            "solution_inf_norm": _to_binary64(norm_x, "solution infinity norm"),
            "rhs_inf_norm": _to_binary64(norm_b, "RHS infinity norm"),
        }
        metrics = {
            key: [item[0] for item in value] if isinstance(value, list) else value[0]
            for key, value in converted_metrics.items()
        }
        metrics["result_exactness"] = {
            key: [item[1] for item in value] if isinstance(value, list) else value[1]
            for key, value in converted_metrics.items()
        }
        metrics.update({
            "zero_over_zero_policy": "DEFINED_AS_ZERO",
        })
        return {"status": OFFLINE_VALIDATOR_PASS, "solver_acceptance": THRESHOLD_UNJUSTIFIED,
                "arithmetic": "EXACT_RATIONAL_FROM_BINARY64_INPUTS", **metrics}
    except (ArithmeticError, _InvalidInput, TypeError, ValueError, OverflowError, IndexError) as exc:
        status = NUMERICAL_DIAGNOSTIC_UNDEFINED if isinstance(exc, ArithmeticError) else INVALID_INPUT
        return {"status": status, "reason": str(exc)}


__all__ = [
    "INVALID_INPUT", "NUMERICAL_DIAGNOSTIC_UNDEFINED", "OFFLINE_VALIDATOR_PASS", "THRESHOLD_UNJUSTIFIED",
    "band_matvec", "diagnose_system",
]
