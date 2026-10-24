# pt_profile_data.json (input of `04_tools/cadgen/pt_profiles.py`)

Lengths in cm along the tendon (`u`), heights in cm (`z` from the lowest soffit datum, `h` above the local soffit).

| Key | Content |
|---|---|
| `file_prefix` | output file stem |
| `v_den` | vertical scale denominator (25 for 1:25) |
| `title_block` | title-block attributes (DRAWING_NAME and SCALE are set per sheet by the tool) |
| `sheets` | [{number, title, marks: [..], den_candidates?, titles: [{text, x, y, style}]}]; the tool picks the largest horizontal scale that fits. `{den}` in a title text is replaced by it |
| `profiles` | {mark: profile} |
| `plan_lengths` | optional {mark: [[group, length_m], ...]} to print the plan label length and flag differences |
| `labels` | optional {profile, plan, verify, plan_offset_m} header texts and the plan-label offset rule |
| `notes` | {x, y, pitch, lines} |

## Profile object
- `stations`: [{u, sp, h}] chainage, spacing from the previous station, tendon height above the local soffit. The spacings must add to the last `u` (build stops otherwise).
- `section`: {soffit: [[u0, u1, z], ...], top: [[u0, u1, z], ...]} stepped outline of the section.
- `curve`: optional [[u, z], ...] drawn tendon curve. If absent, the curve is the polyline soffit(u) + h through the stations. For a design with parabolic or other profiles supply `curve`; the generator does not compute a profile shape.
- `supports`: optional list of support chainages.

Each station gets a label above (spacing) and below (height). For a new design the stations and heights come from the PT analysis, not from this tool.

## Redraft pattern
`03_projects/PJR-2F-PT/redraft/profiles/convert_profiles_to_pt_data.py` smooths the traced PDF geometry once and stores the result as `section` and `curve`. The data file is 60 KB against 1.4 MB for the raw trace.
