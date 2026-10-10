import copy

from scripts.r6_si1_bandwidth_f2b_d3b_numerical import (
    INVALID_INPUT,
    NUMERICAL_DIAGNOSTIC_UNDEFINED,
    OFFLINE_VALIDATOR_PASS,
    THRESHOLD_UNJUSTIFIED,
    band_matvec,
    diagnose_system,
)


def dense_to_band(matrix, kl, ku):
    """Test-only independent fixture encoder for DGBSV general-band storage."""
    n = len(matrix)
    ldab = 2 * kl + ku + 1
    band = [[0.0 for _ in range(n)] for _ in range(ldab)]
    for i in range(n):
        for j in range(n):
            if -ku <= i - j <= kl:
                band[kl + ku + i - j][j] = matrix[i][j]
            else:
                assert matrix[i][j] == 0.0
    return band


def dense_matvec(matrix, x):
    return [sum(aij * xj for aij, xj in zip(row, x)) for row in matrix]


def test_asymmetric_band_kl_not_equal_ku_matches_known_dense_answer():
    dense = [[4.0, 1.0, -1.0], [2.0, 5.0, 3.0], [0.0, -2.0, 6.0]]
    x = [1.0, 2.0, -1.0]
    ab = dense_to_band(dense, kl=1, ku=2)
    actual = band_matvec(ab, x, kl=1, ku=2)
    assert actual == {
        "status": OFFLINE_VALIDATOR_PASS,
        "solver_acceptance": THRESHOLD_UNJUSTIFIED,
        "values": [7.0, 9.0, -10.0],
        "result_exactness": ["EXACT_BINARY64"] * 3,
        "arithmetic": "EXACT_RATIONAL_FROM_BINARY64_INPUTS",
    }
    assert actual["values"] == dense_matvec(dense, x)


def test_other_asymmetric_band_with_kl_greater_than_ku():
    dense = [[2.0, 3.0, 0.0], [-1.0, 4.0, 5.0], [6.0, 2.0, 7.0]]
    x = [2.0, -1.0, 3.0]
    ab = dense_to_band(dense, kl=2, ku=1)
    result = band_matvec(ab, x, kl=2, ku=1)
    assert result["status"] == OFFLINE_VALIDATOR_PASS
    assert result["values"] == dense_matvec(dense, x) == [1.0, 9.0, 31.0]


def test_residual_normwise_and_componentwise_match_hand_calculation():
    dense = [[4.0, 1.0, -1.0], [2.0, 5.0, 3.0], [0.0, -2.0, 6.0]]
    x = [1.0, 2.0, -1.0]
    b0 = [8.0, 9.0, -8.0]
    ab = dense_to_band(dense, 1, 2)
    ab_before, b_before = copy.deepcopy(ab), list(b0)
    result = diagnose_system(ab, b0, x, kl=1, ku=2)
    assert result["status"] == OFFLINE_VALIDATOR_PASS
    assert result["solver_acceptance"] == THRESHOLD_UNJUSTIFIED
    assert result["residual_vector"] == [1.0, 0.0, 2.0]
    assert result["absolute_residual_inf"] == 2.0
    assert result["matrix_inf_norm"] == 10.0
    assert result["solution_inf_norm"] == 2.0
    assert result["rhs_inf_norm"] == 9.0
    assert result["backward_error_normwise"] == 2 / 29
    assert result["backward_error_componentwise"] == 1 / 9
    assert ab == ab_before and b0 == b_before


def test_exact_binary64_rational_path_handles_large_and_small_operands():
    large = band_matvec([[1e200]], [1e100], kl=0, ku=0)
    assert large["status"] == OFFLINE_VALIDATOR_PASS
    assert large["values"] == [1e300]
    tiny = band_matvec([[5e-324]], [1.0], kl=0, ku=0)
    assert tiny["status"] == OFFLINE_VALIDATOR_PASS
    assert tiny["values"] == [5e-324]
    assert tiny["result_exactness"] == ["EXACT_BINARY64"]
    inexact_normal = band_matvec([[0.0, 2.0 ** -53], [1.0, 0.0]], [1.0, 1.0], kl=0, ku=1)
    assert inexact_normal["status"] == OFFLINE_VALIDATOR_PASS
    assert inexact_normal["values"][0] == 1.0
    assert inexact_normal["result_exactness"][0] == "ROUNDED_NORMAL_BINARY64"
    negative = band_matvec([[-5e-324]], [0.75], kl=0, ku=0)
    assert negative["status"] == NUMERICAL_DIAGNOSTIC_UNDEFINED
    exact_zero = band_matvec([[0.0]], [0.75], kl=0, ku=0)
    assert exact_zero["values"] == [0.0]
    assert exact_zero["result_exactness"] == ["EXACT_BINARY64"]
    underflow = band_matvec([[5e-324]], [0.5], kl=0, ku=0)
    assert underflow["status"] == NUMERICAL_DIAGNOSTIC_UNDEFINED
    overflow = band_matvec([[1.7e308]], [2.0], kl=0, ku=0)
    assert overflow["status"] == NUMERICAL_DIAGNOSTIC_UNDEFINED


