import importlib.util
import math
from pathlib import Path
import io
import json
import copy
import unittest
from typing import Any, ClassVar

spec = importlib.util.spec_from_file_location('view_audit', Path(__file__).parents[1] / 'audit.py')
assert spec is not None and spec.loader is not None
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class Coordinates(unittest.TestCase):
    def test_all_cells_roundtrip(self):
        for i in range(64800):
            row, col = audit.row_col(i)
            self.assertEqual(audit.checked_cell(row, col), i)
            self.assertEqual(audit.locate(*audit.center(row, col)), (row, col))

    def test_seam_and_poles(self):
        for lon in (-540, -180, 180, 540):
            self.assertEqual(audit.locate(0, lon), (90, 0))
        self.assertEqual(audit.locate(0, 179.999), (90, 359))
        self.assertEqual(audit.locate(-90, -180), (0, 0))
        self.assertEqual(audit.locate(90, 180), (179, 0))
        self.assertEqual(audit.center(0, 0), (-89.5, -179.5))
        self.assertEqual(audit.center(179, 359), (89.5, 179.5))

    def test_invalid_coordinates(self):
        for lat, lon in [(91, 0), (-91, 0), (math.nan, 0), (0, math.inf)]:
            with self.assertRaises(ValueError):
                audit.locate(lat, lon)
        for row, col in [(-1, 0), (180, 0), (0, 360), (0.5, 0), (True, 0)]:
            with self.assertRaises(ValueError):
                audit.checked_cell(row, col)


class Safety(unittest.TestCase):
    def test_masks_do_not_change_values(self):
        values = [0.0, math.nan, math.nan, 7.0]
        self.assertEqual(audit.classify(values, [True, False, True, True],
                                        [False, True, False, False]),
                         ['VALID', 'UNKNOWN', 'INVALID', 'VALID'])
        self.assertTrue(math.isnan(values[1]))
        self.assertEqual(values[0], 0.0)
        self.assertEqual(audit.classify([math.nan], [False], [False]), ['UNSUPPORTED'])

    def test_invalid_masks(self):
        for support, unknown in [([], [True]), ([1], [False])]:
            with self.assertRaises(ValueError):
                audit.classify([1.0], support, unknown)

    def test_authority_is_never_promoted(self):
        self.assertFalse(audit.authority_allowed('NONE'))
        self.assertFalse(audit.authority_allowed('EVIDENCE_ONLY'))
        self.assertFalse(audit.authority_allowed('NONCANONICAL_ENGINEERING'))
        self.assertTrue(audit.authority_allowed('NONCANONICAL_ENGINEERING', engineering=True))
        self.assertTrue(audit.authority_allowed('AUTHORIAL_SYNTHETIC_INITIALIZATION'))
        with self.assertRaises(ValueError):
            audit.authority_allowed('OBSERVED_EARTH')

    def test_sha_missing_and_mismatch_fail_closed(self):
        p = Path(__file__)
        before = p.read_bytes()
        pin = {'sha256': '0' * 64, 'bytes': len(before)}
        self.assertEqual(audit.inspect_file(p / 'absent', pin, 'EVIDENCE_ONLY')['status'], 'INPUT_UNAVAILABLE')
        self.assertEqual(audit.inspect_file(p, pin, 'EVIDENCE_ONLY')['status'], 'SHA_MISMATCH')
        pin['sha256'] = audit.sha256(p)
        self.assertEqual(audit.inspect_file(p, pin, 'EVIDENCE_ONLY')['status'], 'VERIFIED')
        pin['bytes'] = 2
        self.assertEqual(audit.inspect_file(p, pin, 'EVIDENCE_ONLY')['status'], 'SIZE_MISMATCH')
        self.assertEqual(p.read_bytes(), before)

    def test_npz_objects_rejected(self):
        import zipfile
        p = io.BytesIO()
        h = b"{'descr': '|O', 'fortran_order': False, 'shape': (1,), }\n"
        with zipfile.ZipFile(p, 'w') as z:
            z.writestr('object.npy', b'\x93NUMPY\x02\x00' + len(h).to_bytes(4, 'little') + h)
        p.seek(0)
        with self.assertRaisesRegex(ValueError, 'dtype'):
            audit.npz_arrays(p)


class Inventory(unittest.TestCase):
    repo: ClassVar[Path]
    lock: ClassVar[dict[str, Any]]
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[2]
        cls.lock = json.loads((cls.repo / 'visualization/source-lock.json').read_text())

    def test_missing_external_payloads_are_not_inferred(self):
        report, code = audit.audit(self.repo, self.lock, self.repo / 'visualization/ABSENT_EXTERNAL_ROOT')
        self.assertEqual(code, 2)
        self.assertEqual(report['status'], 'INPUT_UNAVAILABLE')
        self.assertEqual(len(report['missing']), 2)
        self.assertEqual(report['checks']['geography']['status'], 'INPUT_UNAVAILABLE')
        self.assertEqual(report['checks']['partition']['status'], 'INPUT_UNAVAILABLE')
        self.assertFalse(report['authority_promoted'])

    def test_sha_mismatch_disables_contract_checks(self):
        lock = copy.deepcopy(self.lock)
        lock['sources'][0]['sha256'] = '0' * 64
        report, code = audit.audit(self.repo, lock, self.repo / 'visualization/ABSENT_EXTERNAL_ROOT')
        self.assertEqual(code, 1)
        self.assertEqual(report['status'], 'FAIL_CLOSED')
        self.assertEqual(report['sources'][0]['status'], 'SHA_MISMATCH')
        self.assertEqual(report['checks'], {})
        self.assertNotIn('fields', report['sources'][0])

    def test_grid_radius_rejected(self):
        load = lambda p: json.loads((self.repo / p).read_text())
        s = load('R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json')
        m = load('R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json')
        p = load('R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json')
        self.assertEqual(audit.validate_grid(s, m, p)['status'], 'VERIFIED')
        m['grid']['radius_m'] = 6378137
        with self.assertRaisesRegex(ValueError, 'radius'):
            audit.validate_grid(s, m, p)


if __name__ == '__main__':
    unittest.main()
