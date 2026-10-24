PT DETAILING, ARRANGEMENT & PROFILE SKILL
1. PURPOSE

SYSTEM: BONDED POST-TENSIONING ONLY. (Changed from unbonded to bonded on 16-OCT-2026 on the user's instruction. Every item below applies to bonded tendons: strands in grouted ducts. Do not use unbonded / mono-strand detailing.)

This skill is responsible exclusively for generating and checking the detailing, plan arrangement, tendon layout, anchorage layout, and tendon profile of a bonded post-tensioned concrete slab / band-beam system.

Scope

The skill shall control:

PT tendon plan arrangement
Band tendon arrangement
Distributed tendon arrangement
Tendon spacing
Tendon offsets
Column/support relationship
Anchorage locations
Live-end / dead-end arrangement
Tendon grouping
Tendon identification
Edge conditions
Opening avoidance
Core/wall interaction
MEP exclusion zones
Tendon profile
High points
Low points
Profile transition
Cover
Eccentricity
Tendon/rebar clearance
Anchorage-zone detailing
Tendon chair/support locations
Grout inlet / vent / drain locations
Construction/detailing checks
PT plan drawing
PT profile drawing
PT sections/details
Out of Scope

This skill does not independently perform:

Global structural analysis
Full slab design
Full band-beam design
PT force optimization
Complete prestress-loss calculation
Full punching design
Full shear design
Full reinforcement design

Those calculations provide the engineering inputs to this detailing module.

2. DESIGN PHILOSOPHY

The default PT arrangement shall be:

             COLUMN / SUPPORT LINE
                    │
        ┌───────────┼───────────┐
        │       BAND TENDONS    │
        │   T T T T T T T T     │
        │                       │
        │   D     D     D       │
        │                       │
        │   D     D     D       │
        │                       │
        │   D     D     D       │
        │                       │
        └───────────────────────┘

        T = Band Tendon
        D = Distributed Tendon

The system shall not distribute all tendons uniformly across the slab.

Instead:

Band Tendons

Concentrated near:

column lines
primary support lines
band beams
major moment/support regions
Distributed Tendons

Distributed through:

slab field
secondary span regions
middle areas between band lines

The final arrangement must satisfy both:

Structural efficiency + constructability

3. INPUT DATA REQUIRED

The detailing engine shall receive a structured geometry model.

3.1 Structural Geometry
project:
  floor_level:
  grid_system:
  slab_thickness:
  band_beam_width:
  band_beam_depth:

columns:
  id:
  x:
  y:
  width:
  depth:

walls:
  id:
  geometry:

openings:
  id:
  geometry:

edges:
  slab_boundary:
4. PT SYSTEM PARAMETERS
pt_system:

  tendon_type: bonded

  strand:
    diameter:
    area:
    grade:
    tensile_strength:
    modulus:

  tendon:
    strands_per_tendon:
    outer_diameter:

  anchorage:
    type:
    dimensions:
    edge_distance:
    minimum_spacing:

  duct:
    type:               # flat / round
    outer_dimension:    # H x W for a flat duct
    grout_vent_spacing:

  chair:
    type:
    spacing:

The values must come from:

Approved project PT system
Manufacturer
Project specification
Applicable standards

The AI shall never invent manufacturer-specific detailing dimensions.

5. PLAN ZONING

Every slab shall first be divided into PT detailing zones.

┌──────────────────────────────────────────────┐
│                SLAB EDGE ZONE                │
│                                              │
│    DISTRIBUTED TENDON ZONE                   │
│                                              │
│       ┌──────── BAND ZONE ────────┐          │
│       │ T  T  T  T  T  T  T      │          │
│       └───────────────────────────┘          │
│                                              │
│             OPENING ZONE                     │
│                                              │
└──────────────────────────────────────────────┘
Zone Types
ZONE-A  Anchorage Zone
ZONE-B  Column / Support Zone
ZONE-C  Band Tendon Zone
ZONE-D  Distributed Tendon Zone
ZONE-E  Opening Exclusion Zone
ZONE-F  Slab Edge Zone
ZONE-G  Core / Wall Zone
ZONE-H  MEP Exclusion Zone

Each tendon must belong to one or more relevant zones.

6. BAND TENDON ARRANGEMENT
6.1 Band Identification

For each structural bay:

Identify column/support centerline.
Identify column faces.
Identify band beam centerline.
Determine band width.
Determine usable tendon width.
Determine required band tendon force.
Determine tendon quantity.
Determine strands per tendon.
Arrange tendon group.
Check spacing.
Check offsets.
Check anchorage.
Check openings.
Check reinforcement congestion.
7. BAND TENDON GROUP

The default arrangement is:

              BAND WIDTH
        <────────────────────>

             T T T T T
             ↑ ↑ ↑ ↑ ↑
             │ │ │ │ │
             │ │ │ │ │
             │ │ │ │ │
             └─┬─────┬─┘
               │     │
          symmetric about
          band centerline

The tendon group should normally be approximately centered about the band centerline.

Where geometry permits:

        │<──── BAND ────>│
        │                │
        │ T  T  T  T  T  │
        │                │
        └──────┬─────────┘
               │
          BAND CENTERLINE

Asymmetry is permitted only when caused by:

opening
slab edge
core/wall
column geometry
transfer condition
anchorage restriction
MEP zone
reinforcement congestion
structural analysis
construction requirement

The reason for asymmetry shall be recorded.

8. COLUMN-FACE OFFSET

This is an important detailing parameter.

The system shall distinguish:

A. Column centerline
             │
             │
        COLUMN CL
             │
B. Column face
        ┌─────────────┐
        │             │
        │   COLUMN    │
        │             │
        └─────────────┘
          ↑         ↑
       face-L     face-R
C. Tendon / Anchorage reference

The system shall calculate:

Column Face
     │
     │<───── offset ─────>│
     │                    ●
     │                 tendon/
     │                 anchorage

Store:

column_face_offset:
  left:
  right:

anchorage_offset:
  left:
  right:

The governing minimum shall be:

MAX(
    applicable code requirement,
    PT manufacturer requirement,
    anchorage requirement,
    reinforcement clearance,
    concrete placement requirement,
    project detailing requirement
)

The AI must not hard-code an arbitrary universal Eurocode value.

9. BAND TENDON SPACING

For every band tendon group calculate:

s_actual
s_min
s_max
Minimum spacing
s_min =
MAX(
    code minimum,
    manufacturer minimum,
    anchorage minimum,
    reinforcement clearance,
    concrete placement requirement,
    project detailing requirement
)
Maximum spacing
s_max =
MIN(
    applicable design/detailing limit,
    force distribution requirement,
    tributary width requirement,
    project limit
)

The drawing shall report:

BAND TENDON SPACING

T01 ──150── T02 ──150── T03 ──150── T04

Actual = 150 mm
Minimum = xxx mm
Maximum = xxx mm
Status = PASS
10. DISTRIBUTED TENDON ARRANGEMENT

Distributed tendons are located primarily within the slab field between band lines.

Example:

        BAND
══════════════════════════════
 T   T   T   T   T   T   T

 D       D       D       D

 D       D       D       D

 D       D       D       D

══════════════════════════════
        BAND

The distributed tendon layout shall be determined from:

slab geometry
span
tributary width
required PT force/m
flexural demand
serviceability
load balancing
openings
slab edges
MEP zones
construction constraints
11. DISTRIBUTED TENDON SPACING

For each distributed tendon group:

distributed_spacing:
  actual:
  minimum:
  maximum:
  governing_source:

The hierarchy shall be:

1. Applicable code
2. National Annex
3. Approved PT manufacturer
4. Anchorage/reinforcement requirements
5. Project specification
6. Construction requirements
7. Structural analysis

The system shall never create a fake statement such as:

"Eurocode requires distributed PT tendons at exactly XXX mm."

unless that requirement is actually supported by the adopted design basis.

12. SLAB EDGE OFFSET

Distributed tendons shall maintain an edge offset.

SLAB EDGE
│
│<──── edge offset ────>● T
│
│

Store:

edge_offset:
  actual:
  minimum:
  governing_requirement:

Check:

actual edge clearance >= governing minimum
13. OPENING DETAILING

Openings shall automatically generate exclusion zones.

       T      T
────────────────────

       ┌──────────┐
       │ OPENING  │
       │          │
       └──────────┘

────────────────────
       T      T

No tendon shall pass through an opening unless explicitly approved.

The system shall calculate:

opening clearance
tendon deviation
local tendon congestion
additional reinforcement zone

For larger openings:

        T       T
────────┐     ┌────────
        │     │
        │OPEN │
        │ING  │
        │     │
────────┘     └────────
        T       T

The layout engine shall attempt to:

shift tendon
redistribute tendon
maintain spacing
preserve required PT force
avoid excessive concentration
flag engineering review if impossible

14. TENDON NUMBERING

Every tendon receives a unique ID.

Recommended:

B01-T01
B01-T02
B01-T03

D01-T01
D01-T02
D01-T03

Where:

B = Band
D = Distributed
01 = tendon zone/group
T = tendon

Example:

B03-T07 = Band Group 03, Tendon 07
D02-T14 = Distributed Group 02, Tendon 14

The same ID must appear on:

plan
profile
section
tendon schedule
calculation model
ADAPT model mapping
15. STRAND CONFIGURATION

The system shall select tendon configuration from the approved PT library.

Example:

3S13
4S13
5S13
6S13
7S13

The selection shall consider:

Required PT force
        ↓
Available strand capacity
        ↓
Required number of tendons
        ↓
Available band width
        ↓
Minimum spacing
        ↓
Anchorage capacity
        ↓
Constructability

The algorithm shall prefer:

More constructible tendon groups rather than excessive strands concentrated into a small number of tendons, unless analysis or approved system requirements dictate otherwise.

16. TENDON ARRANGEMENT OPTIMIZATION

The arrangement engine shall attempt to optimize:

Structural efficiency
+
Balanced PT distribution
+
Minimum congestion
+
Simple construction
+
Simple stressing
+
Clear tendon identification
+
ADAPT compatibility

Objective:

MINIMIZE

Congestion
+ excessive deviation
+ irregular spacing
+ anchorage conflict
+ MEP conflict
+ unnecessary tendon changes

Subject to:

PT force requirement
Spacing requirements
Clearance requirements
Cover requirements
Profile requirements
Anchorage requirements
Opening constraints
Structural constraints

17. TENDON PLAN OUTPUT

The PT plan shall contain:

General
Grid
Column/wall/core
slab boundary
openings
band beams
tendon IDs
tendon direction
tendon groups
Band Tendons
tendon ID
number of strands
tendon centerline
spacing
support relationship
anchorage
stressing end
Distributed Tendons
tendon ID
number of strands
spacing
slab field
anchorage
stressing end
Dimensioning

Show:

Column face → tendon
Tendon → tendon
Tendon → slab edge
Tendon → opening
Tendon → core/wall
Anchorage → edge
18. TENDON PROFILE

The tendon profile is not simply a graphic curve.

It is an engineered geometric model.

Typical profile:

Elevation

 High                High
   ●──────────────────●
    \                /
     \              /
      \            /
       \          /
        \        /
         \      /
          \    /
           \  /
            ●
          Low
        Midspan

Typical bonded PT slab profile:

High over support
        ●
       / \
      /   \
─────/─────\─────
   support
Low at midspan
──────\     /──────
       \   /
        \ /
         ●
      midspan

The actual profile must be calculated from:

slab thickness
band beam depth
required eccentricity
cover
duct size (the duct, not the strand, sets the cover and clearance)
reinforcement
structural demand
load balancing
deflection
support geometry
anchorage geometry
grout vent / drain positions (vents at high points, drains at low points)
19. PROFILE DATUM

Every profile must explicitly state its datum.

Possible datum:

FFL
Structural Top of Slab
Structural Bottom of Slab
Band Beam Top
Band Beam Bottom

Recommended drawing notation:

PROFILE DATUM = TOP OF STRUCTURAL SLAB
EL. = +XX.XXX

Never show tendon elevations without identifying the reference datum.

20. PROFILE CONTROL POINTS

Each tendon shall have defined control points.

Minimum standard:

P01 = Anchorage
P02 = End transition
P03 = Support high point
P04 = Quarter span
P05 = Midspan low point
P06 = Quarter span
P07 = Support high point
P08 = End transition
P09 = Anchorage

Example:

        P03                    P07
         ●                      ●
        / \                    / \
       /   \                  /   \
──────●─────\──────●─────────/─────●──────
 P02          P05             P08
              LOW

For irregular geometry, additional points are required.

21. SUPPORT HIGH POINT

The high point shall not automatically be placed at an arbitrary location.

Possible locations:

Column centerline
Column face
Inside support zone
Band beam centerline
Other calculated location

Selection shall consider:

structural moment diagram
required eccentricity
tendon cover
reinforcement
anchorage
band geometry
minimum radius
construction

The actual location must be stored:

support_high_point:
  x:
  y:
  elevation:
  reference:
  reason:
22. MIDSPAN LOW POINT

The low point shall be determined from:

required eccentricity
slab thickness
bottom cover
duct size
reinforcement
deflection
load balancing
construction clearance

Store:

midspan_low_point:
  x:
  y:
  elevation:
  eccentricity:
23. PROFILE SHAPE

The profile engine may use:

Option A — Parabolic

Suitable for regular spans.

      ●
     / \
    /   \
   /     \
  /       \
 ●         ●
Option B — Circular / smooth arc

Where appropriate.

Option C — Piecewise polynomial

For irregular geometry.

Option D — Piecewise linear

Only where permitted by the adopted detailing system and construction method.

The profile must preserve:

Position
Elevation
Cover
Eccentricity
Tangency
Curvature
Minimum radius
Anchorage geometry
Constructability
24. PROFILE CONSTRAINTS

For every tendon:

profile_constraints:

  top_of_slab:
  bottom_of_slab:

  top_cover:
  bottom_cover:

  duct_outer_dimension:

  tendon_centroid:

  eccentricity:

  minimum_radius:

  maximum_slope:

  high_point:

  low_point:

  transition_length:

The actual values shall be derived from the adopted design basis and PT system.

25. COVER CHECK

For every profile control point:

Available concrete depth
        ↓
Duct outer dimension
        ↓
Required cover
        ↓
Required reinforcement clearance
        ↓
Available tendon position

Check:

Actual cover >= governing minimum

Status:

PASS
WARNING
FAIL
26. TENDON / REINFORCEMENT CLEARANCE

The profile engine must check:

Tendon
   ↓
Concrete
   ↓
Rebar

and:

Tendon ↔ Tendon
Tendon ↔ Rebar
Tendon ↔ Anchorage
Tendon ↔ Opening
Tendon ↔ MEP

No tendon profile is accepted merely because it fits inside the slab thickness.

It must also be constructible.

27. TENDON PROFILE DRAWING

Each profile should show:

Tendon ID
Span
Grid
Support
High point
Low point
Anchorage
Elevation
Cover
Eccentricity
Datum
Control points
Grout vents (high points) and drains (low points)

Example:

T01 — 4S13

        +XXX.XXX
          ●  HIGH
         / \
        /   \
───────/─────\──────────────
      /       \
     /         \
    ●           ●
  LOW          HIGH

  +XXX.XXX

DATUM = TOP OF STRUCTURAL SLAB
28. ANCHORAGE DETAILING

The layout must distinguish:

LIVE END
DEAD END

Example:

LIVE END ───────────────────── DEAD END
   ●                              ●
   │                              │
   └────────── T01 ───────────────┘

Each tendon record:

anchorage:
  start_type:
  end_type:
  start_location:
  end_location:
  stressing_access:
  grout_inlet_vent_access:

Check:

edge distance
anchorage spacing
local reinforcement
stressing access
grout inlet / vent access
dead-end geometry
tendon continuity
congestion
29. CHAIR / SUPPORT DETAILING

The profile shall be converted into physical support locations.

Duct
   ●
   │
   │ duct chair
   │
───┴──────── slab

Chair locations shall be determined from:

profile control points
tendon slope
construction requirements
manufacturer requirements
profile stability

The drawing shall not show an abstract curve without a practical means of supporting the duct at the required elevation.

30. PROFILE-TO-PLAN CONSISTENCY

This is mandatory.

The plan and profile must reference the same tendon ID.

Example:

PLAN
B01-T04
     │
     ▼
PROFILE
B01-T04
     │
     ▼
SECTION
B01-T04
     │
     ▼
SCHEDULE
B01-T04

No duplicated or conflicting tendon IDs are allowed.

31. DETAILING QA/QC

Before producing the final drawing, run:

Plan
 All tendons have IDs
 Band tendons identified
 Distributed tendons identified
 Spacing checked
 Column-face offset checked
 Edge offset checked
 Opening clearance checked
 Core/wall clearance checked
 Anchorage checked
 Live/dead ends identified
 Strand quantity identified
 Tendon direction clear
Profile
 Datum identified
 High points defined
 Low points defined
 Anchorage elevations defined
 Cover checked
 Eccentricity checked
 Tendon/rebar clearance checked
 Tendon/tendon clearance checked
 Minimum radius checked
 Profile transitions checked
 Chair/support locations checked
 Grout vents / drains located
Cross-consistency
 Plan ID = Profile ID
 Profile span = Plan span
 Anchorage locations agree
 Tendon quantity agrees
 Strand count agrees
 Geometry agrees
 Elevations agree
32. DETAILING STATUS

Each tendon arrangement receives one status:

VALID

All requirements satisfied.

VALID WITH WARNING

Minor non-critical issue requiring review.

ENGINEER REVIEW

Engineering judgment required.

INVALID

Cannot generate final drawing.

The system shall never silently fix an invalid PT arrangement.

33. FINAL DRAWING STRUCTURE

For this detailing module, I would keep the drawing package very focused:

PT-D001
GENERAL PT DETAILING NOTES

PT-D002
PT TENDON PLAN — BAND ARRANGEMENT

PT-D003
PT TENDON PLAN — DISTRIBUTED ARRANGEMENT

PT-D004
PT ANCHORAGE PLAN

PT-D005
PT TENDON PROFILE

PT-D006
TYPICAL TENDON SECTIONS

PT-D007
BAND BEAM + SLAB PT DETAIL

PT-D008
OPENING / EDGE / CORE DETAILS

PT-D009
ANCHORAGE + STRESSING DETAILS

PT-D010
TENDON SCHEDULE
34. CORE PRINCIPLE

The AI must think of PT detailing as:

STRUCTURAL ANALYSIS
       │
       ▼
Required PT Force
       │
       ▼
Tendon Quantity / Strand Quantity
       │
       ▼
┌─────────────────────────────┐
│     PLAN ARRANGEMENT        │
│                             │
│  BAND + DISTRIBUTED         │
│                             │
│  spacing                    │
│  offsets                    │
│  openings                   │
│  anchorage                  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│       TENDON PROFILE        │
│                             │
│  high point                 │
│  low point                  │
│  eccentricity               │
│  cover                      │
│  curvature                  │
│  clearance                  │
└─────────────┬───────────────┘
              │
              ▼
       CONSTRUCTIBLE PT
           DRAWING
              │
              ▼
        ADAPT-BUILDER
         VERIFICATION
