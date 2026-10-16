"""M0 tests: units layer, check status, code registry, shared schemas. Run: python -m unittest discover -s tests -v

The registry tests use a synthetic registry written to a temp folder. Its parameter names and values are made up
for testing and are not Eurocode values.
"""
import copy
import pathlib
import sys
import tempfile
import unittest

import yaml
from pydantic import ValidationError

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from calc_lib.core import schemas as s  # noqa: E402
from calc_lib.core import units  # noqa: E402
from calc_lib.core.registry import CodeRegistry, RegistryError  # noqa: E402
from calc_lib.core.status import CheckStatus, NotEvaluated, combine  # noqa: E402


# ------------------------------------------------------------------------------------------------ units
class Units(unittest.TestCase):
    def test_conversions_to_internal(self):
        self.assertAlmostEqual(units.to_internal("0.25 kN*m", "moment"), 250000.0)
        self.assertAlmostEqual(units.to_internal("1.2 m", "length"), 1200.0)
        self.assertAlmostEqual(units.to_internal({"value": 30, "unit": "N/mm**2"}, "pressure"), 30.0)
        self.assertAlmostEqual(units.to_internal("5 kN/m**2", "pressure"), 0.005)
        self.assertAlmostEqual(units.to_internal("25 kN/m**3", "unit_weight"), 25e-6)

    def test_bare_numbers_rejected(self):
        for bad in (12, 12.5, True):
            with self.assertRaises(units.DimensionError):
                units.require(bad, "length")

    def test_wrong_dimension_rejected(self):
        with self.assertRaises(units.DimensionError):
            units.require("10 kN", "length")
        with self.assertRaises(units.DimensionError):
            units.require("10 kN*m", "force")

    def test_mapping_rules(self):
        with self.assertRaises(units.DimensionError):
            units.parse({"value": None, "unit": "mm"})
        with self.assertRaises(units.DimensionError):
            units.parse({"value": 1, "unit": "mm", "note": "x"})
        with self.assertRaises(units.DimensionError):
            units.parse("12")
        with self.assertRaises(units.DimensionError):
            units.parse({"value": 5, "unit": "mm - 3"})
        with self.assertRaises(units.DimensionError):
            units.parse({"value": "5", "unit": "mm"})

    def test_text_is_one_number_and_one_unit(self):
        ok = {"0.002 1/mm": ("curvature", 0.002), "-3.5 mm": ("length", -3.5), "1e3 N": ("force", 1000.0),
              "140kN": ("force", 140000.0), "25 kN/m^3": ("unit_weight", 25e-6), "1 m**-1": ("curvature", 0.001),
              "0.5 dimensionless": ("dimensionless", 0.5)}
        for text, (kind, internal) in ok.items():
            self.assertAlmostEqual(units.to_internal(text, kind), internal, msg=text)

    def test_ranges_and_arithmetic_rejected(self):
        # "55-80 mm" is how the 2F PT basis records duct width; it must not become 55 - 80 mm
        for bad in ("55-80 mm", "100 mm - 20 mm", "5 mm + 2 mm", "2*3 mm", "1/3 m", "3 1/2 mm", "10 kN 2", "mm", ""):
            with self.assertRaises(units.DimensionError, msg=bad):
                units.parse(bad)

    def test_round_trip(self):
        q = units.Quantity(3.5, "kN/m")
        self.assertEqual(units.parse(units.to_dict(q)), q)
        self.assertEqual(units.from_internal(3.5, "force_per_length").to("kN/m").magnitude, 3.5)

    def test_unknown_kind(self):
        with self.assertRaises(KeyError):
            units.require("1 m", "velocity_of_light")


# ------------------------------------------------------------------------------------------------ status
class Status(unittest.TestCase):
    def test_empty_set_is_not_evaluated(self):
        self.assertIs(combine([]), CheckStatus.NOT_EVALUATED)

    def test_not_evaluated_is_never_pass(self):
        self.assertIs(combine([CheckStatus.PASS, CheckStatus.NOT_EVALUATED]), CheckStatus.NOT_EVALUATED)

    def test_fail_dominates(self):
        self.assertIs(combine([CheckStatus.PASS, CheckStatus.BLOCKED, CheckStatus.FAIL]), CheckStatus.FAIL)

    def test_all_pass(self):
        self.assertIs(combine([CheckStatus.PASS, CheckStatus.PASS]), CheckStatus.PASS)


