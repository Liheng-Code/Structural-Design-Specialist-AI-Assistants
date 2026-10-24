# PT drawing package (bonded)

Sheet numbers follow the project prefix from the design basis: `<PREFIX>-PT-<nnn>`. Stage and revision come from the design basis. For preliminary PT work the user has used stage PRELIMINARY PT DESIGN and revision P01 (see `01_standards/00-gap-register.md` G08 for the open P/R/C rule).

| Sheet | Name | Made by | Status of tooling |
|---|---|---|---|
| PT-001 | General notes and design criteria | `04_tools/cadgen/pt_notes.py` | built, DXF + preview, tested |
| PT-101 | Tendon layout plan | `04_tools/cadgen/pt_plan.py` | built, tested against the 2F redraft |
| PT-102 | Tendon profiles (one or more sheets, X and Y) | `04_tools/cadgen/pt_profiles.py` | built, tested against the 2F redraft |
| PT-103 | Anchorage layout | not built | draw manually; data from the PT supplier |
| PT-104 | Band beam PT details | not built | draw manually |
| PT-105 | Tendon schedule | CSV from `pt_plan.py` (`*_schedule.csv`) and the table on PT-101 | table sheet not built |
| PT-106 | Design check summary | not built | needs the PT analysis results |

Not built means: the skill describes the content from the data and flags manual drafting. It must say so.

## Title block
Company title block (01-01). Fields come from the design basis. `pt_notes.py` takes them with `--design-basis`; plan and profile data files carry a `title_block` object that must hold the same values. The stage text PRELIMINARY PT DESIGN is longer than its title-block cell and runs into the CLIENT cell (observed 16-OCT-2026, gap G25).

## Input data for each sheet
- Notes: `03_projects/<code>.pt.yaml` (template `03_projects/_template/pt-basis.yaml`).
- Plan: `references/pt-plan-data.md`.
- Profiles: `references/pt-profile-data.md`.
Example data for all three: `03_projects/PJR-2F-PT/`.
