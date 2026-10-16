"""Tests for the PT notes builder, PT basis validator and (when present) the data-driven plan/profile generators."""
import copy, pathlib, sys, tempfile, unittest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "cadgen"))
import pt_notes as pn, validate_pt_basis as vb  # noqa: E402

BASIS = yaml.safe_load(open(ROOT / "design-basis" / "examples" / "PJR-2F-PT" / "pt_basis_2F.pt.yaml", encoding="utf-8"))
TEMPLATE = yaml.safe_load(open(pn.DEFAULT_TEMPLATE, encoding="utf-8"))
STD = ROOT / "Structural-Drawing-Standards"


class Notes(unittest.TestCase):
    def test_render_is_eurocode_and_bonded(self):
        txt = pn.to_text(pn.render(TEMPLATE, BASIS))
        self.assertIn("EN 1992-1-1", txt)
        self.assertIn("BONDED", txt)
        self.assertNotRegex(txt.split("K. ASSUMPTIONS")[0], r"BS\s?\d{4}")        # no BS code in the notes themselves
        self.assertNotIn("UNBONDED", txt.upper())

    def test_missing_value_prints_tbc_and_is_listed(self):
        b = copy.deepcopy(BASIS); b["tendon"]["mu"] = None
        r = pn.render(TEMPLATE, b)
        self.assertIn("tendon.mu", r["missing"])
        self.assertIn("mu = TBC", pn.to_text(r))

    def test_unbonded_is_refused(self):
        b = copy.deepcopy(BASIS); b["system"]["type"] = "unbonded"
        with self.assertRaises(pn.PTBasisError):
            pn.render(TEMPLATE, b)

    def test_sheet_builds_and_validates(self):
        import common as c, validate_dxf as v
        with tempfile.TemporaryDirectory() as d:
            p = pn.build_sheet(pn.render(TEMPLATE, BASIS), {k: "T" for k in c.ATTRIBS}, c.load_layers(STD), pathlib.Path(d), "t")
            res = v.validate(str(p), STD)
            self.assertTrue(res["ok"], res["errors"])


class Validator(unittest.TestCase):
    def test_example_has_no_errors(self):
        r = vb.validate(BASIS)
        self.assertTrue(r["ok"], r["errors"])
        self.assertTrue(any("jacking stress" in m for m in r["info"]))

    def test_unbonded_and_bs_rejected(self):
        b = copy.deepcopy(BASIS); b["system"]["type"] = "unbonded"; b["codes"]["concrete"] = "BS 8110-1997"
        r = vb.validate(b)
        self.assertFalse(r["ok"])
        self.assertTrue(any("bonded" in e for e in r["errors"]))
        self.assertTrue(any("British Standard" in e for e in r["errors"]))

    def test_jacking_over_limit_is_error(self):
        b = copy.deepcopy(BASIS); b["strand"]["jacking_force_kn"] = 160
        self.assertFalse(vb.validate(b)["ok"])

    def test_project_code_mismatch(self):
        b = copy.deepcopy(BASIS); b["project_code"] = "PJR-2026-001"
        r = vb.validate(b, {"project": {"code": "PJR-2026-002"}})
        self.assertFalse(r["ok"])


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------- data-driven plan / profile generators (regression against the user's 2F DXFs)
import json, subprocess  # noqa: E402
sys.path.insert(0, str(ROOT / "tests"))
from dxf_signature import signature, diff  # noqa: E402
import pt_plan as pp, pt_profiles as pf  # noqa: E402

EX = ROOT / "design-basis" / "examples" / "PJR-2F-PT"
PLAN_DATA = json.load(open(EX / "pt_plan_data_2F.json", encoding="utf-8"))
PROF_DATA = json.load(open(EX / "pt_profile_data_2F.json", encoding="utf-8"))


class PlanGenerator(unittest.TestCase):
    def test_2f_plan_matches_existing_redraft(self):
        ref = ROOT / "redraft_2F_PT" / "2F_PT_Layout_Plan_REDRAFT.dxf"
        if not ref.exists():
            self.skipTest("existing 2F plan DXF not present")
        with tempfile.TemporaryDirectory() as d:
            p = pp.build(PLAN_DATA, STD, pathlib.Path(d))
            df = diff(signature(ref), signature(p))
            self.assertEqual((df["only_old"], df["only_new"]), ([], []))

    def test_strand_numbers_must_match_count(self):
        d = copy.deepcopy(PLAN_DATA); d["tendons"][0]["last"] += 1
        with self.assertRaises(pp.PlanDataError):
            pp.check_data(d)

    def test_duplicate_group_rejected(self):
        d = copy.deepcopy(PLAN_DATA); d["tendons"][1]["group"] = d["tendons"][0]["group"]
        with self.assertRaises(pp.PlanDataError):
            pp.check_data(d)

    def test_missing_field_is_not_guessed(self):
        d = copy.deepcopy(PLAN_DATA); d["tendons"][0]["length_m"] = None
        with self.assertRaises(pp.PlanDataError):
            pp.check_data(d)

    def test_symbol_for_one_strand_refused(self):
        d = copy.deepcopy(PLAN_DATA)
        t = [t for t in d["tendons"] if t["dir"] == "X"][0]; t["strands"] = 1; t["last"] = t["first"]
        with tempfile.TemporaryDirectory() as o, self.assertRaises(pp.PlanDataError):
            pp.build(d, STD, pathlib.Path(o))

    def test_schedule_csv_has_every_tendon(self):
        with tempfile.TemporaryDirectory() as o:
            pp.build(PLAN_DATA, STD, pathlib.Path(o))
            rows = open(pathlib.Path(o) / f"{PLAN_DATA['file_name']}_schedule.csv").read().strip().splitlines()
            self.assertEqual(len(rows) - 1, len(PLAN_DATA["tendons"]))


class ProfileGenerator(unittest.TestCase):
    def test_2f_profiles_match_existing_redraft(self):
        refs = {"X": ROOT / "redraft_2F_PT" / "profiles" / "2F_PT_Profiles_X_REDRAFT.dxf", "Y": ROOT / "redraft_2F_PT" / "profiles" / "2F_PT_Profiles_Y_REDRAFT.dxf"}
        if not all(p.exists() for p in refs.values()):
            self.skipTest("existing 2F profile DXFs not present")
        with tempfile.TemporaryDirectory() as o:
            self.assertEqual(pf.main(["--data", str(EX / "pt_profile_data_2F.json"), "--standards", str(STD), "--out", o, "--no-pdf"]), 0)
            for k, ref in refs.items():
                df = diff(signature(ref), signature(pathlib.Path(o) / f"{PROF_DATA['file_prefix']}_{k}.dxf"))
                self.assertEqual((df["only_old"], df["only_new"]), ([], []), k)

    def test_spacing_sum_must_match_last_chainage(self):
        p = copy.deepcopy(PROF_DATA["profiles"]["X1"]); p["stations"][3]["sp"] += 25
        with self.assertRaises(pf.ProfileDataError):
            pf.check_profile("X1", p)

    def test_curve_derived_from_stations_when_absent(self):
        p = copy.deepcopy(PROF_DATA["profiles"]["X1"]); p.pop("curve")
        b = pf.prep("X1", p, 10.0 / 250, 0.4)
        self.assertEqual(len(b["curve"]), len(p["stations"]))
