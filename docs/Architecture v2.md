# Architecture v2 - Bonded PT Band Beam & Slab Designer

Status: PROPOSED (16-OCT-2026). Replaces `mermaid-diagram.png`, `Import pipeline.png` and `Tendon design workflow.png`.
Companion to [Development Plan v2.md](Development%20Plan%20v2.md).

Legend: solid arrow = data flow; dotted arrow = Claude tool call; `[[ ]]` = exists in this repo today; hexagon = human decision.

## 1. System architecture

```mermaid
flowchart TB
    subgraph IN["Inputs"]
        DB[("Project design basis<br/>design-basis/#lt;CODE#gt;.yaml<br/>+ #lt;CODE#gt;.pt.yaml")]
        REG[("Design-code registry<br/>editions, NA, factors<br/>status per value")]
        PTS[("Approved PT system data<br/>supplier / ETA")]
        CAD["DXF / DWG layout"]
    end

    subgraph GEO["Geometry"]
        IMP["CAD import + classification"]
        GREV{{"Engineer geometry<br/>review + correction"}}
        GM["Validated geometry model"]
    end

    subgraph ANA["Analysis (replaceable adapter)"]
        AD["Analysis adapter"]
        EXT[["SAFE / ETABS result import<br/>tools/etabs/ - first adapter"]]
        FEA["In-house FE solver<br/>later, separate research track"]
        RES[("Analysis result store<br/>+ input snapshot + SHA-256")]
    end

    subgraph DES["Design engine (deterministic, calc_lib/)"]
        TG["Tendon geometry + profiles"]
        LOSS["Prestress losses<br/>friction, wobble, draw-in,<br/>elastic, creep, shrinkage, relaxation"]
        EQ["Equivalent prestress actions"]
        SLS["SLS: stresses, decompression,<br/>deflection, long-term"]
        ULS["ULS: flexure, shear,<br/>punching, anchorage zone"]
        RC["Conventional reinforcement<br/>+ detailing + clash checks"]
        VER["Verification record<br/>PASS / FAIL / NOT EVALUATED /<br/>BLOCKED / WARNING / REVIEW REQUIRED"]
    end

    BM[["Benchmark + regression suite<br/>tests/"]]

    subgraph DOC["Deliverables (from the same design data)"]
        DWG[["DXF sheets + preview PDF<br/>tools/cadgen/"]]
        CALC[["Calc report DOCX/PDF<br/>tools/docgen/"]]
        XLS[["Workbooks / schedules<br/>tools/xlsxgen/"]]
        SPEC[["Specification<br/>tools/docgen/"]]
        QA[["Package QA<br/>tools/qa/"]]
    end

    REV{{"Checker review<br/>+ engineer approval<br/>(human only)"}}
    ISS["Issued package + register<br/>tools/doc_control/"]

    subgraph AI["Claude orchestration (server-side)"]
        CL["Claude"]
        TOOLS["Tool layer<br/>schema-validated, implemented tools only"]
    end

    CAD --> IMP --> GREV --> GM
    DB --> GM
    GM --> AD
    DB --> AD
    REG --> AD
    AD --> EXT
    AD -.-> FEA
    EXT --> RES
    FEA --> RES

    RES --> TG
    DB --> TG
    PTS --> LOSS
    REG --> SLS
    REG --> ULS
    TG --> LOSS --> EQ
    EQ -- "prestress load cases<br/>(iteration loop)" --> AD
    RES --> SLS
    RES --> ULS
    EQ --> SLS
    SLS --> RC
    ULS --> RC
    RC --> VER
    SLS --> VER
    ULS --> VER
    BM -. "gates changes to" .-> DES
    BM -. "gates changes to" .-> AD

    VER -- "verified design data<br/>(DRAFT)" --> DWG
    VER --> CALC
    VER --> XLS
    VER --> SPEC
    DWG --> QA
    CALC --> QA
    XLS --> QA
    SPEC --> QA
    QA --> REV
    VER --> REV
    REV -- "approved" --> ISS
    REV -- "comments / rejected" --> GREV

    CL -.-> TOOLS
    TOOLS -.-> IMP
    TOOLS -.-> AD
    TOOLS -.-> DES
    TOOLS -.-> DOC
    TOOLS -. "read only" .-> VER

```

