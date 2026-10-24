# PT floor slab master ruleset - guide

Status: **DRAFT, UNVERIFIED** (imported 24-OCT-2026). No rule is accepted until an engineer reviews it (gap G33).

The rules themselves (IDs, text, parameters, basis, review notes) are in [pt-master-ruleset.yaml](pt-master-ruleset.yaml). This page explains how to use them.

**Source:** the user's Google Doc "Post-Tensioned Concrete Floor Slab Master Ruleset" (Drive id `1uswGptsC840d8DoSZPEr56YYV1UgwQgkRelrw_IJDOw`). It states that it is synthesised from EN 1992-1-1:2004, ACI 318 and B. Aalami technical notes TN451, TN454, TN458 and B124. Rule text and numbers were copied as written; nothing was added.

## Rule groups

| IDs | Topic | Count |
|---|---|---|
| PT-LAY-01 to 12 | Type A (banded-distributed) tendon layout: layout type, banded-direction selection, precompression, spacing, integrity tendons, band width, tendon profiles, rebar placement | 12 |
| PT-SHR-01 to 12 | Shortening, support restraint and crack mitigation: shortening estimate, length thresholds, 6 mm restraint limit, delay-strip duration, restraint by level, joints, releases, crack-control and trim bars | 12 |

## Basis of the rules

Most rules are **not Eurocode clauses**:

| Basis | Rules | Meaning for a Eurocode project |
|---|---|---|
| ACI | PT-LAY-03 (P/A 0.7-0.85 MPa), PT-LAY-07 (spacing 8h / 1.5 m), PT-LAY-08 (2 tendons through each column), PT-LAY-09 (band width) | Use only if the project adopts them; EN 1992-1-1 equivalents are checked separately |
| practice | All others (Aalami technical notes, US practice) | Guidance and design targets, not code requirements |

A rule never turns a check into PASS by itself. Values used in a design still come from the project design basis and PT basis.

## Choosing the banded direction (Type A)

1. **PT-LAY-05 column continuity** and **PT-LAY-06 slab bands** come first. If columns are continuous in one direction only, band along that line. If slab bands or wide shallow beams exist (h <= 2 t_slab, b >= 3h), band inside them.
2. Otherwise **PT-LAY-04 span length**: band along the long span, distribute along the short span.
3. If PT-LAY-05 and PT-LAY-06 point different ways, the source gives no order. The engineer decides.

## Conflicts with the "Design Template & Technical Specification" doc

| Topic | This ruleset | Design Template doc |
|---|---|---|
| Long-term shortening | ~10 mm per 15 m (~67 mm per 100 m), PT-SHR-02 | 15-35 mm per 100 m |
| Delay strip open time | 20-25 days (upper floors), 30-40 days (podium), PT-SHR-06 | 28-56 days |

Both must be resolved by the engineer before either value is used.

## Unclear rules to restate

- **PT-LAY-09:** band width "column + 1.5h each side **or** L_y/2". Is it the lesser or the greater, and which L_y?
- **PT-LAY-12:** "top rebar diameter should match the tendon duct size". This doesn't read as a meaningful engineering rule.
- **PT-SHR-06:** needs the TN451 time-shortening curve (Fig. Q.2.7-1), which isn't in the repo, before it can be automated.

## Rules that tools could apply later

Rules marked `automatable: true` in the YAML could be applied by tools: the banded-direction choice, spacing and band-width checks, length thresholds, the 6 mm restraint check and trim bars at corners. A DXF importer or SAFE/ADAPT model builder could use them to *suggest* a layout. They would only suggest; the engineer still confirms the layout at the review gate.
