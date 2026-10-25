"""Bit-pattern identity and fail-closed publication tests; no scientific execution."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, ClassVar
import unittest
from unittest.mock import patch

import numpy as np

from visualization import audit, export_t0 as export


class StaticExport(unittest.TestCase):
    repo: ClassVar[Path] = Path(__file__).resolve().parents[2]
    visual: ClassVar[Path] = repo / 'visualization'
    prepared: ClassVar[export.PreparedExport]

    @classmethod
    def setUpClass(cls) -> None:
        cls.prepared = export.prepare(cls.repo)

    def setUp(self) -> None:
        self.owned = Path(tempfile.mkdtemp(prefix='.test-view1b-', dir=self.visual)).resolve()

    def tearDown(self) -> None:
        self.assertEqual(self.owned.parent, self.visual.resolve())
        self.assertTrue(self.owned.name.startswith('.test-view1b-'))
        self.assertFalse(self.owned.is_symlink())
        shutil.rmtree(self.owned)

    def snapshot(self, directory: Path) -> dict[str, str]:
        return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in directory.rglob('*') if p.is_file()}

    def publish(self, name: str) -> Path:
        destination = self.owned / name
        # Preparation is already a verified real-source snapshot; production still rechecks inputs.
        with patch.object(export, 'prepare', return_value=self.prepared):
            export.export(self.repo, destination)
        return destination

    def test_real_sources_shape_dtype_masks_and_element_bits(self) -> None:
        before = {p: audit.sha256(p) for p in self.prepared.inputs}
        destination = self.publish('all-native-arrays')
        export.validate_export(destination, self.prepared)
        self.assertEqual(len(self.prepared.arrays), 30)
        for relative, source in self.prepared.arrays.items():
            output = np.load(destination / relative, allow_pickle=False)
            self.assertEqual(output.shape, source.shape)
            self.assertEqual(output.dtype.str, source.dtype.str)
            self.assertTrue(output.flags.c_contiguous)
            self.assertEqual(output.tobytes(order='C'), source.tobytes(order='C'))
        elevation = np.load(destination / 'arrays/t0__land_surface_elevation_m.npy', allow_pickle=False)
        support = np.load(destination / 'arrays/t0__elevation_support_mask.npy', allow_pickle=False)
        self.assertEqual(int(np.isnan(elevation).sum()), 50542)
        self.assertEqual(int(support.sum()), 14258)
        self.assertTrue(np.isnan(elevation[~support]).all())
        self.assertEqual(before, {p: audit.sha256(p) for p in self.prepared.inputs})

    def test_deterministic_complete_directory_bytes(self) -> None:
        a, b = self.publish('first'), self.publish('second')
        self.assertEqual(self.snapshot(a), self.snapshot(b))
        self.assertEqual(len(self.snapshot(a)), 31)
        self.assertEqual((a / 'manifest.json').read_bytes(), (b / 'manifest.json').read_bytes())

    def test_nan_payloads_signed_zero_and_categorical_bits(self) -> None:
        # Distinct quiet/signaling NaNs, sign bits and signed zero: equal_nan is insufficient.
        bits = np.array([0x7FC01234, 0x7FA01234, 0xFFC05678, 0x80000000, 0x00000000], dtype='<u4')
        values = bits.view('<f4')
        restored = export.decode_npy(export.encode_npy(values))
        self.assertEqual(restored.tobytes(), bits.tobytes())
        self.assertTrue(export.same_bits(values, restored))
        changed = restored.copy()
        changed.view('<u4')[0] = 0x7FC00000
        self.assertFalse(export.same_bits(values, changed))
        for values in [np.array([-2, 0, 1, 2, 3], dtype='int8'), np.array([False, True], dtype='bool')]:
            self.assertEqual(export.decode_npy(export.encode_npy(values)).tobytes(), values.tobytes())

    def test_coordinate_index_and_seam_stay_source_native(self) -> None:
        for r, c in [(0, 0), (91, 28), (179, 359)]:
            self.assertEqual(audit.row_col(audit.checked_cell(r, c)), (r, c))
            self.assertEqual(audit.locate(*audit.center(r, c)), (r, c))
        self.assertEqual(audit.locate(0, -180), audit.locate(0, 180))
        manifest = self.prepared.manifest
        self.assertEqual(manifest['dataset']['geometry']['radiusM'], 6371000)
        self.assertTrue(manifest['dataset']['geometry']['periodicLongitude'])
        self.assertTrue(all(l['temporal']['elapsedYears'] == [0.0] for l in manifest['dataset']['layers']))

    def test_manifest_integrity_and_export_identity(self) -> None:
        manifest = copy.deepcopy(self.prepared.manifest)
        identifier = manifest.pop('exportId')
        self.assertEqual(identifier, 'viewexport_' + export.digest(export.canonical(manifest)))
        self.assertFalse(identifier.startswith('r6state_'))
        self.assertTrue(all(r['exportArrayId'].startswith('viewarray_') for r in manifest['arrays']))
        self.assertTrue(all(not v for v in manifest['governance'].values()))
        destination = self.publish('tamper-manifest')
        altered = copy.deepcopy(self.prepared.manifest)
        altered['dataset']['layers'][0]['units'] = 'invented units'
        (destination / 'manifest.json').write_bytes(export.canonical(altered))
        with self.assertRaisesRegex(export.ExportError, 'MANIFEST_INTEGRITY'):
            export.validate_export(destination, self.prepared)

    def test_missing_source_has_no_publication(self) -> None:
        destination = self.owned / 'missing-source'
        with self.assertRaisesRegex(export.ExportError, 'INPUT_UNAVAILABLE'):
            export.export(self.repo, destination, self.owned / 'absent-external')
        self.assertEqual(list(self.owned.iterdir()), [])

    def test_sha_size_mismatch_before_decode(self) -> None:
        path = self.owned / 'mismatch.npz'
        path.write_bytes(b'not an array')
        for pin, message in [({'bytes': 12, 'sha256': '0' * 64}, 'SHA_MISMATCH'),
                             ({'bytes': 13, 'sha256': '0' * 64}, 'SIZE_MISMATCH')]:
            with self.assertRaisesRegex(export.ExportError, message):
                export.authenticate(path, pin)

    def test_source_change_before_publication_cleans_only_owned_stage(self) -> None:
        destination = self.owned / 'changing-source'
        unrelated = self.owned / 'existing-evidence'
        unrelated.write_bytes(b'preserve')
        with patch.object(export, 'prepare', return_value=self.prepared), \
                patch.object(export, 'recheck_inputs', side_effect=export.ExportError('SHA_MISMATCH')):
            with self.assertRaisesRegex(export.ExportError, 'SHA_MISMATCH'):
                export.export(self.repo, destination)
        self.assertEqual(list(self.owned.iterdir()), [unrelated])
        self.assertEqual(unrelated.read_bytes(), b'preserve')

    def test_corrupt_npy_never_publishes_partial_directory(self) -> None:
        original = export.validate_export

        def corrupt_and_validate(stage: Path, prepared: export.PreparedExport) -> None:
            path = stage / next(iter(prepared.files))
            data = bytearray(path.read_bytes())
            data[-1] ^= 1
            path.write_bytes(data)
            original(stage, prepared)

        destination = self.owned / 'corrupt-array'
        with patch.object(export, 'prepare', return_value=self.prepared), \
                patch.object(export, 'validate_export', side_effect=corrupt_and_validate):
            with self.assertRaisesRegex(export.ExportError, 'OUTPUT_SHA_OR_BYTE'):
                export.export(self.repo, destination)
        self.assertEqual(list(self.owned.iterdir()), [])

    def test_existing_and_racing_destination_not_overwritten(self) -> None:
        existing = self.publish('existing')
        before = self.snapshot(existing)
        with self.assertRaisesRegex(export.ExportError, 'OUTPUT_ALREADY_EXISTS'):
            export.export(self.repo, existing)
        self.assertEqual(before, self.snapshot(existing))
        destination = self.owned / 'race'
        rename = export.os.rename

        def create_racer(source: Path, target: Path) -> None:
            target.mkdir()
            (target / 'sentinel').write_bytes(b'other owner')
            rename(source, target)

        with patch.object(export, 'prepare', return_value=self.prepared), \
                patch.object(export.os, 'rename', side_effect=create_racer):
            with self.assertRaises(OSError):
                export.export(self.repo, destination)
        self.assertEqual((destination / 'sentinel').read_bytes(), b'other owner')
        self.assertEqual({p.name for p in self.owned.iterdir()}, {'existing', 'race'})

    def test_unsupported_dtype_and_object_pickle_rejected(self) -> None:
        for array in [np.array([1], dtype='int32'), np.array([{'a': 1}], dtype=object)]:
            with self.assertRaisesRegex(export.ExportError, 'UNSUPPORTED_DTYPE'):
                export.encode_npy(array)
        import io
        stream = io.BytesIO()
        np.save(stream, np.array([{'a': 1}], dtype=object), allow_pickle=True)
        with self.assertRaisesRegex(export.ExportError, 'UNSUPPORTED_NPY'):
            export.decode_npy(stream.getvalue())

    def test_invalid_schema_and_contract_fail_without_weakening(self) -> None:
        schema = json.loads((self.visual / 'export-dataset.schema.json').read_bytes())
        proposal = json.loads((self.visual / 'proposed-layers.json').read_bytes())
        export.validate_schema(schema, proposal)
        proposal['geometry']['radiusM'] = 6378137
        with self.assertRaisesRegex(export.ExportError, 'INVALID_CONTRACT'):
            export.validate_schema(schema, proposal)
        schema['properties']['version']['type'] = 'invented_type'
        with self.assertRaisesRegex(export.ExportError, 'INVALID_CONTRACT'):
            export.validate_schema(schema, proposal)


if __name__ == '__main__':
    unittest.main()
