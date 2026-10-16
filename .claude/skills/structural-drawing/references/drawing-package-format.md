# Drawing package format (from WH-STR-SD Drawing Set R00, 7 sheets reviewed)

Status: convention observed from the user's issued drawing set; standards 01-04 approved by the user 14-OCT-2026.

## Sheet frame
A3 landscape, single outer border. Title block is a strip across the TOP, two rows:
- Row 1: PROJ. REFERENCE | DRAWING NAME | REVISION | (blank cell) | DRAWN BY | north arrow + "STRUCTURAL (BIM)"
- Row 2: DRAWING NUMBER | DRAWING STAGE | CLIENT | SCALE | ISSUE DATE
- Labels small grey upper case; values larger, black. Right-hand box holds north arrow and discipline label (no company logo is reproduced).

Example values: PRJ-2026-003 | STRUCTURAL COVER PAGE | R00 | P.LIHENG | WH-STR-SD-001 | FOR APPROVAL | Mr. XXX | AS-SHOWN | 13-OCT-2026. Notes sheets use scale `N.T.S.`.

## Numbering series
| Range | Content |
|---|---|
| 001 | Structural cover page |
| 002 | Structural drawing list |
| 003-007 | General notes parts 01-05 |
| 101-108 | Layouts, sections, elevations, steel connection/member details |
| 201-204 | Concrete reinforcement details |

## Cover page (001)
Centred: `<PROJECT CODE>_<PROJECT NAME>` (large, underlined rule), `STRUCTURAL CONSTRUCTION DRAWING`, one-line description + design codes, isometric structure view, `ISSUE DATE: ...`, `REVISION: ...`.

## Drawing list (002)
Heading `STRUCTURAL DRAWING LIST`; table columns: Sheet Number | Sheet Name | Paper | Current Revision | Sheet Issue Date. One row per sheet in number order, including the cover and list itself.

## General notes (003-007)
Two-column text sheets with lettered sections (`A. GENERAL`, `B. DESIGN CODES`, ...), small bordered tables, numbered notes. Current split:
- 003 General, design codes, design basis & actions, load combinations, design results summary, assumptions to be confirmed
- 004 Concrete: materials, cover, anchorage/lap, reinforcement notes, curing, earthworks, brickwork
- 005 Steelwork: materials, sections adopted, fabrication & welding, corrosion protection, erection, connection basis
- 006 RC standard details (bends/hooks, laps, corner detail, notation)
- 007 Steel standard details (bolt table, weld symbols, stiffener/fin plate, abbreviations)

Design-derived values on notes sheets must trace to the design basis / calculation report; keep "assumptions to be confirmed" in sync with `open_items`.