Rules the diagram encodes:

- Claude reaches engines only through the tool layer. It has no path to `REV` or `ISS` and cannot write to `VER`.
- Deliverables are generated as DRAFT from verified data so the checker can review them; approval comes after, and only from a person.
- Prestress actions go back into the analysis (the iteration loop), they are not added on top of the results.
- Every review, run, check result, approval and issue goes to the audit log. Any change to the design basis, geometry, PT data or code registry marks downstream results and deliverables stale.
- The in-house FE solver is optional and sits behind the same adapter; v1 does not depend on it.

## 2. CAD import pipeline

```mermaid
flowchart TB
    U["Upload DWG or DXF"] --> V{"Format, size,<br/>units valid?"}
    V -- "no" --> R1["Reject with reason"]
    V -- "DXF" --> P
    V -- "DWG" --> C{"DWG converter<br/>installed + tested?"}
    C -- "no" --> R2["Ask for DXF export<br/>(no native DWG claim)"]
    C -- "yes" --> CV["Convert to DXF<br/>(ODA / AutoCAD batch)"] --> P
    P["Parse supported entities<br/>block transforms, units"] --> UN["Report unsupported entities"]
    UN --> L["Read layers + blocks"] --> CLS["Classify geometry<br/>(layer + geometric rules;<br/>Claude may suggest, never decides)"]
    CLS --> M["Map structural elements<br/>grids, columns, walls, bands,<br/>slab edges, openings, drops"]
    M --> GV{"Geometry validation"}
    GV -- "fatal errors" --> BLK["BLOCKED - list elements<br/>+ corrective action"] --> ER
    GV -- "warnings / ok" --> ER{{"Engineer review<br/>+ correction"}}
    ER -- "edits" --> GV
    ER -- "confirmed" --> GM["Validated geometry model<br/>(snapshot + checksum)"]
    GM --> AM["Analysis adapter input"]
```

Changes from `Import pipeline.png`: reject paths for invalid files and missing DWG converter; unsupported entities reported; validation is a gate with a BLOCKED path; review loops back through validation; geometry is snapshotted before analysis.

## 3. Tendon design workflow

```mermaid
flowchart TB
    A["Validated geometry + loads<br/>+ approved PT system data"] --> B["Trial slab + band beam sizing<br/>(trial values, not results)"]
    B --> C["Design strips + band beam paths"]
    C --> D["Trial prestress demand"]
    D --> E["Tendon + duct arrangement"]
    E --> F["Tendon profiles + stressing ends"]
    F --> G["Prestress losses<br/>(short + long term)"]
    G --> H["Equivalent prestress actions"]
    H --> I["Run / import analysis<br/>with prestress load cases"]
    I --> J["SLS: stresses + deflections<br/>at transfer and service"]
    J --> K["ULS + conventional reinforcement<br/>+ detailing + clash checks"]
    K --> L{"Result of every<br/>mandatory check"}
    L -- "any FAIL" --> N{"Iteration limit<br/>reached?"}
    N -- "no" --> O["Adjust design variables<br/>(recorded iteration)"] --> E
    N -- "yes" --> P["DESIGN FAILED<br/>report reasons + options"]
    L -- "any NOT EVALUATED /<br/>BLOCKED" --> Q["Incomplete - list missing<br/>method, data or clause"]
    L -- "all PASS" --> S["Verified design data (DRAFT)"]
    S --> T["Generate draft deliverables"]
    T --> U{{"Independent check<br/>+ engineer approval"}}
    U -- "comments" --> O
    U -- "approved (human)" --> W["Issue"]
```

Changes from `Tendon design workflow.png`: SLS and ULS are in sequence (the original jumped from deflections straight to the top of the ULS box); prestress feeds into the analysis; three outcomes instead of yes/no (FAIL, NOT EVALUATED/BLOCKED, PASS); iteration limit and a design-failed exit; deliverables are drafted before approval, and approval is a human step.