def test_inexact_nonzero_subnormal_is_not_reported_as_exact_or_pass():
    result = band_matvec([[5e-324]], [0.75], kl=0, ku=0)
    assert result["status"] == NUMERICAL_DIAGNOSTIC_UNDEFINED
    assert "subnormal" in result["reason"]


def test_band_boundary_oracles_and_operational_limits_precede_conversion():
    # Upper-only band: first/last columns and asymmetric edge values.
    ku_only = [[0.0, 0.0, 3.0, 6.0], [0.0, 2.0, 5.0, 8.0], [1.0, 4.0, 7.0, 9.0]]
    assert band_matvec(ku_only, [1.0, 2.0, 3.0, 4.0], kl=0, ku=2)["values"] == [14.0, 47.0, 53.0, 36.0]

    # Lower-only band: explicitly calculated from a distinct orientation.
    kl_only = [[0.0] * 4 for _ in range(5)]
    kl_only[2][0], kl_only[3][0], kl_only[4][0] = 1.0, 2.0, 3.0
    kl_only[2][1], kl_only[3][1], kl_only[4][1] = 5.0, 7.0, 13.0
    kl_only[2][2], kl_only[3][2] = 11.0, 17.0
    kl_only[2][3] = 19.0
    assert band_matvec(kl_only, [2.0, 3.0, 4.0, 5.0], kl=2, ku=0)["values"] == [2.0, 19.0, 71.0, 202.0]

    # Both matrix and vector are tiny to construct; the cap must reject before AB conversion.
    oversized = band_matvec([], [0.0] * 64_442, kl=0, ku=0)
    assert oversized["status"] == INVALID_INPUT
    assert "synthetic dimension" in oversized["reason"]
    too_wide = band_matvec([], [0.0] * 2048, kl=2047, ku=0)
    assert too_wide["status"] == INVALID_INPUT
    assert "band storage cells" in too_wide["reason"]


def test_invalid_shapes_nonfinite_values_and_reserved_storage_fail_closed():
    assert band_matvec([], [1.0], kl=0, ku=0)["status"] == INVALID_INPUT
    assert band_matvec([[0.0], [1.0]], [], kl=0, ku=0)["status"] == INVALID_INPUT
    assert band_matvec([[0.0], [float("nan")], [0.0]], [1.0], kl=0, ku=0)["status"] == INVALID_INPUT
    assert band_matvec([[float("nan")]], [1.0], kl=0, ku=0)["status"] == INVALID_INPUT
    assert band_matvec([[1.0]], [float("inf")], kl=0, ku=0)["status"] == INVALID_INPUT
    assert band_matvec([["1"]], [1.0], kl=0, ku=0)["status"] == INVALID_INPUT
    assert band_matvec([[1.0]], [True], kl=0, ku=0)["status"] == INVALID_INPUT
    assert diagnose_system([[1.0]], [float("nan")], [1.0], kl=0, ku=0)["status"] == INVALID_INPUT
    # For kl=1, row zero/column zero is reserved pivot-fill storage.
    assert band_matvec([[1.0, 0.0], [0.0, 0.0], [0.0, 0.0]], [1.0, 1.0], kl=1, ku=0)["status"] == INVALID_INPUT
    assert band_matvec([[1.0]], [1.0, 2.0], kl=0, ku=0)["status"] == INVALID_INPUT


def test_zero_over_zero_has_explicit_policy_and_no_acceptance_threshold():
    result = diagnose_system([[0.0]], [0.0], [0.0], kl=0, ku=0)
    assert result["status"] == OFFLINE_VALIDATOR_PASS
    assert result["backward_error_normwise"] == 0.0
    assert result["backward_error_componentwise"] == 0.0
    assert result["zero_over_zero_policy"] == "DEFINED_AS_ZERO"
    assert result["solver_acceptance"] == THRESHOLD_UNJUSTIFIED
