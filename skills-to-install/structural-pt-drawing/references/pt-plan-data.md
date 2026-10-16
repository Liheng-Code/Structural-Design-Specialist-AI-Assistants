# pt_plan_data.json (input of `tools/cadgen/pt_plan.py`)

Plain JSON. Model coordinates are millimetres with the origin you choose (the 2F example uses grid 1 / grid A). Paper values are A3 millimetres.

| Key | Content |
|---|---|
| `scale_den` | plan scale denominator, e.g. 200 |
| `origin_paper_mm` | [x, y] paper position of model (0, 0) |
| `file_name` | output file stem |
| `title_block` | the 9 title-block attributes: PROJ_REFERENCE, DRAWING_NAME, REVISION, DRAWN_BY, DRAWING_NUMBER, DRAWING_STAGE, CLIENT, SCALE, ISSUE_DATE (from the design basis) |
| `titles` | [{text, x, y, style}] paper-space titles |
| `grid` | {x: [{name, pos}], y: [{name, pos}], style?: overrides} |
| `outlines` | [{pts, closed, layer}] slab, walls, voids (`S-CONC-OUTLINE`), drop panels / bands (`S-CONC-DROP`) |
| `blockouts` | [[x0, y0, x1, y1]] block-out strips (hatched, tagged B/O) |
| `columns` | [{tag, size, x, y}] square columns |
| `cross_boxes` | [{bbox, label, label_dy_mm}] shafts drawn with a cross |
| `tendon_lines` | [[[x, y], ...]] tendon polylines (`S-PT-TENDON`) |
| `tendons` | one object per tendon group, see below. The schedule and the CSV are built from this list |
| `tags_below` | {y_model, y_off_mm, pitch_mm} placement of Y-direction tendon tags |
| `side_offset_model` | model distance of X-direction tag columns outside the grid (default 600) |
| `labels` | [{text, x, y, dx_mm, dy_mm, align, rot}] free labels anchored in the model with a paper offset |
| `level_marks` | [{x, y, text}] |
| `dims` | h: {dir, ref_model, offset_mm, positions, labels}; v: {dir, paper \| (ref_model, offset_mm), positions, labels} |
| `schedule` | {title?, check_note?, legend: [lines], sections?} |
| `notes` | {x, y, pitch, lines: [text or {gap: n}]} |

## Tendon object
`group` (unique int), `mark`, `dir` ("X" or "Y"), `strands` (2-5), `first`, `last` (strand numbers; `last - first + 1` must equal `strands`), `length_m`.
X tendons also need `y` (model, duct position) and `side` ("L" or "R"). Y tendons need `anchor` [x, y] (model, lower end).
A missing field stops the build. Nothing is guessed.

## Redraft pattern
`redraft_2F_PT/convert_plan_to_pt_data.py` converts the hard-coded 2F tables and PDF-extracted lines into this format once. Regenerating from the data reproduces the 2F DXF element for element (tested).
