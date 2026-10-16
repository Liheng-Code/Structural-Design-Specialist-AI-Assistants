# CAD workflow and claim discipline

| Artifact | May be called | Requires |
|---|---|---|
| `.dxf` written by script | "DXF generated" | file exists, re-opened by a DXF reader, audit clean |
| `.dwg` | "DWG generated" | produced by AutoCAD / licensed converter AND opened successfully |
| `.pdf` | "PDF plotted" | plotted from the sheet with company plot style; pages rendered and inspected |
| PNG/SVG render | "preview" only | - |

## Validation checklist (per file)
Units mm; drawing extents inside sheet border; only layers from `05-04_Layer_Standards.csv` (plus approved additions); text heights from `05-01` (>= 2.0 mm on A3); lineweights from layer table; title block fields match design basis/register; no unresolved external references; fonts available (Arial); plot style present.

## Missing-tool flags
If AutoCAD, the company DWT template, CTB/STB plot style, title-block block definition or fonts are unavailable, say so explicitly and list them in the gap register. Do not substitute silently.

## Environment on record (Oct 2026)
Cloud workspace: Python, ezdxf, matplotlib, LibreOffice; no AutoCAD/ETABS/ODA. User PC: Autodesk and Graphisoft folders exist; installed CAD/ETABS versions NOT verified (`tools/cadgen/probe_cad.py` must be run there).

## What the preview PDF is
A matplotlib rendering of the DXF at true A3 size with layer lineweights applied (checked: 0.50 / 0.25 / 0.18 mm measure within 0.02 mm). It is not an AutoCAD plot: no CTB/STB, fonts substituted (Arial -> available sans), no xref handling. Call it a preview.
