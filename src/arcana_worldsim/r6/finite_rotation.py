"""Exact constant-Euler spherical rotation primitives for R6.

These point/feature-coordinate operations do not resolve plate contacts,
shared-boundary motion, topology, collision, or newly exposed ocean domains.
They are therefore not, by themselves, an authorized world-state transition.
"""

from __future__ import annotations

from math import cos, isfinite, sin, sqrt
from typing import Iterable

Vector3 = tuple[float, float, float]


def _vector3(value: Iterable[float], name: str) -> Vector3:
    result = tuple(float(x) for x in value)
    if len(result) != 3 or not all(isfinite(x) for x in result):
        raise ValueError(f"{name} must contain exactly three finite values")
    return result  # type: ignore[return-value]


def _cross(a: Vector3, b: Vector3) -> Vector3:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def rotate_vector_constant_euler(
    vector_xyz: Iterable[float],
    euler_angular_velocity_rad_per_year: Iterable[float],
    elapsed_years: float,
) -> Vector3:
    """Apply the exact finite rotation for a constant Euler vector.

    The input is an arbitrary finite 3-vector (normally a unit spherical
    position). Time must be non-negative and the Euler vector is radians/year.
    Quaternion form avoids an ODE step and remains stable for small angles.
    """
    vector = _vector3(vector_xyz, "vector_xyz")
    omega = _vector3(euler_angular_velocity_rad_per_year,
                     "euler_angular_velocity_rad_per_year")
    dt = float(elapsed_years)
    if not isfinite(dt) or dt < 0:
        raise ValueError("elapsed_years must be finite and non-negative")
    omega_norm = sqrt(sum(x * x for x in omega))
    if omega_norm == 0.0 or dt == 0.0:
        return vector
    half_angle = 0.5 * omega_norm * dt
    qv_scale = sin(half_angle) / omega_norm
    qv = (omega[0] * qv_scale, omega[1] * qv_scale,
          omega[2] * qv_scale)
    qw = cos(half_angle)
    q_cross_v = _cross(qv, vector)
    second = _cross(qv, q_cross_v)
    return tuple(vector[i] + 2.0 * (qw * q_cross_v[i] + second[i])
                 for i in range(3))  # type: ignore[return-value]


def rotate_points_constant_euler(
    points_xyz: Iterable[Iterable[float]],
    euler_angular_velocity_rad_per_year: Iterable[float],
    elapsed_years: float,
) -> tuple[Vector3, ...]:
    """Return rotated fixture/feature points; does not mutate the input."""
    omega = _vector3(euler_angular_velocity_rad_per_year,
                     "euler_angular_velocity_rad_per_year")
    dt = float(elapsed_years)
    if not isfinite(dt) or dt < 0:
        raise ValueError("elapsed_years must be finite and non-negative")
    return tuple(rotate_vector_constant_euler(point, omega, dt)
                 for point in points_xyz)
