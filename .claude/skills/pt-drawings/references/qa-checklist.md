# PT drawing QA checklist (bonded)

Run after generating sheets. Tick only what was actually checked. "Automatic" means a tool in this repo checks it.

## Plan
- [ ] Every tendon has a mark and group number; group numbers unique (automatic: `pt_plan.check_data`)
- [ ] Strand numbers match the strand count (automatic)
- [ ] Every tendon appears in the schedule and the CSV (automatic: both built from one list)
- [ ] Strand symbol defined for every strand count used (automatic: build stops otherwise)
- [ ] Spacing, column-face offset, edge offset, opening and core clearances, anchorage edge distance: from the PT supplier and the design basis, not from this skill (manual)
- [ ] Stressing end(s) and dead ends identified (the 2F redraft did NOT redraw them: TBC)
- [ ] Duct size and grout inlet / vent positions shown where the supplier requires them (manual)

## Profile
- [ ] Station spacings add to the last chainage (automatic)
- [ ] Datum stated (heights above soffit; section steps drawn)
- [ ] High / low points, cover, eccentricity, tendon-to-rebar clearance, minimum radius: from the PT analysis (manual)
- [ ] Bar chair heights from the supplier library (manual)

## Cross-consistency
- [ ] Plan mark = profile mark = schedule mark
- [ ] Profile length against plan label length. Differences are observations to verify with the designer (gap G24); the tool prints VERIFY
- [ ] Strand count and tendon length agree between plan, profile and schedule

## Notes (PT-001)
- [ ] `validate_pt_basis.py` has no errors; warnings read and explained
- [ ] Every TBC on the sheet is listed under ASSUMPTIONS TO BE CONFIRMED (automatic)
- [ ] No BS reference and no unbonded wording (automatic in the validator)
- [ ] Values equal the project design basis and the PT supplier assessment (manual)

## Files
- [ ] `python 04_tools/cadgen/validate_dxf.py <sheet>.dxf --standards 01_standards`
- [ ] `python -m unittest discover -s tests`
- [ ] Preview PDF looked at page by page; say it is a script-rendered preview, not a CTB plot
- [ ] Status stated as DRAFT / FOR REVIEW. Never APPROVED