# ------------------------------------------------------------------------------------------------ registry
def _entry(value, status="UNVERIFIED", ndp=False, kind="dimensionless", unit="dimensionless"):
    e = {"description": "synthetic test parameter", "kind": kind, "unit": unit, "value": value, "ndp": ndp,
         "source_ref": "T.1", "status": status}
    if status == "VERIFIED":
        e.update(verified_by="Test Engineer", verified_date="2026-10-16")
    return e


BASE = {
    "file_version": 1, "standard": "TEST-STD", "edition": "2000", "national_annex": "CEN_RECOMMENDED",
    "parameters": {
        "p.ndp": _entry(0.5, "VERIFIED", ndp=True),
        "p.ndp_not_in_na": _entry(0.7, "VERIFIED", ndp=True),
        "p.fixed": _entry(2.0, "VERIFIED"),
        "p.unverified": _entry(0.9),
        "p.empty": _entry(None),
        "p.stress": _entry(400, "VERIFIED", kind="pressure", unit="MPa"),
    },
}
NA_XX = {
    "file_version": 3, "standard": "TEST-STD", "edition": "2000", "national_annex": "NA", "country": "XX",
    "na_reference": "XX NA to TEST-STD:2000",
    "parameters": {"p.ndp": _entry(0.6, "VERIFIED", ndp=True)},
}


class Registry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, data):
        (self.dir / name).write_text(yaml.safe_dump(data), encoding="utf-8")

    def load(self, base=BASE, na=NA_XX):
        self.write("base.yaml", base)
        if na is not None:
            self.write("na.yaml", na)
        return CodeRegistry.load(self.dir)

    def test_verified_value_returned_with_unit(self):
        v = self.load().select("TEST-STD", "2000", "CEN_RECOMMENDED")
        self.assertEqual(v.require("p.ndp").magnitude, 0.5)
        self.assertEqual(units.to_internal(v.require("p.stress"), "pressure"), 400.0)
        self.assertEqual(v.source_ref("p.fixed"), "TEST-STD:2000 T.1")

    def test_unverified_empty_and_missing_are_not_evaluated(self):
        v = self.load().select("TEST-STD", "2000", "CEN_RECOMMENDED")
        for pid in ("p.unverified", "p.empty", "p.not_there"):
            with self.assertRaises(NotEvaluated) as cm:
                v.require(pid)
            self.assertEqual(cm.exception.missing, (pid,))

    def test_na_overlay(self):
        v = self.load().select("TEST-STD", "2000", "NA", "XX")
        self.assertEqual(v.require("p.ndp").magnitude, 0.6)
        self.assertEqual(v.require("p.fixed").magnitude, 2.0)          # not an NDP: CEN value applies
        self.assertEqual(v.source_ref("p.ndp"), "XX NA to TEST-STD:2000 T.1")
        with self.assertRaises(NotEvaluated):
            v.require("p.ndp_not_in_na")                                 # NDP missing from NA: no fallback
        self.assertIn("NA[XX] v1+v3", v.version)

    def test_selection_failures(self):
        reg = self.load()
        cases = [("TEST-STD", None, "CEN_RECOMMENDED", None), ("TEST-STD", "1999", "CEN_RECOMMENDED", None),
                 ("TEST-STD", "2000", "UNRESOLVED", None), ("TEST-STD", "2000", "NA", None),
                 ("TEST-STD", "2000", "NA", "YY")]
        for args in cases:
            with self.assertRaises(NotEvaluated, msg=str(args)):
                reg.select(*args)

    def test_select_for_project(self):
        reg = self.load()
        db = {"standards": [{"id": "TEST-STD", "edition": "2000"}],
              "national_annex": {"mode": "CEN_RECOMMENDED"}}
        self.assertEqual(reg.select_for_project(db, "TEST-STD").require("p.fixed").magnitude, 2.0)
        for change in ({"national_annex": {"mode": "UNRESOLVED"}},
                       {"standards": [{"id": "TEST-STD", "edition": None}]},
                       {"standards": [{"id": "TEST-STD", "edition": "2000"}, {"id": "TEST-STD", "edition": "2010"}]},
                       {"standards": []}):
            with self.assertRaises(NotEvaluated, msg=str(change)):
                reg.select_for_project({**db, **change}, "TEST-STD")

    def test_version_changes_with_content(self):
        v1 = self.load(na=None).select("TEST-STD", "2000", "CEN_RECOMMENDED").version
        changed = copy.deepcopy(BASE)
        changed["parameters"]["p.fixed"]["value"] = 2.5
        v2 = self.load(base=changed, na=None).select("TEST-STD", "2000", "CEN_RECOMMENDED").version
        self.assertNotEqual(v1, v2)

    def test_invalid_files_rejected(self):
        bad_verified = copy.deepcopy(BASE)
        bad_verified["parameters"]["p.fixed"].pop("verified_by")
        bad_unit = copy.deepcopy(BASE)
        bad_unit["parameters"]["p.stress"]["unit"] = "kN"
        na_unknown = copy.deepcopy(NA_XX)
        na_unknown["parameters"]["p.new"] = _entry(1.0, "VERIFIED")
        na_no_ref = copy.deepcopy(NA_XX)
        na_no_ref["na_reference"] = None
        for base, na in ((bad_verified, None), (bad_unit, None), (BASE, na_unknown), (BASE, na_no_ref)):
            for f in self.dir.glob("*.yaml"):
                f.unlink()
            with self.assertRaises(RegistryError):
                self.load(base, na)

    def test_duplicate_and_orphan_files_rejected(self):
        self.write("a.yaml", BASE)
        self.write("b.yaml", BASE)
        with self.assertRaises(RegistryError):
            CodeRegistry.load(self.dir)
        (self.dir / "a.yaml").unlink()
        (self.dir / "b.yaml").unlink()
        self.write("na.yaml", NA_XX)
        with self.assertRaises(RegistryError):
            CodeRegistry.load(self.dir)

    def test_repo_registry_loads(self):
        reg = CodeRegistry.load(ROOT / "config" / "code_registry")
        view = reg.select("EN 1992-1-1", "2004", "CEN_RECOMMENDED")
        self.assertTrue(view.version.startswith("EN 1992-1-1:2004 CEN"))


