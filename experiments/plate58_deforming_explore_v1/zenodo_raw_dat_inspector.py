"""Inspect Zenodo 8304793 data.zip without extracting, converting units, or fitting.

Digitized ordinate/abscissa data cannot be called measured stress/rate
before verifying the original figure captions and secondary publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import zipfile

EXPECTED_MD5 = "fbb1734ffce3eb94e4ef974f5b2cb7be"
EXPECTED_SHA256 = "1af973f4e96afe615d0f3eee94020b8a2186422392d3bcfa85699fd01f41327d"
SOURCE_URI = "https://zenodo.org/records/8304793"
STATUS = "PASS_SOURCE_ARCHIVE_INTEGRITY_AND_RAW_SHAPE__EXPERIMENTAL_COLUMN_SEMANTICS_UNQUALIFIED"


class InspectionError(ValueError):
    pass


def sha_file(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def family(path: str) -> str:
    name = PurePosixPath(path).name
    if re.fullmatch(r"gleason_tullis_fig(?:3a|3b|6a|6b|6c)_[1-9][0-9]*\.dat", name):
        return "gleason_tullis"
    if re.fullmatch(r"zhou_16_[0-9]{4}_[1-9][0-9]*\.dat", name):
        return "zhou"
    raise InspectionError("ZENODO_UNKNOWN_FIGURE_FILENAME: " + path)


def inspect_member(info: zipfile.ZipInfo, data: bytes) -> dict:
    try:
        content = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InspectionError("ZENODO_NON_UTF8_DAT: " + info.filename) from exc
    lines = content.splitlines()
    nonempty = [row.strip() for row in lines if row.strip()]
    sample = nonempty[:5]
    rows = []
    unparsed = []
    for lineno, raw in enumerate(lines, 1):
        row = raw.strip()
        if not row or row.startswith(("#", "!", "%", "//")):
            continue
        # Only inspect clearly numeric fields. Unknown text remains raw evidence.
        row = re.split(r"\s+(?:#|!|%)", row, maxsplit=1)[0]
        tokens = re.split(r"[\s,;]+", row)
        try:
            values = [float(v.replace("D", "E").replace("d", "e")) for v in tokens]
        except ValueError:
            if len(unparsed) < 5:
                unparsed.append({"line": lineno, "text": raw[:220]})
            continue
        if not values or not all(math.isfinite(v) for v in values):
            raise InspectionError("ZENODO_NONFINITE_NUMERIC_ROW: " + info.filename)
        rows.append((lineno, values))
    widths = sorted({len(v) for _, v in rows})
    column_ranges = []
    if len(widths) == 1:
        width = widths[0]
        for index in range(width):
            values = [r[index] for _, r in rows]
            column_ranges.append([min(values), max(values)])
    return {
        "name": info.filename, "figure_family": family(info.filename),
        "raw_sha256": digest(data), "uncompressed_bytes": len(data),
        "total_lines": len(lines), "nonempty_lines": len(nonempty),
        "numeric_data_rows": len(rows), "observed_numeric_column_counts": widths,
        "raw_first_nonempty_lines": sample, "first_unparsed_lines": unparsed,
        "raw_first_numeric_rows": [dict(line=line, columns=vals) for line, vals in rows[:3]],
        "numeric_column_min_max_without_units": column_ranges,
        "axes_units_or_stress_rate_semantics_verified": False,
        "independent_laboratory_experiment_count_inferred": None,
    }


def inspect_archive(archive: Path, *, expected_md5: str = EXPECTED_MD5,
                    expected_sha256: str = EXPECTED_SHA256,
                    expected_counts: dict | None = None) -> dict:
    if expected_counts is None:
        expected_counts = {"gleason_tullis": 18, "zhou": 21}
    if not archive.is_file():
        raise InspectionError("ZENODO_ARCHIVE_MISSING")
    size = archive.stat().st_size
    if not 0 < size < 20_000_000:
        raise InspectionError("ZENODO_ARCHIVE_UNEXPECTED_SIZE")
    md5 = sha_file(archive, "md5")
    sha = sha_file(archive, "sha256")
    if md5 != expected_md5 or sha != expected_sha256:
        raise InspectionError("ZENODO_ARCHIVE_CHECKSUM_MISMATCH")
    records = []
    with zipfile.ZipFile(archive) as z:
        items = z.infolist()
        names = [i.filename for i in items]
        if len(names) != len(set(names)):
            raise InspectionError("ZENODO_DUPLICATE_ZIP_MEMBER")
        if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
               or "\\" in name or "\x00" in name for name in names):
            raise InspectionError("ZENODO_UNSAFE_ZIP_MEMBER_NAME")
        files = [i for i in items if not i.is_dir()]
        if any(not i.filename.startswith("data/") or not i.filename.endswith(".dat")
               for i in files):
            raise InspectionError("ZENODO_UNEXPECTED_NON_DAT_MEMBER")
        if sum(i.file_size for i in files) > 20_000_000:
            raise InspectionError("ZENODO_UNCOMPRESSED_SIZE_TOO_LARGE")
        for i in sorted(files, key=lambda row: row.filename):
            records.append(inspect_member(i, z.read(i)))
    family_counts = {f: sum(x["figure_family"] == f for x in records)
                     for f in ("gleason_tullis", "zhou")}
    if family_counts != expected_counts:
        raise InspectionError("ZENODO_SOURCE_FIGURE_FAMILY_CARDINALITY_MISMATCH")
    return {
        "schema": "ARCANA_R6_ZENODO_8304793_RAW_DAT_INSPECTION_V1",
        "status": STATUS, "published_data_record": SOURCE_URI,
        "source_archive_path": str(archive),
        "source_archive_bytes": size, "source_archive_md5": md5,
        "source_archive_sha256": sha,
        "observed_file_count": len(records), "observed_figure_file_family_counts": family_counts,
        "total_numeric_rows": sum(x["numeric_data_rows"] for x in records),
        "source_member_records": records,
        "raw_data_has_been_rewritten_or_extracted": False,
        "units_provenance_and_figure_axes_verified": False,
        "figure_files_are_independent_experiments": None,
        "stress_strain_rate_pressure_temperature_water_per_row_verified": False,
        "g2_parameters_calibrated": None,
        "mechanical_solve_authorized": False, "solver_runs": 0, "physical_T1": None,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    if args.output.exists():
        raise InspectionError("ZENODO_INSPECTION_OUTPUT_ALREADY_EXISTS")
    result = inspect_archive(args.archive)
    args.output.mkdir(parents=True, exist_ok=False)
    target = args.output / "RAW_DAT_INSPECTION.json"
    data = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    target.write_bytes(data)
    manifest = {
        "schema": "ARCANA_R6_ZENODO_8304793_RAW_DAT_INSPECTION_MANIFEST_V1",
        "status": STATUS, "source_archive_sha256": result["source_archive_sha256"],
        "files": {"RAW_DAT_INSPECTION.json": digest(data)},
        "no_fit": True, "no_solver_run": True, "no_T1": True,
        "no_canonical_promotion": True,
    }
    (args.output / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({
        "status": STATUS, "files": result["observed_file_count"],
        "families": result["observed_figure_file_family_counts"],
        "numeric_rows": result["total_numeric_rows"],
        "output": str(args.output), "solver_runs": 0, "physical_T1": None,
    }, indent=2))


if __name__ == "__main__":
    main()
