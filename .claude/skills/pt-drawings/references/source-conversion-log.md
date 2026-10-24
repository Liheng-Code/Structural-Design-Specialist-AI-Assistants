# Source notes -> Eurocode conversion log (2F PT notes, 16-OCT-2026)

Instruction from the user: turn the two source note images into reusable general notes; change the design codes from BS to Eurocode; change the PT system to bonded; keep everything else. Where a value does not carry straight across, it is left as the source value or TBC and listed as an open item on the sheet.

| Source item | Treatment in the notes | Open item |
|---|---|---|
| LOAD: BS 6399 | EN 1990 and EN 1991-1-1 (parameter `codes.actions`) | PT-OI-01 |
| CONCRETE: BS 8110-1997 | EN 1992-1-1 (parameter `codes.concrete`) | PT-OI-01 |
| f'cu = 37 MPa (cube) | C30/37: fck = 30, fck,cube = 37 (EN 1992-1-1 Table 3.1 equivalent class) | PT-OI-02 |
| f'cui = 0.75 x f'cu = 28.75 MPa | not carried: 0.75 x 37 = 27.75, the source prints 28.75. Value at stressing left TBC for the engineer | PT-OI-03 |
| Nominal aggregate 20 mm | kept | - |
| DIA >= 10 deformed fy = 500 MPa, mark DB | kept, written fyk | - |
| DIA < 10 round fy = 235 MPa, mark RB | kept; not an EN 10080 B500 steel | PT-OI-04 |
| Clear cover 25 mm | kept; EN 1992-1-1 4.4.1 sets cnom from exposure class and bond, exposure class not given | PT-OI-05 |
| Strand: ASTM A416 Grade 270, low relaxation | kept as the source standard | PT-OI-06 |
| 7 wire, 12.70 mm, 98.70 mm2, 184 kN, 1860 MPa, Ep 1.95 x 10^5 MPa, elongation 3.5 % | kept (Ep printed as 195000 MPa because the caret prints badly in DXF text) | - |
| Yield strength 1670 MPa | kept; EN design uses the 0.1 % proof stress fp0.1k (supplier certificate), not converted | PT-OI-07 |
| Stressing design 140 kN | kept as jacking force per strand; validator prints the stress and the EN 1992-1-1 5.10.2.1 limit it compares with | PT-OI-13 |
| Friction coefficient 0.2 | kept | - |
| Wobble factor k = 0.003 /m | kept as printed; EN 1992-1-1 5.10.5.2 uses mu x (theta + k x) with k in rad/m and the source formula is unknown | PT-OI-08 |
| Wedge draw-in 6.0 mm; duct H 25 mm, W 55-80 mm | kept; supplier specific | PT-OI-09 |
| Loads blank | left TBC; the source plan states SDL = 250 KSM, LL = 500 KSM | PT-OI-10 |
| Rebar layer legends B1, B2, T1, T2 | slab-step detail order used (3RD = T1, 4TH = T2); first legend shows the reverse | PT-OI-11 |
| Strand symbols 1 to N | 2 circle, 3 triangle, 4 square, 5 diamond, N circle with N; 1-strand symbol not readable | PT-OI-12 |
| (PT system) | notes state POST-TENSIONING SYSTEM SHALL BE BONDED (the source plan sheet already says so) | - |

Clause numbers quoted above are from memory of EN 1992-1-1 and are NOT checked against the standard text. An engineer must check them before relying on them.
