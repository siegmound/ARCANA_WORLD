from __future__ import annotations

import numpy as np
import unittest
import json
from pathlib import Path

from arcana_worldsim.r6.shellset_mesh.orbdata import make_orbdata_grids


def fixture_fields():
    domain = np.full((180, 360), 2, dtype=np.uint8)
    domain[:, :2] = 1
    age = np.zeros((180, 360), dtype=np.float64)
    age[:, 0] = 10.0
    age[:, 1] = 20.0
    return {
        "oceanic_lithosphere_age_ma": age,
        "crustal_thickness_m": np.full((180, 360), 7000.0),
        "physical_crust_domain_id": domain,
        "continental_reference_lithosphere_thickness_m": np.full((180, 360), 85000.0),
    }


class OrbDataAdapterTests(unittest.TestCase):
 def test_export_contract_units_orientation_wrap_and_domain_identity(self):
    fields = fixture_fields()
    grids, lineage = make_orbdata_grids(fields)
    self.assertAlmostEqual(grids["cArray"][50, 50], 7.0)  # m -> km; OrbData multiplies by 1000
    self.assertEqual(grids["aArray"].shape, (182, 362))
    self.assertEqual(grids["aArray"][90, 1], 10.0)  # west edge physical cell
    self.assertEqual(grids["aArray"][90, 2], 20.0)  # adjacent physical cell
    self.assertEqual(grids["aArray"][90, 0], grids["aArray"][90, 360])  # periodic halo
    self.assertEqual(grids["aArray"][0, 100], grids["aArray"][1, 100])  # north halo
    self.assertEqual(grids["aArray"][-1, 100], grids["aArray"][-2, 100])  # south halo
    self.assertEqual(grids["arcana_domain"][90, 1], 1)
    self.assertEqual(grids["arcana_domain"][90, 3], 2)
    self.assertTrue(lineage["aArray"]["physical_support_mask_sha256"])
    self.assertTrue(lineage["aArray"]["halo_mask_sha256"])
    self.assertNotIn("sArray", grids)
    self.assertNotIn("delta_ts", grids)
    self.assertEqual(lineage["continental_total_lithosphere"]["units"], "m")
    self.assertEqual(lineage["continental_total_lithosphere"]["semantic_role"],
                     "GOVERNED_REQUESTED_TOTAL_LITHOSPHERE_STRUCTURE")
    self.assertTrue(lineage["continental_total_lithosphere"]["transfer"].startswith("direct"))
    # Every input age on land is a numerical fill, never physical authority.
    self.assertEqual(grids["aArray"][90, 20], 20.0)
    self.assertEqual(lineage["domain"]["source"], "physical_crust_domain_id")


 def test_grid_exports_are_deterministic_and_require_complete_governed_inputs(self):
    fields = fixture_fields()
    one, manifest_one = make_orbdata_grids(fields)
    two, manifest_two = make_orbdata_grids(fields)
    self.assertEqual(manifest_one["replay_identity"], manifest_two["replay_identity"])
    self.assertTrue(all(np.array_equal(one[name], two[name]) for name in one))
    del fields["physical_crust_domain_id"]
    with self.assertRaisesRegex(ValueError, "missing"):
        make_orbdata_grids(fields)

 def test_governed_parent_package_and_validator_bindings(self):
    root = Path(__file__).resolve().parents[1]
    report = json.loads((root / "R6_T0_ORBDATA_ARCANA_ADAPTER_AND_SOURCE_GENERALIZATION.json").read_text())
    validator = (root / "scripts/r6_t0_fair_validate_orbdata_result.sh").read_text()
    self.assertEqual(report["shellset_source_generalization"]["required_parent_commit"],
                     "09a06ecd061f00b80a52af86e31d609ff5545a8b")
    self.assertIn("31cf4fb77e6fc12df1716805eeb4b46059ca35bbcd7b3bc305efa2e8afef3534", validator)
    self.assertIn("15dfca97b24c387af5b46c32f2b7db58154c2268", validator)
    self.assertIn("39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e", validator)
    self.assertIn("INTEROPERABILITY_GENERALIZATION", json.dumps(report))

 def test_source_patch_has_explicit_fail_closed_domain_and_total_thickness_contracts(self):
    root = Path(__file__).resolve().parents[1]
    patch = (root / "patches/shellset/R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch").read_text()
    self.assertIn("trim(filename)//'15'", patch)
    self.assertIn("trim(filename)//'16'", patch)
    self.assertIn(".neqv. arcLithosphereExists", patch)
    self.assertIn("arcanaOcean=(domainClass==1)", patch)
    self.assertIn("domainRow=INT((domainY2-pLat)/domainDY+1.50000001D0)", patch)
    self.assertIn("requestedTotalLithosphere-thickC", patch)
    # The hunk retains the stock unit-12 read; its unchanged inversion remains
    # in source context outside the patch additions.
    self.assertIn("READ (12, * )", patch)
    self.assertIn("IF (.NOT. arcanaMode) THEN", patch)
    self.assertIn("needE = (elevat == 0.0D0) .AND. (.NOT. arcanaMode)", patch)
    self.assertIn("MOD_ShellSet.f90", patch)
    self.assertIn("OrbData5.f90", patch)
    self.assertIn("MOD_Data.f90", patch)


if __name__ == "__main__":
    unittest.main()
