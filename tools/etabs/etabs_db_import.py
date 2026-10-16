#!/usr/bin/env python3
"""Import and check an ETABS/SAFE model exported as a SQLite .db (the user's own exporter, 'ExporterVersion' in table _ModelInfo).

Usage: python tools/etabs/etabs_db_import.py <model.db> --out <dir> --model-id <id> [--members members.csv] [--expected expected_cases.yaml]
                                              [--design-basis db.yaml] [--no-raw-copy]

Layout seen in ONE real file (GDT_CleanV3.db, ETABS 22.1.0, ExporterVersion 2, IncludesResults = No): tables named like the ETABS
database tables ('Frame_Assignments_Summary', 'Load_Combination_Definitions', ...) plus _ModelInfo (Key/Value) and _Tables (status per table).
That file holds the MODEL DEFINITION only - it contains NO analysis results (no joint reactions, forces or displacements). So this tool checks
what a definition export can show: provenance, units, table export status, referential integrity (sections, materials, joints, load names),
duplicates, expected load cases / combination factors, member mapping, supports, and the design codes the model uses.
It does NOT check equilibrium, superposition of results or any force: results checks stay NOT CHECKED until a .db with results (or the
table export read by etabs_import.py) is supplied. A table layout for results in this exporter has not been seen and is not guessed.
Import success does not show the model is correct. SAFE exports have not been seen at all (not verified).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import pathlib
import shutil
import sqlite3
import sys

import yaml

OK, FAIL, NOTC, WARN, INFO = "PASS", "FAIL", "NOT CHECKED", "WARNING", "INFO"
LEN_TO_M = {"mm": 0.001, "m": 1.0, "cm": 0.01, "in": 0.0254, "ft": 0.3048}
RESULT_HINTS = ("reaction", "displacement", "frame_forces", "element_forces", "joint_displ", "story_drift", "modal_participating")


def nm(v):
    """Normalise identifiers that the exporter stores as REAL (1790.0 -> '1790')."""
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


class DB:
    def __init__(self, path):
        self.c = sqlite3.connect(f"file:{pathlib.Path(path).as_posix()}?mode=ro", uri=True)
        self.c.row_factory = sqlite3.Row
        self.names = {r[0] for r in self.c.execute("select name from sqlite_master where type='table'")}

    def has(self, t):
        return t in self.names

    def rows(self, t):
        return [dict(r) for r in self.c.execute(f'select * from "{t}"')] if t in self.names else None


def units_of(d):
    info = {r["Key"]: r["Value"] for r in d.rows("_ModelInfo") or []}
    return info


def run(db_path, out, model_id, members_csv=None, expected_yaml=None, design_basis=None, copy_raw=True) -> dict:
    db_path, out = pathlib.Path(db_path), pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with open(db_path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    if copy_raw:
        (out / "raw").mkdir(exist_ok=True)
        shutil.copyfile(db_path, out / "raw" / db_path.name)
    d = DB(db_path)
    log = {"model_id": model_id, "source_type": "sqlite .db model export", "imported_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "provenance": {"file": db_path.name, "sha256": h.hexdigest(), "bytes": db_path.stat().st_size}, "issues": [], "checks": [],
           "disclaimer": "A completed import does not show the analysis model is correct. Only the checks listed below were performed; this file holds a model definition, not results."}
    add = lambda cid, name, st, det: log["checks"].append({"id": cid, "name": name, "status": st, "detail": det})
    issue = lambda lvl, msg: log["issues"].append({"level": lvl, "msg": msg})

    # M1 provenance, units, results flag
    info = units_of(d)
    prog = (d.rows("Program_Control") or [{}])[0]
    pinfo = (d.rows("Project_Information") or [{}])[0]
    log["provenance"].update({"program": prog.get("ProgramName"), "version": prog.get("Version"), "model_file_recorded": info.get("ModelFile"),
                              "exported_at": info.get("ExportedAt"), "exporter_version": info.get("ExporterVersion"), "data_units": info.get("DataUnits"),
                              "present_units": info.get("PresentUnits"), "program_current_units": prog.get("CurrUnits"),
                              "project_info": {k: pinfo.get(k) for k in ("ClientName", "ProjectName", "ProjectNum", "Engineer", "Checker", "ModelName", "RevisionNum")}})
    miss = [k for k in ("ModelFile", "DataUnits", "ExportedAt", "IncludesResults") if k not in info]
    if not d.has("_ModelInfo") or miss:
        add("M1", "export metadata present (units, results flag, model file)", FAIL, f"missing: {miss or '_ModelInfo table'}")
    else:
        add("M1", "export metadata present (units, results flag, model file)", OK, f"{prog.get('ProgramName')} {prog.get('Version')}; data units {info['DataUnits']}")
    du = info.get("DataUnits", "")
    length_unit = next((u for u in du.split("_") if u in LEN_TO_M), None)
    if length_unit is None:
        add("M2", "data length unit recognised", FAIL, f"DataUnits '{du}'")
        lf = None
    else:
        lf = LEN_TO_M[length_unit]
        add("M2", "data length unit recognised", OK, f"{du}: lengths in {length_unit} (x{lf:g} to m)")
    cu = prog.get("CurrUnits")
    if cu and du and [t.strip() for t in str(cu).split(",")][:2] != du.split("_")[:2]:
        issue(WARN, f"Program_Control.CurrUnits is '{cu}' but the export's DataUnits is '{du}'. Values are read in DataUnits; confirm with the exporter's author that this is intended")
    log["provenance"]["includes_results"] = info.get("IncludesResults")
    hint_tables = sorted(t for t in d.names if any(k in t.lower() for k in RESULT_HINTS))
    if info.get("IncludesResults", "No") != "Yes" or not hint_tables:
        add("M3", "analysis results present", NOTC, "IncludesResults = %s; no results tables found. Equilibrium, superposition and force checks cannot run" % info.get("IncludesResults"))
    else:
        add("M3", "analysis results present", WARN, f"results tables {hint_tables} exist but their layout has not been seen; NOT imported")

    # M4 table export status
    tabs = d.rows("_Tables") or []
    bad = [t for t in tabs if str(t.get("Status")) != "OK"]
    for t in bad:
        issue(WARN, f"exporter could not write table '{t['TableName']}': {t['Status']}")
    add("M4", "every exported table has status OK", WARN if bad else OK,
        f"{len(bad)} of {len(tabs)} tables failed in the exporter: {[t['TableName'] for t in bad]}" if bad else f"{len(tabs)} tables")

    def need(*ts):
        m = [t for t in ts if not d.has(t)]
        return m

    # M5 referential integrity
    probs, skipped = [], []
    sect = {r["Name"] for r in d.rows("Frame_Section_Property_Definitions_Summary") or []}
    mats = {r["Material"] for r in d.rows("Material_Properties_General") or []}
    frames = d.rows("Frame_Assignments_Summary")
    if frames is None or not sect:
        skipped.append("frame sections")
    else:
        unk = sorted({r["AnalysisSect"] for r in frames if r["AnalysisSect"] not in sect and r["Type"] != "Null"})
        if unk:
            probs.append(f"{len(unk)} frame section(s) not defined: {unk[:4]}")
    secs = d.rows("Frame_Section_Property_Definitions_Summary")
    if secs and mats:
        unk = sorted({r["Material"] for r in secs if r["Material"] and r["Material"] not in mats})
        if unk:
            probs.append(f"section materials not defined: {unk[:4]}")
    else:
        skipped.append("section materials")
    pts = d.rows("Point_Object_Connectivity")
    ptset = {nm(r["UniqueName"]) for r in pts or []}
    if pts:
        for t in ("Beam_Object_Connectivity", "Column_Object_Connectivity", "Null_Line_Object_Connectivity"):
            rs = d.rows(t)
            if rs is None:
                skipped.append(t)
                continue
            m = sum(1 for r in rs if nm(r["UniquePtI"]) not in ptset or nm(r["UniquePtJ"]) not in ptset)
            if m:
                probs.append(f"{t}: {m} member(s) reference a joint that does not exist")
        for r in d.rows("Joint_Assignments_Restraints") or []:
            if nm(r["UniqueName"]) not in ptset:
                probs.append(f"restraint at undefined joint {nm(r['UniqueName'])}")
                break
    else:
        skipped.append("joint references")
    pats = {r["Name"] for r in d.rows("Load_Pattern_Definitions") or []}
    cases = {r["Name"] for r in d.rows("Load_Case_Definitions_Summary") or []}
    for t in ("Load_Case_Definitions_Linear_Static", "Load_Case_Definitions_Nonlinear_Static"):
        for r in d.rows(t) or []:
            if r.get("LoadType") == "Load" and r.get("LoadName") and r["LoadName"] not in pats:
                probs.append(f"{t}: case '{r['Name']}' uses undefined load pattern '{r['LoadName']}'")
                break
    combos = d.rows("Load_Combination_Definitions") or []
    comb_names = {r["Name"] for r in combos}
    known = pats | cases | comb_names
    undefined = sorted({r["LoadName"] for r in combos if r["LoadName"] and r["LoadName"] not in known})
    if undefined:
        probs.append(f"{len(undefined)} combination term(s) refer to undefined cases/combinations: {undefined[:4]}")
    if frames:
        frame_story = {(r["Story"], nm(r["Label"])) for r in frames}
        stories = {r["Story"] for r in d.rows("Story_Definitions") or []}
        if stories and any(r["Story"] not in stories for r in frames):
            probs.append("frames on stories not in Story_Definitions")
    add("M5", "referential integrity (sections, materials, joints, load names, stories)", FAIL if probs else OK,
        "; ".join(probs) or "no broken references" + (f" (skipped: {skipped})" if skipped else ""))
    if skipped and not probs:
        log["checks"][-1]["detail"] += ""

    # M6 duplicates
    dup = []
    if frames:
        u = [nm(r["UniqueName"]) for r in frames]
        if len(u) != len(set(u)):
            dup.append("duplicate frame UniqueName")
        lab = [(r["Story"], nm(r["Label"])) for r in frames if r["Type"] != "Null"]
        if len(lab) != len(set(lab)):
            dup.append("duplicate (story, label) among beams/columns")
    if pts and len(ptset) != len(pts):
        dup.append("duplicate joint UniqueName")
    if len(comb_names) and len({(r["Name"], r["LoadName"]) for r in combos}) != len(combos):
        dup.append("a combination lists the same case twice")
    add("M6", "no duplicate identifiers", FAIL if dup else OK, "; ".join(dup) or "none")

    # M7 supports
    rest = d.rows("Joint_Assignments_Restraints")
    springs = d.rows("Joint_Assignments_Springs")
    if rest is None:
        add("M7", "model has supports", NOTC, "no restraint table")
    else:
        add("M7", "model has supports", OK if (rest or springs) else FAIL, f"{len(rest)} restrained joints, {len(springs or [])} spring joints")

    # M8 expected cases / combination factors
    exp = yaml.safe_load(pathlib.Path(expected_yaml).read_text(encoding="utf-8")) if expected_yaml else None
    if exp:
        want = [c["name"] for c in exp.get("cases", [])] + [c["name"] for c in exp.get("combos", [])]
        missing = [w for w in want if w not in cases | comb_names]   # analysis cases / combinations, not bare load patterns
        add("M8", "expected load cases/combinations defined", FAIL if missing else OK, f"missing: {missing}" if missing else f"all {len(want)} defined")
        defs = {}
        for r in combos:
            defs.setdefault(r["Name"], {})[r["LoadName"]] = r["SF"]
        pr = []
        for c in exp.get("combos", []):
            got = defs.get(c["name"])
            if got is None:
                pr.append(f"{c['name']}: not defined")
            elif {k: float(v) for k, v in c["terms"].items()} != {k: float(v) for k, v in got.items()}:
                pr.append(f"{c['name']}: model {got} != expected {c['terms']}")
        add("M9", "combination factors equal the expected (design-basis) factors", FAIL if pr else (OK if exp.get("combos") else NOTC), "; ".join(pr) or "all match")
    else:
        add("M8", "expected load cases/combinations defined", NOTC, "no expected_cases.yaml")
        add("M9", "combination factors equal the expected (design-basis) factors", NOTC, "no expected_cases.yaml")

    # M10 member mapping
    if members_csv and frames:
        with open(members_csv, newline="", encoding="utf-8-sig") as fh:
            ids = {m["etabs_label"] for m in csv.DictReader(fh)}
        labs = {nm(r["Label"]) for r in frames if r["Type"] in ("Beam", "Column", "Brace")}
        un, nr = sorted(labs - ids), sorted(ids - labs)
        add("M10", "every project member id exists in the model", FAIL if nr else OK, f"in members.csv but not in the model: {nr[:6]}" if nr else f"{len(ids)} mapped")
        add("M10b", "model members not in members.csv", INFO, f"{len(un)} of {len(labs)} beams/columns are not listed in members.csv (expected if members.csv is a subset)")
    else:
        add("M10", "every project member id exists in the model", NOTC, "no members.csv")

    # M11 design codes vs design basis
    codes = {k: prog.get(k) for k in ("StlFrmCode", "CompBmCode", "CompColCode", "ConcFrmCode", "ConcSlbCode", "ShrWallCode")}
    log["design_codes_in_model"] = codes
    if design_basis:
        dbd = yaml.safe_load(pathlib.Path(design_basis).read_text(encoding="utf-8"))
        ids = " ".join(str(s.get("id", "")) for s in dbd.get("standards", []))
        notes = []
        if "EN 1992" in ids and "Eurocode 2" not in str(codes["ConcFrmCode"]):
            notes.append(f"concrete design code in model is '{codes['ConcFrmCode']}', design basis lists EN 1992")
        if "EN 1993" in ids and "EN 1993" not in str(codes["StlFrmCode"]):
            notes.append(f"steel design code in model is '{codes['StlFrmCode']}', design basis lists EN 1993")
        gen = {k: v for k, v in codes.items() if v and ("2004" in v or "2005" in v)}
        if gen:
            notes.append("model codes are dated 2004/2005 (1st-generation Eurocode editions); compare with the generation recorded in the design basis")
        if any(c and "AISC" in c for c in codes.values()):
            notes.append(f"a non-Eurocode code is selected in the model: {[k for k, v in codes.items() if v and 'AISC' in v]}")
        add("M11", "model design codes consistent with design basis standards", WARN if notes else OK, "; ".join(notes) or "consistent at family level")
    else:
        add("M11", "model design codes consistent with design basis standards", NOTC, "no design basis given; codes recorded in the log")

    # inventory + outputs
    inv = {"stories": len(d.rows("Story_Definitions") or []), "joints": len(pts or []), "frames": {k: sum(1 for r in frames or [] if r["Type"] == k) for k in ("Beam", "Column", "Brace", "Null")},
           "areas_floor": len(d.rows("Floor_Object_Connectivity") or []), "walls": len(d.rows("Wall_Object_Connectivity") or []), "materials": sorted(mats),
           "frame_sections": len(sect), "load_patterns": sorted(pats), "load_cases": len(cases), "combinations": len(comb_names),
           "combination_types": {t: len({r["Name"] for r in combos if r["Type"] == t}) for t in {r["Type"] for r in combos if r["Type"]}}}
    (out / "model_inventory.json").write_text(json.dumps(inv, indent=2), encoding="utf-8")
    with open(out / "frames.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["model_id", "unique_name", "label", "story", "type", "length_m", "section", "unit_length_source"])
        for r in frames or []:
            w.writerow([model_id, nm(r["UniqueName"]), nm(r["Label"]), r["Story"], r["Type"], round(r["Length"] * lf, 4) if lf and r["Length"] is not None else "", r["AnalysisSect"], length_unit])
    with open(out / "load_definitions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["model_id", "combination", "type", "term", "factor"])
        cur = None
        for r in combos:
            w.writerow([model_id, r["Name"], r["Type"] or "", r["LoadName"], r["SF"]])
    fails = [c for c in log["checks"] if c["status"] == FAIL]
    log["summary"] = {"checks_pass": sum(c["status"] == OK for c in log["checks"]), "checks_fail": len(fails), "checks_warning": sum(c["status"] == WARN for c in log["checks"]),
                      "checks_not_checked": sum(c["status"] == NOTC for c in log["checks"]), "model_definition_usable": not fails,
                      "ready_for_calculations": False,
                      "reason_not_ready": "export contains no analysis results" if info.get("IncludesResults", "No") != "Yes" else "results layout of this exporter not yet supported"}
    (out / "import_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    prov = {"analysis_provenance": {"software": f"{prog.get('ProgramName')} {prog.get('Version')}", "model_file": info.get("ModelFile"),
                                    "run_date": None, "export_files": [db_path.name], "export_sha256": {db_path.name: h.hexdigest()},
                                    "note": "run_date is not in the export; results not included"}}
    (out / "analysis_provenance.proposed.yaml").write_text("# PROPOSED - review, then paste into the design basis. Not applied automatically.\n" + yaml.safe_dump(prov, sort_keys=False), encoding="utf-8")
    L = [f"# ETABS/SAFE .db import report - {model_id}", "", f"Model definition usable: **{'YES' if log['summary']['model_definition_usable'] else 'NO'}** | Ready for calculations: **NO** ({log['summary']['reason_not_ready']})",
         "", "> " + log["disclaimer"], "", "## Checks", "| Id | Check | Status | Detail |", "|---|---|---|---|"]
    L += [f"| {c['id']} | {c['name']} | {c['status']} | {str(c['detail']).replace('|', '/')} |" for c in log["checks"]]
    if log["issues"]:
        L += ["", "## Issues"] + [f"- **{i['level']}** {i['msg']}" for i in log["issues"]]
    L += ["", "## Inventory", "```json", json.dumps(inv, indent=1), "```"]
    (out / "import_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    d.c.close()
    return log


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model-id", required=True)
    ap.add_argument("--members")
    ap.add_argument("--expected")
    ap.add_argument("--design-basis")
    ap.add_argument("--no-raw-copy", action="store_true")
    ns = ap.parse_args(argv)
    log = run(ns.db, ns.out, ns.model_id, ns.members, ns.expected, ns.design_basis, not ns.no_raw_copy)
    print(json.dumps(log["summary"], indent=2))
    return 0 if log["summary"]["model_definition_usable"] else 1


if __name__ == "__main__":
    sys.exit(main())
