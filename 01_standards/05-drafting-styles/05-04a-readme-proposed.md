# 05-04a Layer Extensions - APPROVED (user, 14-OCT-2026)

`05-04-layer-standards.csv` (approved, 10 layers) has no layers for the sheet border, title block, tables or schematic views.
`05-04a-layer-extensions-proposed.csv` adds the five layers needed to generate the cover page and drawing list.
Weights follow `05-03` (border 0.50 = thick; title block lines 0.25 = thin; text/table 0.18). Colour 7 (black), Continuous.
Nothing in `05-04` was changed. Approve, edit or reject this file; the CAD generator reads both files and reports any layer outside them.
Linetype names: the company CSV says `Centre` / `Phantom`; the DXF generator maps these to the standard `CENTER` / `PHANTOM` linetypes.

Approved by P.Liheng (stated in chat) 14-OCT-2026. File name keeps the `_PROPOSED` suffix so existing references still resolve.
