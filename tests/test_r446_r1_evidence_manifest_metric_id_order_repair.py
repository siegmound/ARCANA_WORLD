import inspect
import arcana_worldsim.scientific_engines.r446_geonomics_first_governed_revalidation_cohort_execution_evidence_capture as m


def test_exact_metric_ids_use_canonical_sorted_comparison():
    s = inspect.getsource(m._evidence_manifest)
    assert "metric_ids = sorted" in s
    assert 'metric_ids == sorted([' in s


def test_exact_authorized_five_ids_are_preserved():
    expected = sorted([
        m.MID_COORD,
        m.MID_CELL,
        m.MID_NN,
        m.MID_RASTER,
        m.MID_LAYER_SUMMARY,
    ])
    assert expected == [
        "GNX_CARRIER_COORDINATE_READBACK_XY",
        "GNX_CARRIER_NATIVE_CELL_READBACK_IJ",
        "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE",
        "GNX_NATIVE_LAYER_DESCRIPTIVE_SUMMARY",
        "GNX_NATIVE_LAYER_RASTER_READBACK",
    ]


def test_no_metric_id_added_or_removed_by_repair():
    s = inspect.getsource(m._evidence_manifest)
    assert "MID_COORD" in s
    assert "MID_CELL" in s
    assert "MID_NN" in s
    assert "MID_RASTER" in s
    assert "MID_LAYER_SUMMARY" in s


def test_evidence_semantics_unchanged():
    s = inspect.getsource(m._evidence_manifest)
    assert '"zero_numeric_thresholds"' in s
    assert '"zero_automatic_pass_fail"' in s
    assert '"zero_forbidden_metric_ids"' in s


def test_parent_plan_hash_still_frozen():
    assert m.EXPECTED_PARENT_PLAN_SHA256 == (
        "9a33a40c178a816526ca8aec053aae5a393086d7a18b9a3122bd453a4f592ec0"
    )


def test_repair_does_not_add_default_execution():
    s = inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s
