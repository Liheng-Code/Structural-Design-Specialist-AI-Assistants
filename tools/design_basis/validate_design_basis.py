#!/usr/bin/env python3
"""Validate a project design-basis file (YAML).

Usage:  python validate_design_basis.py <design_basis.yaml> [--strict] [--json]

Exit codes: 0 = no ERRORs (WARNINGs allowed unless --strict), 1 = ERRORs, 2 = file unreadable.

Philosophy: the validator never fills in or "fixes" engineering values. It only reports what is
missing, unresolved, or contradictory so an engineer can resolve it.
Requires: Python 3.9+, PyYAML.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required:  pip install pyyaml")

STATUSES = {"DRAFT", "FOR_REVIEW", "APPROVED"}
NA_MODES = {"NA", "CEN_RECOMMENDED", "UNRESOLVED"}
GENERATIONS = {"1st", "2nd"}
ITEM_STATUSES = {"confirmed", "assumed", "to_confirm"}
STRUCTURE_FAMILIES = {  # structure_types -> Eurocode families expected (not auto-applied!)
    "steel": "EN 1993",
    "rc": "EN 1992",
    "pt": "EN 1992",
    "composite": "EN 1994",
    "timber": "EN 1995",
    "masonry": "EN 1996",
    "foundations": "EN 1997",
    "seismic": "EN 1998",
}
ALWAYS_FAMILIES = {"EN 1990", "EN 1991"}
PLACEHOLDER = re.compile(r"\b(TBC|TBD|XXX+|TO BE CONFIRMED|PLACEHOLDER)\b", re.I)
DATE_RE = re.compile(r"^\d{2}-[A-Z]{3}-\d{4}$")
PROJECT_CODE_RE = re.compile(r"^[A-Z]{3}-\d{4}-\d{3}$")
PREFIX_RE = re.compile(r"^[A-Z]{2,4}-STR$")
REV_RE = re.compile(r"^(R|P|C)\d{2}$")  # R00 issued, P01 preliminary, C01 construction (extendable)

ALLOWED_KEYS = {
    "standards": {"id", "generation", "edition", "amendments", "corrigenda", "used_for"},
    "materials": {"id", "element", "spec", "status", "source"},
    "loads": {"id", "description", "value", "unit", "status", "source"},
    "combinations": {"id", "description", "status", "source"},
    "open_items": {"id", "status", "description", "owner"},
}

Issue = tuple  # (severity, path, message)


def family(std_id: str) -> str | None:
    m = re.match(r"^(EN\s?\d{4})", std_id.strip())
    return re.sub(r"\s+", " ", m.group(1)) if m else None


def walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def validate(db: dict) -> list[Issue]:
    issues: list[Issue] = []
    add = lambda sev, path, msg: issues.append((sev, path, msg))

    if not isinstance(db, dict):
        return [("ERROR", "<root>", "design basis must be a mapping")]

    for sect in ("project", "approval", "standards", "national_annex", "design_assumptions"):
        if sect not in db or db[sect] in (None, "", [], {}):
            add("ERROR", sect, "required section missing or empty")
    proj = db.get("project") or {}
    appr = db.get("approval") or {}
    status = appr.get("status")
    approved = status == "APPROVED"
    unresolved = "ERROR" if approved else "WARNING"  # unresolved items block approval only

    # ---- project
    for k in ("code", "name", "stage", "client", "drawing_prefix", "revision", "issue_date", "structure_types"):
        if proj.get(k) in (None, "", []):
            add("ERROR", f"project.{k}", "required field missing")
    if proj.get("code") and not PROJECT_CODE_RE.match(str(proj["code"])):
        add("ERROR", "project.code", f"'{proj['code']}' does not match AAA-YYYY-NNN")
    if proj.get("code") and PROJECT_CODE_RE.match(str(proj["code"])) and not str(proj["code"]).startswith("PJR-"):
        add("WARNING", "project.code", f"company project codes use the PJR- prefix; '{proj['code']}' does not")
    if proj.get("drawing_prefix") and not PREFIX_RE.match(str(proj["drawing_prefix"])):
        add("ERROR", "project.drawing_prefix", f"'{proj['drawing_prefix']}' does not match XX-STR")
    if proj.get("revision") and not REV_RE.match(str(proj["revision"])):
        add("ERROR", "project.revision", f"'{proj['revision']}' is not a recognised revision (R00/P01/C01 style)")
    if proj.get("issue_date") and not DATE_RE.match(str(proj["issue_date"]).upper()):
        add("ERROR", "project.issue_date", "date must be DD-MMM-YYYY (e.g. 13-OCT-2026)")

    # ---- approval
    if status not in STATUSES:
        add("ERROR", "approval.status", f"must be one of {sorted(STATUSES)}")
    if approved:
        for k in ("prepared_by", "checked_by", "approved_by", "approved_date"):
            if not appr.get(k):
                add("ERROR", f"approval.{k}", "APPROVED status requires this field (authorised engineering review)")

    # ---- unexpected fields (typically an unquoted comma inside a YAML {flow, mapping} splitting a value)
    for sect, allowed in ALLOWED_KEYS.items():
        for i, it in enumerate(db.get(sect) or []):
            if isinstance(it, dict):
                for k in it:
                    if k not in allowed:
                        add("ERROR", f"{sect}[{i}]", f"unexpected field '{k}' - is a value with a comma missing quotes?")

    # ---- standards
    stds = db.get("standards") or []
    seen_ed = defaultdict(set)
    gens = set()
    for i, s in enumerate(stds):
        p = f"standards[{i}]"
        if not isinstance(s, dict) or not s.get("id"):
            add("ERROR", p, "each standard needs an 'id' (e.g. 'EN 1992-1-1')")
            continue
        if not s.get("edition"):
            add(unresolved, f"{p}.edition", f"{s['id']}: edition/year not recorded")
        else:
            seen_ed[s["id"]].add(str(s["edition"]))
        if s.get("generation"):
            if s["generation"] not in GENERATIONS:
                add("ERROR", f"{p}.generation", "must be '1st' or '2nd'")
            gens.add(s["generation"])
        else:
            add("WARNING", f"{p}.generation", f"{s['id']}: Eurocode generation (1st/2nd) not stated")
        if not s.get("used_for"):
            add("WARNING", f"{p}.used_for", f"{s['id']}: scope of use not stated")
    for sid, eds in seen_ed.items():
        if len(eds) > 1:
            add("ERROR", "standards", f"{sid} listed with conflicting editions {sorted(eds)}")
    if len(gens) > 1 and not db.get("mixed_generation_justification"):
        add("ERROR", "standards", "1st and 2nd generation Eurocodes mixed without 'mixed_generation_justification'")

    # ---- applicability (do not auto-apply every family)
    fams = {family(s["id"]) for s in stds if isinstance(s, dict) and s.get("id")} - {None}
    expected = set(ALWAYS_FAMILIES)
    for t in proj.get("structure_types") or []:
        if t not in STRUCTURE_FAMILIES:
            add("ERROR", "project.structure_types", f"unknown structure type '{t}' (allowed: {sorted(STRUCTURE_FAMILIES)})")
        else:
            expected.add(STRUCTURE_FAMILIES[t])
    for f in sorted(expected - fams):
        add("WARNING", "standards", f"{f} expected for the stated structure types but not listed")
    for f in sorted(x for x in fams - expected if x.startswith("EN 199")):
        add("WARNING", "standards", f"{f} is listed but no structure type needs it - confirm it applies")

    # ---- national annex
    na = db.get("national_annex") or {}
    mode = na.get("mode")
    if mode not in NA_MODES:
        add("ERROR", "national_annex.mode", f"must be one of {sorted(NA_MODES)}")
    elif mode == "UNRESOLVED":
        add(unresolved, "national_annex.mode", "National Annex choice is unresolved")
    elif mode == "NA":
        if not na.get("country"):
            add("ERROR", "national_annex.country", "country required when mode is NA")
        if not na.get("references"):
            add("ERROR", "national_annex.references", "exact NA document references required when mode is NA")
    elif mode == "CEN_RECOMMENDED" and not na.get("basis_note"):
        add("ERROR", "national_annex.basis_note", "state why CEN recommended values are used (e.g. no NA exists for the country)")

    # ---- assumptions / loads / combinations / provenance
    da = db.get("design_assumptions") or {}
    for k in ("design_working_life_years", "consequence_class", "units"):
        if da.get(k) in (None, "", {}):
            add("ERROR", f"design_assumptions.{k}", "required field missing")
    for sect in ("materials", "loads", "combinations"):
        for i, it in enumerate(db.get(sect) or []):
            st = it.get("status") if isinstance(it, dict) else None
            if st not in ITEM_STATUSES:
                add("ERROR", f"{sect}[{i}].status", f"must be one of {sorted(ITEM_STATUSES)}")
            elif st != "confirmed":
                add(unresolved, f"{sect}[{i}]", f"{it.get('id') or it.get('element') or i} is '{st}' - confirm before approval")
            if isinstance(it, dict) and st != "to_confirm" and not (it.get("source")):
                add("WARNING", f"{sect}[{i}].source", "no source/clause recorded")
    if not db.get("analysis_provenance"):
        add("WARNING", "analysis_provenance", "no analysis provenance recorded (software, version, model, run date)")
    for i, oi in enumerate(db.get("open_items") or []):
        if isinstance(oi, dict) and oi.get("status", "open") == "open":
            add(unresolved, f"open_items[{i}]", f"open item {oi.get('id', i)}: {oi.get('description', '')[:60]}")

    # ---- placeholders anywhere
    for path, text in walk_strings(db):
        if PLACEHOLDER.search(text) and not path.startswith("open_items"):
            add("WARNING" if not approved else "ERROR", path, f"unresolved placeholder in '{text[:50]}'")
    return issues


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        with open(a.file, encoding="utf-8") as fh:
            db = yaml.safe_load(fh)
    except Exception as e:  # noqa: BLE001
        print(f"cannot read {a.file}: {e}", file=sys.stderr)
        return 2
    issues = validate(db)
    errs = [i for i in issues if i[0] == "ERROR"]
    warns = [i for i in issues if i[0] == "WARNING"]
    if a.json:
        print(json.dumps([{"severity": s, "path": p, "message": m} for s, p, m in issues], indent=2))
    else:
        for s, p, m in issues:
            print(f"{s:7} {p}: {m}")
        print(f"\n{len(errs)} error(s), {len(warns)} warning(s)  ->  "
              f"{'NOT READY' if errs or (a.strict and warns) else 'structurally valid'}")
    return 1 if errs or (a.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
