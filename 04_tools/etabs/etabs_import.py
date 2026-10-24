#!/usr/bin/env python3
"""Import ETABS / SAFE exported tables (XLSX or CSV), normalise, and run completeness / mapping / consistency checks.

Usage:
  python 04_tools/etabs/etabs_import.py <export.xlsx|.csv> [more files] --out <dir> --model-id <id>
      [--model-file NAME] [--run-date DD-MMM-YYYY] [--software "ETABS 21.x"] [--members members.csv]
      [--expected expected_cases.yaml] [--hand-totals hand_totals.yaml] [--assume-units kN,m] [--use <tables...>]

Status: written against the documented ETABS 'Export Tables to Excel/CSV' layout (row 1 'TABLE:  <name>', row 2 headers,
row 3 units, then data). NOT yet verified against a real export from the user's ETABS/SAFE version - format assumptions are
listed in references/etabs-safe-import.md. Tables or columns that do not match are reported, never guessed.

An import that completes is NOT evidence that the analysis model is correct. The log says so, and records what was and
was not checked. Raw files are copied unchanged (with SHA-256) before anything is derived.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import pathlib
import re
import shutil
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

FORCE = {"N": 0.001, "kN": 1.0, "MN": 1000.0, "kgf": 0.00980665, "tonf": 9.80665, "kip": 4.4482216, "lb": 0.00444822, "lbf": 0.00444822}
LENGTH = {"mm": 0.001, "cm": 0.01, "m": 1.0, "ft": 0.3048, "in": 0.0254}
OK, FAIL, NOTC, WARN = "PASS", "FAIL", "NOT CHECKED", "WARNING"

# table registry: normalised table name -> (kind, required columns, force cols, moment cols, length cols)
REGISTRY = {
    "joint reactions": ("reactions", ["Output Case", "FX", "FY", "FZ", "MX", "MY", "MZ"], ["FX", "FY", "FZ"], ["MX", "MY", "MZ"], []),
    "base reactions": ("base", ["Output Case", "FX", "FY", "FZ", "MX", "MY", "MZ"], ["FX", "FY", "FZ"], ["MX", "MY", "MZ"], ["X", "Y", "Z"]),
    "element forces - columns": ("forces", ["Output Case", "Station", "P", "V2", "V3", "T", "M2", "M3"], ["P", "V2", "V3"], ["T", "M2", "M3"], ["Station"]),
    "element forces - beams": ("forces", ["Output Case", "Station", "P", "V2", "V3", "T", "M2", "M3"], ["P", "V2", "V3"], ["T", "M2", "M3"], ["Station"]),
    "element forces - braces": ("forces", ["Output Case", "Station", "P", "V2", "V3", "T", "M2", "M3"], ["P", "V2", "V3"], ["T", "M2", "M3"], ["Station"]),
    "element forces - frames": ("forces", ["Output Case", "Station", "P", "V2", "V3", "T", "M2", "M3"], ["P", "V2", "V3"], ["T", "M2", "M3"], ["Station"]),
    "load combinations": ("combos", ["Name", "Scale Factor"], [], [], []),
    "program control": ("program", [], [], [], []),
}
MEMBER_ID_COLS = ["Unique Name", "Column", "Beam", "Brace", "Frame", "Label"]


# --------------------------------------------------------------------------- units
def unit_factor(token: str) -> tuple[float, str] | None:
    """Return (factor to kN/m basis, normalised unit) or None if the token is not a recognised unit."""
    t = token.strip()
    if t in FORCE:
        return FORCE[t], "kN"
    if t in LENGTH:
        return LENGTH[t], "m"
    m = re.fullmatch(r"([A-Za-z]+)-([A-Za-z]+)", t)
    if m and m[1] in FORCE and m[2] in LENGTH:
        return FORCE[m[1]] * LENGTH[m[2]], "kN-m"
    return None


# --------------------------------------------------------------------------- parsing
def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _is_num(v) -> bool:
    if isinstance(v, (int, float)):
        return True
    try:
        float(str(v).strip())
        return True
    except ValueError:
        return False


def _table_from_rows(rows: list[list], fallback_name: str, src: str) -> dict | None:
    rows = [r for r in rows]
    while rows and all(v in (None, "") for v in rows[0]):
        rows.pop(0)
    if not rows:
        return None
    first = str(rows[0][0] or "")
    if first.upper().startswith("TABLE:"):
        name, rows = first.split(":", 1)[1].strip(), rows[1:]
    else:
        name = fallback_name
    if not rows:
        return None
    header = [str(v).strip() if v is not None else "" for v in rows[0]]
    body = rows[1:]
    units = None
    if body:
        cand = [("" if v is None else str(v).strip()) for v in body[0]]
        nonempty = [v for v in cand if v]
        if nonempty and all(unit_factor(v) for v in nonempty) and not any(_is_num(v) for v in nonempty):
            units = dict(zip(header, cand))
            body = body[1:]
    data = [dict(zip(header, r)) for r in body if any(v not in (None, "") for v in r)]
    return {"name": name, "key": _norm(name), "header": header, "units": units, "rows": data, "source": src}


def parse_file(path: pathlib.Path) -> list[dict]:
    tables = []
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook
        wb = load_workbook(path, data_only=True, read_only=True)
        for ws in wb.worksheets:
            t = _table_from_rows([list(r) for r in ws.iter_rows(values_only=True)], ws.title, f"{path.name}:{ws.title}")
            if t:
                tables.append(t)
    elif path.suffix.lower() == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as fh:
            all_rows = [r for r in csv.reader(fh)]
        # a CSV may hold several tables separated by a blank row, each starting with 'TABLE:'
        block: list[list] = []
        blocks = []
        for r in all_rows:
            if r and str(r[0]).upper().startswith("TABLE:") and block:
                blocks.append(block)
                block = []
            block.append(r)
        blocks.append(block)
        for i, b in enumerate(blocks):
            t = _table_from_rows(b, path.stem if len(blocks) == 1 else f"{path.stem}#{i + 1}", f"{path.name}#{i + 1}")
            if t:
                tables.append(t)
    else:
        raise ValueError(f"unsupported file type {path.suffix}")
    return tables


# --------------------------------------------------------------------------- normalisation
def normalise(tables, assume_units, log):
    """Return dict of normalised datasets and fill log['tables'] / log['issues']."""
    out = {"results": [], "reactions": [], "base": [], "combos": [], "program": {}}
    for t in tables:
        entry = {"name": t["name"], "source": t["source"], "rows": len(t["rows"]), "status": "", "notes": []}
        reg = REGISTRY.get(t["key"])
        log["tables"].append(entry)
        if not reg:
            entry["status"] = "UNSUPPORTED - not imported"
            log["issues"].append({"level": WARN, "msg": f"table '{t['name']}' is not supported by this importer and was not imported"})
            continue
        kind, required, fcols, mcols, lcols = reg
        missing = [c for c in required if c not in t["header"]]
        if missing:
            entry["status"] = "REJECTED - missing columns"
            log["issues"].append({"level": FAIL, "msg": f"table '{t['name']}' lacks required column(s) {missing}; not imported"})
            continue
        if kind == "program":
            for r in t["rows"]:
                out["program"].update({str(k): v for k, v in r.items() if v not in (None, "")})
            entry["status"] = "imported"
            continue
        # unit factors per column
        fac, unit_of = {}, {}
        for col in fcols + mcols + lcols:
            if col not in t["header"]:
                continue
            tok = (t["units"] or {}).get(col, "") if t["units"] else ""
            if not tok:
                if assume_units:
                    f, l = assume_units
                    tok = f if col in fcols else (f"{f}-{l}" if col in mcols else l)
                    entry["notes"].append(f"units for {col} ASSUMED as {tok}")
                    log["issues"].append({"level": WARN, "msg": f"'{t['name']}': no units row; assumed {tok} for {col}"})
                else:
                    entry["status"] = "REJECTED - units unknown"
                    log["issues"].append({"level": FAIL, "msg": f"table '{t['name']}' has no units for {col}; pass --assume-units only if you know them"})
                    break
            uf = unit_factor(tok)
            if uf is None:
                entry["status"] = "REJECTED - unit not recognised"
                log["issues"].append({"level": FAIL, "msg": f"'{t['name']}': unit '{tok}' for {col} not recognised"})
                break
            fac[col], unit_of[col] = uf[0], tok
        else:
            entry["status"] = "imported"
        if entry["status"].startswith("REJECTED"):
            continue
        entry["units_found"] = sorted(set(unit_of.values()))
        for col, tok in unit_of.items():
            if fac[col] != 1.0:
                entry["notes"].append(f"{col}: {tok} -> {unit_factor(tok)[1]} (x{fac[col]:g})")
        mid = next((c for c in MEMBER_ID_COLS if c in t["header"]), None)
        for i, r in enumerate(t["rows"], start=1):
            vals = {}
            bad = False
            for col in fcols + mcols + lcols:
                if col not in t["header"]:
                    continue
                v = r.get(col)
                if v in (None, "") or not _is_num(v):
                    log["issues"].append({"level": FAIL, "msg": f"'{t['name']}' row {i}: {col} is empty or not numeric ({v!r})"})
                    bad = True
                    continue
                vals[col] = float(v) * fac[col]
            if bad:
                continue
            base = {"source_table": t["name"], "source_row": i, "case": str(r.get("Output Case", "")).strip(),
                    "case_type": str(r.get("Case Type", "") or "").strip(), "step": str(r.get("Step Type", "") or "").strip(),
                    "story": str(r.get("Story", "") or "").strip()}
            if kind == "forces":
                out["results"].append({**base, "member_id": str(r.get(mid, "")).strip() if mid else "", "label": str(r.get("Label", r.get("Column", r.get("Beam", ""))) or "").strip(),
                                       "station": vals["Station"], "N": vals["P"], "V2": vals["V2"], "V3": vals["V3"], "T": vals["T"], "M2": vals["M2"], "M3": vals["M3"]})
            elif kind == "reactions":
                jid = str(r.get("Unique Name", r.get("Joint Label", r.get("Joint", ""))) or "").strip()
                out["reactions"].append({**base, "joint": jid, **{k: vals[k] for k in ("FX", "FY", "FZ", "MX", "MY", "MZ")}})
            elif kind == "base":
                out["base"].append({**base, **{k: vals[k] for k in ("FX", "FY", "FZ", "MX", "MY", "MZ")}})
            elif kind == "combos":
                try:
                    sf = float(r["Scale Factor"])
                except (TypeError, ValueError):
                    log["issues"].append({"level": FAIL, "msg": f"'{t['name']}' row {i}: Scale Factor not numeric"})
                    continue
                comp = r.get("Load Case/Combo", r.get("Case", r.get("Load Name", "")))
                out["combos"].append({"name": str(r["Name"]).strip(), "component": str(comp).strip(), "factor": sf})
    return out


# --------------------------------------------------------------------------- checks
def _tol_ok(a, b, pct, abs_floor=1e-6):
    return abs(a - b) <= max(abs_floor, abs(b) * pct / 100.0)


def run_checks(data, expected, members, hand, log):
    chk = log["checks"]
    add = lambda cid, name, status, detail: chk.append({"id": cid, "name": name, "status": status, "detail": detail})
    cases_seen = {r["case"] for k in ("results", "reactions", "base") for r in data[k]}

    # C1 expected cases / combinations present
    if expected:
        want = [c["name"] for c in expected.get("cases", [])] + [c["name"] for c in expected.get("combos", [])]
        missing = [w for w in want if w not in cases_seen]
        extra = sorted(cases_seen - set(want))
        add("C1", "expected load cases/combinations present", FAIL if missing else OK,
            f"missing: {missing}" if missing else f"all {len(want)} expected present")
        if extra:
            add("C1b", "cases in export but not in expected list", WARN, f"{extra}")
    else:
        add("C1", "expected load cases/combinations present", NOTC, "no expected_cases.yaml supplied")

    # C2 combination definitions vs expected factors
    if expected and expected.get("combos"):
        defs = {}
        for r in data["combos"]:
            defs.setdefault(r["name"], {})[r["component"]] = r["factor"]
        probs = []
        for c in expected["combos"]:
            got = defs.get(c["name"])
            if got is None:
                probs.append(f"{c['name']}: definition not in export")
            elif {k: float(v) for k, v in c["terms"].items()} != got:
                probs.append(f"{c['name']}: export {got} != expected {c['terms']}")
        add("C2", "combination factors equal the expected (design-basis) factors", FAIL if probs else OK, "; ".join(probs) or "all match")
    else:
        add("C2", "combination factors equal the expected (design-basis) factors", NOTC, "no expected combinations supplied")

    # C3 member mapping
    if members is not None and data["results"]:
        ids = {m["etabs_label"] for m in members}
        got = {r["label"] or r["member_id"] for r in data["results"]}
        unmapped = sorted(got - ids)
        noresult = sorted(ids - got)
        add("C3", "every exported member maps to a project member", FAIL if unmapped else OK, f"unmapped: {unmapped}" if unmapped else f"{len(got)} members mapped")
        add("C3b", "every project member has results", WARN if noresult else OK, f"no results for: {noresult}" if noresult else "all have results")
    else:
        add("C3", "every exported member maps to a project member", NOTC, "no members.csv or no member results")

    # C4 duplicates
    seen, dups = set(), []
    for r in data["results"]:
        k = (r["case"], r["step"], r["member_id"], r["story"], round(r["station"], 6))
        if k in seen:
            dups.append(k)
        seen.add(k)
    add("C4", "no duplicate (case, member, station) rows", FAIL if dups else OK, f"{len(dups)} duplicate(s), first {dups[:2]}" if dups else "none")

    # C5 superposition (linear combinations)
    if expected and expected.get("combos"):
        probs, tested = [], 0
        tol = float(expected.get("superposition_tolerance_pct", 0.5))
        by = {}
        for r in data["reactions"]:
            by[(r["case"], r["joint"])] = r
        for c in expected["combos"]:
            if not c.get("linear", True):
                continue
            for (case, j), r in list(by.items()):
                if case != c["name"]:
                    continue
                for comp in ("FX", "FY", "FZ"):
                    exp = 0.0
                    ok = True
                    for cn, f in c["terms"].items():
                        src = by.get((cn, j))
                        if src is None:
                            ok = False
                            break
                        exp += float(f) * src[comp]
                    if ok:
                        tested += 1
                        if not _tol_ok(r[comp], exp, tol, 0.01):
                            probs.append(f"{c['name']} joint {j} {comp}: {r[comp]:.3f} vs sum {exp:.3f}")
        add("C5", "combination results equal factor-weighted sum of component cases (joint reactions)",
            FAIL if probs else (OK if tested else NOTC), "; ".join(probs[:4]) or (f"{tested} values tested" if tested else "nothing to test"))
    else:
        add("C5", "combination results equal factor-weighted sum of component cases", NOTC, "no expected combinations")

    # C6 reactions vs base reactions
    if data["reactions"] and data["base"]:
        probs, n = [], 0
        for b in data["base"]:
            s = [r for r in data["reactions"] if r["case"] == b["case"] and r["step"] == b["step"]]
            if not s:
                probs.append(f"{b['case']}: no joint reactions")
                continue
            n += 1
            tot = sum(r["FZ"] for r in s)
            if not _tol_ok(tot, b["FZ"], 0.5, 0.01):
                probs.append(f"{b['case']}: sum of joint reactions FZ {tot:.2f} vs base reaction {b['FZ']:.2f}")
        add("C6", "sum of joint reactions FZ equals base reaction FZ (internal consistency)", FAIL if probs else OK, "; ".join(probs) or f"{n} cases agree within 0.5 %")
    else:
        add("C6", "sum of joint reactions FZ equals base reaction FZ", NOTC, "need both Joint Reactions and Base Reactions tables")

    # C7 hand take-down (independent applied load)
    if hand:
        tol = hand.get("tolerance_pct")
        if tol is None:
            add("C7", "base reaction equals independent hand total", NOTC, "hand_totals.yaml has no tolerance_pct - none assumed")
        else:
            probs, n = [], 0
            for case, fz in hand.get("fz_kN", {}).items():
                rs = [r["FZ"] for r in data["reactions"] if r["case"] == case]
                if not rs:
                    probs.append(f"{case}: no joint reactions")
                    continue
                n += 1
                if not _tol_ok(sum(rs), float(fz), float(tol), 0.01):
                    probs.append(f"{case}: model {sum(rs):.2f} kN vs hand {float(fz):.2f} kN")
            add("C7", "sum of reactions equals independent hand total", FAIL if probs else OK, "; ".join(probs) or f"{n} cases within {tol} %")
    else:
        add("C7", "sum of reactions equals independent hand total", NOTC, "no hand_totals.yaml - global equilibrium vs applied load NOT verified")

    # C8 units: every imported table had units read from the export (or explicitly assumed) and converted to kN, m
    unit_fail = [i["msg"] for i in log["issues"] if i["level"] == FAIL and "unit" in i["msg"].lower()]
    assumed = [i["msg"] for i in log["issues"] if "assumed" in i["msg"]]
    conv = sorted({n for t in log["tables"] for n in t.get("notes", []) if "->" in n})
    if unit_fail:
        add("C8", "units recognised and converted to kN, m", FAIL, "; ".join(unit_fail))
    elif assumed:
        add("C8", "units recognised and converted to kN, m", WARN, f"{len(assumed)} column(s) used ASSUMED units - confirm against the model")
    else:
        add("C8", "units recognised and converted to kN, m", OK, "; ".join(conv) or "all tables already in kN, m")


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def write_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def run(files, out, model_id, model_file=None, run_date=None, software=None, members_csv=None, expected_yaml=None,
        hand_yaml=None, assume_units=None) -> dict:
    out = pathlib.Path(out)
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    log = {"model_id": model_id, "imported_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "provenance": {"software": software, "model_file": model_file, "run_date": run_date, "export_files": []},
           "tables": [], "issues": [], "checks": [],
           "disclaimer": "A completed import does not show the analysis model is correct. Only the checks listed below were performed."}
    tables = []
    for f in files:
        f = pathlib.Path(f)
        dst = raw / f.name
        shutil.copyfile(f, dst)
        log["provenance"]["export_files"].append({"file": f.name, "sha256": sha256(dst), "bytes": dst.stat().st_size,
                                                  "modified_utc": dt.datetime.fromtimestamp(f.stat().st_mtime, dt.timezone.utc).isoformat(timespec="seconds")})
        tables += parse_file(dst)
    data = normalise(tables, assume_units, log)
    prog = data["program"]
    if prog:
        log["provenance"]["program_control"] = prog
        if not software:
            nm = " ".join(str(prog[k]) for k in ("ProgramName", "Program Name", "Version") if k in prog)
            log["provenance"]["software"] = nm or None
    for k in ("software", "model_file", "run_date"):
        if not log["provenance"][k]:
            log["issues"].append({"level": WARN, "msg": f"provenance '{k}' not recorded (not in export and not supplied)"})
    def _read(p, fn):
        with open(p, newline="", encoding="utf-8-sig") as fh:
            return fn(fh)
    members = _read(members_csv, lambda fh: list(csv.DictReader(fh))) if members_csv else None
    expected = _read(expected_yaml, yaml.safe_load) if expected_yaml else None
    hand = _read(hand_yaml, yaml.safe_load) if hand_yaml else None
    run_checks(data, expected, members, hand, log)
    # outputs
    out.mkdir(parents=True, exist_ok=True)
    rcols = ["model_id", "case_or_combo", "case_type", "step", "story", "member_id", "label", "station", "N", "V2", "V3", "T", "M2", "M3", "unit_force", "unit_length", "source_table", "source_row"]
    rows = [dict(r, model_id=model_id, case_or_combo=r["case"], unit_force="kN", unit_length="m") for r in data["results"]]
    write_csv(out / "analysis_results.csv", rows, rcols)
    write_csv(out / "joint_reactions.csv", [dict(r, model_id=model_id, case_or_combo=r["case"], unit_force="kN", unit_length="m") for r in data["reactions"]],
              ["model_id", "case_or_combo", "step", "joint", "FX", "FY", "FZ", "MX", "MY", "MZ", "unit_force", "unit_length", "source_table", "source_row"])
    write_csv(out / "base_reactions.csv", [dict(r, model_id=model_id, case_or_combo=r["case"]) for r in data["base"]],
              ["model_id", "case_or_combo", "step", "FX", "FY", "FZ", "MX", "MY", "MZ", "source_table", "source_row"])
    fails = [c for c in log["checks"] if c["status"] == FAIL] + [i for i in log["issues"] if i["level"] == FAIL]
    log["summary"] = {"rows_results": len(rows), "rows_reactions": len(data["reactions"]), "rows_base": len(data["base"]),
                      "checks_pass": sum(c["status"] == OK for c in log["checks"]), "checks_fail": sum(c["status"] == FAIL for c in log["checks"]),
                      "checks_not_checked": sum(c["status"] == NOTC for c in log["checks"]),
                      "blocking_problems": len(fails), "ready_for_calculations": not fails}
    with open(out / "import_log.json", "w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=2)
    prov = {"analysis_provenance": {"software": log["provenance"]["software"], "model_file": log["provenance"]["model_file"],
                                    "run_date": log["provenance"]["run_date"], "export_files": [e["file"] for e in log["provenance"]["export_files"]],
                                    "export_sha256": {e["file"]: e["sha256"] for e in log["provenance"]["export_files"]}}}
    (out / "analysis_provenance.proposed.yaml").write_text("# PROPOSED - review, then paste into the design basis. Not applied automatically.\n" + yaml.safe_dump(prov, sort_keys=False), encoding="utf-8")
    lines = [f"# ETABS/SAFE import report - {model_id}", "", f"Ready for calculations: **{'YES' if log['summary']['ready_for_calculations'] else 'NO'}**",
             "", "> " + log["disclaimer"], "", "## Checks", "| Id | Check | Status | Detail |", "|---|---|---|---|"]
    lines += [f"| {c['id']} | {c['name']} | {c['status']} | {c['detail']} |" for c in log["checks"]]
    lines += ["", "## Tables", "| Table | Source | Rows | Status |", "|---|---|---|---|"] + [f"| {t['name']} | {t['source']} | {t['rows']} | {t['status']} |" for t in log["tables"]]
    if log["issues"]:
        lines += ["", "## Issues"] + [f"- **{i['level']}** {i['msg']}" for i in log["issues"]]
    (out / "import_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return log


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model-id", required=True)
    ap.add_argument("--model-file")
    ap.add_argument("--run-date")
    ap.add_argument("--software")
    ap.add_argument("--members")
    ap.add_argument("--expected")
    ap.add_argument("--hand-totals")
    ap.add_argument("--assume-units", help="e.g. kN,m - ONLY when the export has no units row and you know them")
    ns = ap.parse_args(argv)
    au = tuple(ns.assume_units.split(",")) if ns.assume_units else None
    log = run(ns.files, ns.out, ns.model_id, ns.model_file, ns.run_date, ns.software, ns.members, ns.expected, ns.hand_totals, au)
    print(json.dumps(log["summary"], indent=2))
    return 0 if log["summary"]["ready_for_calculations"] else 1


if __name__ == "__main__":
    sys.exit(main())