# ------------------------------------------------------------------------------------------------ schemas
def _check(**kw):
    base = dict(id="CHK-1", check_type="test_check", element_id="BB1", limit_state="ULS", status="PASS",
                value="120 kN", limit="150 kN", utilisation=0.8, method_ref="method X", registry_version="reg v1")
    base.update(kw)
    return s.CheckResult(**base)


def _tendon(**kw):
    base = dict(mark="T1", strand_count=4, strand_ref="strand.main", duct_width="70 mm", duct_height="20 mm",
                stressing="start", plan_path=[{"x": 0, "y": 0}, {"x": 8000, "y": 0}],
                profile=[{"chainage": "0 mm", "height": "150 mm", "kind": "anchor"},
                         {"chainage": "4 m", "height": "40 mm", "kind": "low"},
                         {"chainage": "8000 mm", "height": "150 mm", "kind": "anchor"}])
    base.update(kw)
    return s.Tendon(**base)


class Schemas(unittest.TestCase):
    def test_typed_quantity_fields(self):
        col = s.Column(id="C1", source="extracted_from_cad", centre={"x": 0, "y": 0}, shape="rectangular",
                       b="400 mm", h="0.6 m")
        self.assertEqual(units.to_internal(col.h, "length"), 600.0)
        for bad in (400, "400 kN"):
            with self.assertRaises(ValidationError):
                s.Column(id="C1", source="extracted_from_cad", centre={"x": 0, "y": 0}, shape="rectangular",
                         b=bad, h="600 mm")

    def test_column_shape_rules(self):
        with self.assertRaises(ValidationError):
            s.Column(id="C1", source="engineer_entered", centre={"x": 0, "y": 0}, shape="circular", b="400 mm",
                     h="400 mm")

    def test_models_are_frozen(self):
        t = _tendon()
        with self.assertRaises(ValidationError):
            t.mark = "T2"

    def test_json_round_trip_and_hash(self):
        t = _tendon()
        again = s.Tendon.model_validate_json(t.model_dump_json())
        self.assertEqual(again, t)
        self.assertEqual(s.content_hash(again), s.content_hash(t))
        self.assertNotEqual(s.content_hash(_tendon(strand_count=5)), s.content_hash(t))

    def test_json_schema_generates(self):
        for model in (s.GeometryModel, s.AnalysisResults, s.Tendon, s.LossResult, s.CheckResult,
                      s.ReinforcementGroup):
            self.assertIn("properties", model.model_json_schema())

    def test_geometry_rules(self):
        slab = {"id": "S1", "source": "extracted_from_cad", "thickness": "250 mm",
                "outline": [{"x": 0, "y": 0}, {"x": 9000, "y": 0}, {"x": 9000, "y": 8000}]}
        g = s.GeometryModel(project_code="P", floor_label="2F", slabs=[slab])
        self.assertEqual(g.review.state, "UNREVIEWED")
        with self.assertRaises(ValidationError):
            s.GeometryModel(project_code="P", floor_label="2F", slabs=[slab, slab])
        with self.assertRaises(ValidationError):
            s.GeometryModel(project_code="P", floor_label="2F", review={"state": "CONFIRMED"})
        with self.assertRaises(ValidationError):
            s.SlabRegion(**{**slab, "outline": [{"x": 0, "y": 0}, {"x": 0, "y": 0}, {"x": 1, "y": 1}]})

    def test_analysis_result_references(self):
        src = {"adapter": "test", "adapter_version": "0", "files": [{"name": "x.csv", "sha256": "a" * 64}]}
        cases = [{"name": "DL", "kind": "self_weight"}, {"name": "LL", "kind": "imposed"}]
        ok = s.AnalysisResults(source=src, load_cases=cases,
                               combinations=[{"name": "U1", "limit_state": "ULS", "factors": {"DL": 1.0, "LL": 1.0}}],
                               strip_forces=[{"strip_id": "CS1", "station": "0 m", "case": "U1",
                                              "moment": "10 kN*m", "shear": "5 kN"}])
        self.assertEqual(len(ok.strip_forces), 1)
        with self.assertRaises(ValidationError):
            s.AnalysisResults(source=src, load_cases=cases,
                              combinations=[{"name": "U1", "limit_state": "ULS", "factors": {"WL": 1.0}}])
        with self.assertRaises(ValidationError):
            s.AnalysisResults(source=src, load_cases=cases,
                              strip_forces=[{"strip_id": "CS1", "station": "0 m", "case": "U9",
                                             "moment": "10 kN*m", "shear": "5 kN"}])
        with self.assertRaises(ValidationError):
            s.AnalysisResults(source={**src, "files": []}, load_cases=cases)

    def test_tendon_profile_rules(self):
        p = _tendon().profile
        with self.assertRaises(ValidationError):
            _tendon(profile=[p[0], p[2], p[1]])                         # chainage not increasing
        with self.assertRaises(ValidationError):
            _tendon(profile=[p[0], p[1]])                               # does not end at an anchor
        with self.assertRaises(ValidationError):
            _tendon(profile=[{**p[0].model_dump(mode="json"), "chainage": "1 m"}, p[1], p[2]])

    def test_check_result_pass_and_fail_rules(self):
        self.assertIs(_check().status, CheckStatus.PASS)
        self.assertIs(_check(status="FAIL", utilisation=1.2).status, CheckStatus.FAIL)
        bad = [dict(registry_version=None), dict(method_ref=None), dict(limit=None), dict(utilisation=1.01),
               dict(status="FAIL", utilisation=0.9), dict(limit="150 kN*m"), dict(utilisation=float("nan")),
               dict(missing=["x"])]
        for kw in bad:
            with self.assertRaises(ValidationError, msg=str(kw)):
                _check(**kw)

    def test_check_result_incomplete_rules(self):
        ne = _check(status="NOT EVALUATED", value=None, limit=None, utilisation=None, registry_version=None,
                    missing=["gamma_c.persistent"])
        self.assertIs(ne.status, CheckStatus.NOT_EVALUATED)
        for st in ("NOT EVALUATED", "BLOCKED", "WARNING", "ENGINEER REVIEW REQUIRED"):
            with self.assertRaises(ValidationError, msg=st):
                _check(status=st, value=None, limit=None, utilisation=None)

    def test_check_inputs_carry_source(self):
        c = _check(inputs={"fck": {"value": "30 MPa", "source": "design_basis", "ref": "materials.C1"}})
        self.assertIs(c.inputs["fck"].source, s.ValueSource.DESIGN_BASIS)

    def test_loss_result_rules(self):
        with self.assertRaises(ValidationError):
            s.LossResult(tendon_mark="T1", status="NOT EVALUATED")
        with self.assertRaises(ValidationError):
            s.LossResult(tendon_mark="T1", status="EVALUATED", stations=[{"chainage": "0 m"}])
        s.LossResult(tendon_mark="T1", status="NOT EVALUATED", missing=["tendon.mu"])

    def test_reinforcement_needs_quantity_or_spacing(self):
        base = dict(mark="B01", element_id="BB1", design_revision="P01", bar_diameter="16 mm", grade="B500B",
                    orientation="X", layer="B1", shape_code="00", bar_length="6 m", cover="30 mm")
        s.ReinforcementGroup(**base, spacing="200 mm")
        with self.assertRaises(ValidationError):
            s.ReinforcementGroup(**base)


if __name__ == "__main__":
    unittest.main()
