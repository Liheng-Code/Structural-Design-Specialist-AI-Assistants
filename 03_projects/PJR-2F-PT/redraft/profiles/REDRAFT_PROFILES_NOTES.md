# 2F PT tendon profiles - REDRAFT FOR REVIEW (16-OCT-2026)

Source: Success Design & Build, sheet 16 of 50, Rev 01, 22-AUG-2023. Faithful redraw, no design change. Not approved; engineer sign-off is human.

## Files
- `2F_PT_Profiles_X_REDRAFT.dxf` - X / EX direction (12 profiles), A3, H 1:250, V 1:25
- `2F_PT_Profiles_Y_REDRAFT.dxf` - Y direction (20 profiles), A3, H 1:400, V 1:25
- `2F_PT_Profiles_REDRAFT_preview.pdf` - script-rendered preview of both sheets (not a CTB plot)
- `2F_PT_Profiles_stations_TRANSCRIBED.csv` - every station: chainage, spacing, tendon height above soffit
- `redraft_2f_pt_profiles.py`, `profiles_2F_PT.json` - generator and extracted data

Two sheets instead of the one A3 sheet requested: 32 profiles with all station labels do not fit on one A3 sheet at a readable size.

## How the data was obtained
- Station spacings and heights: read from the vector text of the source PDF (glyph shapes, not OCR), 683 stations. Check: for all 32 profiles the sum of the spacings reproduces the drawn station positions (same scale on every profile, no residual above 3 px); heights agree with the drawn curve within 1.5 cm except at 11 stations that sit on a section step (label measured from the deeper soffit - checked by eye).
- Section outline and tendon curve: traced from the source geometry (about +/-1 cm vertical, +/-5 cm along the tendon). Support lines are the grey lines of the source.
- Mark names (X1.., Y1..): read by eye from the source.

## Not redrawn (TBC)
Grid reference bubbles on the profiles, span-length and section-thickness dimension labels, stressing / dead-end symbols, jacking force and losses (not on the source).

## Observation to verify with the designer (not a conclusion)
Profile length vs plan label length. The plan labels give the group length (drawn length + about 0.5 m). For most marks the sheet-16 profile of the same mark is a different length:

| Mark | Sheet-16 profile length (m) | Plan label length (m) | Plan drawn length (label - 0.5) | Stations | Result |
|---|---|---|---|---|---|
| X1 | 20.52 | 21.05 | 20.55 | 24 | matches |
| X2 | 47.80 | 36.05 | 35.55 | 57 | DIFFERS - verify |
| X3 | 47.20 | 48.90 | 48.40 | 55 | DIFFERS - verify |
| X4 | 10.52 | 48.25 | 47.75 | 13 | DIFFERS - verify |
| X5 | 11.20 | 20.15 | 19.65 | 13 | DIFFERS - verify |
| X6 | 10.52 | 20.65 | 20.15 | 13 | DIFFERS - verify |
| X7 | 11.20 | 20.15 | 19.65 | 13 | DIFFERS - verify |
| X8 | 20.10 | 20.65 | 20.15 | 24 | matches |
| EX1 | 14.34 | 14.85 | 14.35 | 20 | matches |
| EX2 | 12.10 | 12.95 | 12.45 | 14 | DIFFERS - verify |
| EX3 | 12.10 | 14.90 | 14.40 | 15 | DIFFERS - verify |
| EX4 | 12.40 | 12.95 | 12.45 | 16 | matches |
| Y1 | 21.20 | 9.45 | 8.95 | 26 | DIFFERS - verify |
| Y1A | 20.20 | 9.25 | 8.75 | 26 | DIFFERS - verify |
| Y2 | 20.20 | 9.00 | 8.50 | 24 | DIFFERS - verify |
| Y3 | 18.10 | 8.95 | 8.45 | 22 | DIFFERS - verify |
| Y4 | 15.60 | 20.75 | 20.25 | 18 | DIFFERS - verify |
| Y5 | 15.90 | 18.10 | 17.60 | 18 | DIFFERS - verify |
| Y6 | 18.20 | 18.60 | 18.10 | 21 | matches |
| Y7 | 19.20 | 18.10 | 17.60 | 23 | DIFFERS - verify |
| Y8 | 19.20 | 18.40 | 17.90 | 23 | DIFFERS - verify |
| Y9 | 18.20 | 20.70 | 20.20 | 21 | DIFFERS - verify |
| Y9A | 18.70 | 21.20 | 20.70 | 21 | DIFFERS - verify |
| Y10 | 18.70 | 20.70 | 20.20 | 21 | DIFFERS - verify |
| Y11 | 21.20 | 21.70 | 21.20 | 26 | matches |
| Y12 | 18.20 | 18.70 | 18.20 | 21 | matches |
| Y13 | 20.70 | 21.25 | 20.75 | 23 | matches |
| Y14 | 20.20 | 20.75 | 20.25 | 24 | matches |
| Y15 | 8.96 | 9.45 | 8.95 | 12 | matches |
| Y16 | 8.96 | 9.50 | 9.00 | 12 | matches |
| Y17 | 9.46 | 9.95 | 9.45 | 12 | matches |
| Y17A | 9.26 | 9.75 | 9.25 | 12 | matches |

13 of 32 marks match. Possible explanations: sheet-16 mark names are not the plan mark names, one profile is used for several tendons, or I mis-read a plan label. Please check this against the original drawings before relying on any profile.
