---
name: structural-drawing
description: Produce structural drawing sheets (cover page, drawing list, general notes, layouts, details) to company drawing standards for AutoCAD - DXF/DWG and PDF. Use for any request to create, revise or check structural drawings or sheets, or to apply the company title block, layers and text styles.
---

# Structural Drawing

## Before drawing
1. Read the project design basis (`design-basis/<code>.yaml`); take project code, name, client, prefix, stage, revision and date from it.
2. Read the standards, in this order, noting each file's status header:
   - `Structural-Drawing-Standards/01_Title-Block/`, `02_Cover-Page/`, `03_Drawing-Index/`, `04_General-Notes-and-Details/` (derived from the WH-STR-SD R00 drawing set; approved by the user 14-OCT-2026)
   - `05_Drafting-Styles/` (company standard: text, annotation, line types, layers CSV)
3. Read `references/drawing-package-format.md` (what each sheet type looks like) and `references/cad-workflow.md` (what can and cannot be claimed about outputs).

## Rules
- A3 landscape, two-row title block across the top, border and layout exactly per standard. Do not restyle.
- Text, dimensions, hatches, line weights and layers only from `05_Drafting-Styles`. Layer names/colours come from `05-04_Layer_Standards.csv`; if a needed layer does not exist, add it to the gap register - do not invent it silently.
- Separate geometry/data (member sizes, grid, levels) from presentation. Member data must come from the design basis/calc outputs; do not draw dimensions or reinforcement that no source supports. Mark unconfirmed values "TBC" on the sheet.
- Every sheet number must exist in the document register; update the drawing list (002) whenever sheets change.
- **Honesty about outputs:** only say "DWG generated/validated" if a native CAD tool produced and opened it. A DXF written by script is a DXF. A rendered PDF/PNG is a preview. Say which one you made and what was not checked (fonts, plot style, xrefs).

## Output pipeline (built for cover 001, drawing list 002, and Eurocode general notes & standard details 003-007)
- Cover (001) & Drawing List (002): `python tools/cadgen/build_sheets.py --design-basis <db.yaml> --register <register.csv> --standards Structural-Drawing-Standards --out <dir> [--include-notes-details]`
- General Notes & Standard Details (003-007): `python tools/cadgen/build_notes_and_details.py --design-basis <db.yaml> --register <register.csv> --standards Structural-Drawing-Standards --out <dir> [--overrides <notes_overrides.yaml>] [--dwg]`
- Standalone reusable CAD blocks & master sheet templates live in `Structural-Drawing-Standards/06_Templates/` (`blocks/` and `sheets/`), driven by `04_General-Notes-and-Details/04-02_Eurocode_General_Notes_Library.yaml` and `calc_lib/rc/ec2_anchorage.py`. Rebuild templates with `python tools/cadgen/build_notes_and_details.py --export-templates --standards Structural-Drawing-Standards [--dwg]`.
- Always validate every DXF with `python tools/cadgen/validate_dxf.py <sheet.dxf> --standards ... --design-basis ... --register ...` and run `python tools/doc_control/check_register.py` after changing the sheet list.
