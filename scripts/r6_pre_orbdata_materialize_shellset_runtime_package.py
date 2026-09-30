"""Materialize the governed owner-bound ShellSet input package; no ShellSet calls."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.pre_orbdata_runtime_package import write_package


if __name__ == "__main__":
    report = write_package(ROOT)
    print(f"mode={report['explicit_arcana_runtime_mode']}")
    print(f"nodes={report['node_count']} mixed={report['mixed_physical_support_count']}")
    print(f"runtime_data_sha256={report['runtime_data_sha256']}")
