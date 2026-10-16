---
name: structural-pt-drawing
description: Produce BONDED post-tensioning drawing sheets (PT general notes to Eurocode, tendon layout plan, tendon profiles, tendon schedule) from project data files. Use for any request to draft, redraft, revise or check PT slab / band-beam drawings, PT notes or tendon profiles.
---

# Structural PT Drawing (bonded post-tensioning)

This skill turns PT data into company-standard PT sheets. It covers the plan, the profiles and the general notes. It does not design the tendons.

## What it will and will not do
- Draws what the data says. It never invents a tendon force, strand count, length, elevation, friction value, anchorage size or code clause.
- Post-tensioning is **BONDED** only. If a basis or document says unbonded or mono-strand, stop and tell the user. Do not convert silently.
- Design is to Eurocodes (CEN recommended values unless the design basis records a National Annex). British Standard references are not used.
- Never marks anything APPROVED. The output is a DXF written by script (not a DWG) plus a script-rendered preview (not a CTB plot). Say which one you made.

## Before drawing
1. Read `design-basis/<PROJECT-CODE>.yaml` for project code, name, client, prefix, stage, revision, date and National Annex stance. Titles and sheet numbers come from there only.
2. Read the PT basis `design-basis/<PROJECT-CODE>.pt.yaml` (copy `design-basis/PT_BASIS_TEMPLATE.yaml` if there is none; fill only what the user has stated; leave the rest `null`). Run `python tools/cadgen/validate_pt_basis.py <file> --design-basis <db.yaml>`.
3. Read `Structural-Drawing-Standards/` (title block 01, notes 04, drafting styles 05). Check each file's status header. `04-02_PT_General_Notes.md` and layer file `05-04c` are PROPOSED, not approved: follow them and say so.
4. Read `references/pt-drawing-package.md` for sheet numbers and which tool makes which sheet.

## Workflow
| Sheet | Tool | Input |
|---|---|---|
| PT-001 general notes and design criteria | `python tools/cadgen/pt_notes.py --pt-basis <pt.yaml> --design-basis <db.yaml> --standards Structural-Drawing-Standards --out <dir> --sheet-number <PREFIX>-PT-001` | PT basis, template `assets/pt_general_notes.yaml` |
| PT-101 tendon layout plan | `python tools/cadgen/pt_plan.py --data <pt_plan_data.json> --standards ... --out <dir>` | `references/pt-plan-data.md` |
| PT-102 tendon profiles | `python tools/cadgen/pt_profiles.py --data <pt_profile_data.json> --standards ... --out <dir>` | `references/pt-profile-data.md` |

Then ALWAYS: run `python tools/cadgen/validate_dxf.py <sheet.dxf> --standards ...`, run `python -m unittest discover -s tests`, and look at every rendered page before reporting.

## Two modes
- **Redraft** (existing drawing): geometry and labels are transcribed from the source. Mark every transcribed value "VERIFY" on the sheet and keep the source name and revision on it. Convert with the one-off converters in `redraft_2F_PT/` as the pattern. Do not change the design.
- **New design**: tendon quantities, forces, profiles and losses must come from the PT analysis (for example ADAPT-Builder) as data. If they are not supplied, stop and list what is missing. Never fill them in.

## Rules
- The general-notes wording is in `assets/pt_general_notes.yaml`; project values are parameters from the PT basis. A missing value prints TBC and appears under ASSUMPTIONS TO BE CONFIRMED.
- Where a source value does not carry straight across to Eurocode (wobble factor, yield vs fp0.1k, strength at stressing, plain round bars), leave it TBC or as the source value and add an open item. See `references/source-conversion-log.md`.
- Strand symbols: only 2 (circle), 3 (triangle), 4 (square) and 5 (diamond) are defined. Other counts stop the build (open item PT-OI-12).
- Layers `S-PT-TENDON` and `S-CONC-DROP` are in the PROPOSED file 05-04c. Using them gives validator warnings until an authorised engineer approves the file.
- Plan, profile, schedule and notes must agree on tendon marks, strand counts and lengths. The plan generator builds the schedule from the same tendon list. The profile generator stops if station spacings do not add to the last chainage.
- Profile length versus plan label length: report differences as observations to verify with the designer, not as conclusions (gap G24).

## QA
Use `references/qa-checklist.md`. After producing sheets, hand the package to `structural-document-qa`.
