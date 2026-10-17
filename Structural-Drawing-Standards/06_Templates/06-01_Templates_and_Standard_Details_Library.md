# 06-01 Templates and Eurocode Standard Details Library - PROPOSED (16-OCT-2026)

Source: `04-01_General_Notes_Format.md` (APPROVED 14-OCT-2026), `04-02_Eurocode_General_Notes_Library.yaml`, and `tools/cadgen/build_notes_and_details.py`.

## 1. Reusable CAD Detail Blocks (`06_Templates/blocks/`)
Each block is provided in both `.dxf` and `.dwg` (AutoCAD 2018 AC1032 format converted via AutoCAD 2023 `accoreconsole.exe`) and conforms strictly to `05_Drafting-Styles` (`05-01` text heights $\ge 2.0\text{ mm}$, `05-04`/`05-04a`/`05-04b` layers, ByLayer colours and lineweights, millimetre units):

| Block File | Description | Eurocode Reference | Layers Used |
|---|---|---|---|
| `STR_TITLEBLOCK_A3.dxf` / `.dwg` | Company A3 landscape title block with 9 attributes (`PROJ_REFERENCE`, `DRAWING_NAME`, `REVISION`, `DRAWN_BY`, `DRAWING_NUMBER`, `DRAWING_STAGE`, `CLIENT`, `SCALE`, `ISSUE_DATE`) | `01-01_Title_Block.md` | `S-TBLK-BORDER`, `S-TBLK-LINE`, `S-TBLK-TEXT` |
| `BLK_EC2_BENDS_AND_HOOKS.dxf` / `.dwg` | Standard 90° bend ($10\phi$), 135° hook ($10\phi$), 180° hook ($5\phi$), closed link with alternating 135° hooks, and minimum mandrel diameter schedule ($4\phi$ for $\phi \le 16$, $7\phi$ for $\phi > 16$) | EN 1992-1-1 §8.3, Table 8.1N, EN 13670 | `S-REBAR`, `S-ANNO-TABLE`, `S-ANNO-TEXT` |
| `BLK_EC2_LAP_SPLICE.dxf` / `.dwg` | Tension lap splice ($l_0 = \alpha_6 l_{bd}$) and anchorage schematic with minimum lap & transverse spacing criteria | EN 1992-1-1 §8.4, §8.7 | `S-REBAR`, `S-ANNO-DIMS`, `S-ANNO-TEXT` |
| `BLK_EC2_CORNER_DETAIL.dxf` / `.dwg` | Typical beam / wall corner L-bar anchorage detail in plan ($50\phi$ / $l_{bd}$) | EN 1992-1-1 §8.4 / §9.2 | `S-CONC-OUTLINE`, `S-REBAR`, `S-ANNO-TEXT` |
| `BLK_EC3_BOLT_SPACING_TABLE.dxf` / `.dwg` | Bolt hole ($d_0$), minimum edge distance ($e_1 \ge 1.2 d_0$), pitch ($p_1 \ge 2.2 d_0$), and tightening schedule for M12–M24 | EN 1993-1-8 Table 3.3, EN 1090-2 | `S-ANNO-TABLE`, `S-ANNO-TEXT` |
| `BLK_EC3_WELD_SYMBOLS.dxf` / `.dwg` | Standard fillet weld, CJP butt weld, all-round weld, and field weld schedule | EN 1993-1-8 §4, EN ISO 2553 | `S-ANNO-TABLE`, `S-ANNO-TEXT` |
| `BLK_EC3_STIFFENER_FINPLATE.dxf` / `.dwg` | Typical web stiffener (clipped $20 \times 20$ at corners) and bolted fin-plate connection schematic | EN 1993-1-8, EN 1993-1-5 | `S-STEEL-OUTLINE`, `S-ANNO-TEXT` |

---

## 2. Standalone Master Sheet Templates (`06_Templates/sheets/`)
Ready-to-use A3 master sheets (`TPL-STR-SD-003` to `007`) in `.dxf`, `.dwg`, and combined preview PDF (`TPL-STR-SD_R00_preview.pdf`):
- `TPL-STR-SD-003_R00`: **General Notes - Part 01 (General, Design Basis & Loading)** — Eurocode design codes table, actions table, EN 1990 load combinations, design results summary template, and assumptions to be confirmed (`F1..Fn`).
- `TPL-STR-SD-004_R00`: **General Notes - Part 02 (Concrete & Reinforcement)** — EN 206 concrete classes & exposure table, EN 1992-1-1 §4.4 nominal cover table, live-computed EN 1992-1-1 §8.4/§8.7 anchorage/lap/mandrel table (`calc_lib/rc/ec2_anchorage.py`), reinforcement notes, concreting & curing, earthworks & ground slab, and brickwork infill notes.
- `TPL-STR-SD-005_R00`: **General Notes - Part 03 (Structural Steelwork)** — EN 10025-2 / EN 14399-3 materials table, steel sections schedule template, EN 1090-2 EXC2 fabrication & welding notes, ISO 12944 corrosion protection, erection sequence, and EN 1993-1-8 connection basis.
- `TPL-STR-SD-006_R00`: **General Notes - Part 04 (RC Standard Details)** — Bends & hooks, mandrel schedule, tension lap splice, corner detail, reinforcement notation, and RC standard notes.
- `TPL-STR-SD-007_R00`: **General Notes - Part 05 (Steel Standard Details)** — EN 1993-1-8 Table 3.3 bolt hole & spacing table, weld symbols, stiffener/fin-plate schematic, abbreviations, and steelwork standard notes.

---

## 3. Parametric Generation for Any Project
To generate project-specific sheets `003`–`007` directly from a project's `design_basis.yaml` and `document_register.csv`:
```bash
python tools/cadgen/build_notes_and_details.py \
  --design-basis design-basis/<PROJECT>/design_basis.yaml \
  --register design-basis/<PROJECT>/document_register.csv \
  --standards Structural-Drawing-Standards \
  --out design-basis/<PROJECT>/output/cad \
  [--overrides design-basis/<PROJECT>/notes_overrides.yaml]
```
Or generate the full 7-sheet general package (`001` Cover, `002` Drawing List, `003`–`007` General Notes & Standard Details) in one command via `build_sheets.py --include-notes-details`.

