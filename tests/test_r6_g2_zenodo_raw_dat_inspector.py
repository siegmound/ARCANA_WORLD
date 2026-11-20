"""Raw source inspection only: synthetic ZIPs do not calibrate ARCANA."""
import hashlib
import zipfile
import pytest
from experiments.plate58_deforming_explore_v1.zenodo_raw_dat_inspector import (
    inspect_archive, InspectionError,
)


def sample_zip(tmp_path, files):
    target = tmp_path / "x.zip"
    with zipfile.ZipFile(target, "w") as f:
        for path, data in files.items():
            f.writestr(path, data)
    data = target.read_bytes()
    return target, hashlib.md5(data).hexdigest(), hashlib.sha256(data).hexdigest()


def inspect(tmp_path, files):
    path, md5, sha = sample_zip(tmp_path, files)
    return inspect_archive(path, expected_md5=md5, expected_sha256=sha,
                           expected_counts={"gleason_tullis": 1, "zhou": 1})


def test_numeric_rows_do_not_imply_units(tmp_path):
    out = inspect(tmp_path, {
        "data/gleason_tullis_fig3a_1.dat": "# figure\n1.0 2.0\n3D0 4E0\n",
        "data/zhou_16_1125_1.dat": "colX colY\n3, 9\n4,10\n",
    })
    assert out["observed_file_count"] == 2
    assert out["total_numeric_rows"] == 4
    assert out["source_member_records"][0]["numeric_column_min_max_without_units"] == [[1, 3], [2, 4]]
    assert not out["stress_strain_rate_pressure_temperature_water_per_row_verified"]


def test_archive_md5_fails_closed(tmp_path):
    path, md5, sha = sample_zip(tmp_path, {"data/gleason_tullis_fig3a_1.dat": "1 2"})
    with pytest.raises(InspectionError, match="CHECKSUM_MISMATCH"):
        inspect_archive(path, expected_md5="0" * 32, expected_sha256=sha)


def test_unknown_file_name_rejected(tmp_path):
    with pytest.raises(InspectionError, match="UNKNOWN_FIGURE_FILENAME"):
        inspect(tmp_path, {
            "data/gleason_tullis_fig3a_1.dat": "1 2",
            "data/mystery.dat": "2 3",
        })


def test_source_member_count_mismatch_rejected(tmp_path):
    path, md5, sha = sample_zip(tmp_path, {"data/gleason_tullis_fig3a_1.dat": "1 2"})
    with pytest.raises(InspectionError, match="FAMILY_CARDINALITY"):
        inspect_archive(path, expected_md5=md5, expected_sha256=sha)


def test_unparsed_header_preserved(tmp_path):
    out = inspect(tmp_path, {
        "data/gleason_tullis_fig3a_1.dat": "pressure (MPa)\n1 2\n",
        "data/zhou_16_1125_1.dat": "1 3\n",
    })
    assert out["source_member_records"][0]["first_unparsed_lines"][0]["text"] == "pressure (MPa)"


def test_nonfinite_rows_rejected(tmp_path):
    with pytest.raises(InspectionError, match="NONFINITE"):
        inspect(tmp_path, {
            "data/gleason_tullis_fig3a_1.dat": "nan 2",
            "data/zhou_16_1125_1.dat": "1 2",
        })


def test_unexpected_archive_payload_rejected(tmp_path):
    with pytest.raises(InspectionError, match="UNEXPECTED_NON_DAT"):
        inspect(tmp_path, {
            "data/gleason_tullis_fig3a_1.dat": "1 2",
            "data/zhou_16_1125_1.dat": "1 2",
            "data/readme.exe": "bad",
        })
