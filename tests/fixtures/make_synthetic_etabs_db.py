"""SYNTHETIC TEST FIXTURE - NOT A REAL MODEL. A tiny SQLite file imitating the table/column names seen in one real exported .db
(GDT_CleanV3.db, ETABS 22.1.0). Values are invented. build(path, **defects) breaks one thing per keyword."""
import sqlite3


def build(path, **d):
    c = sqlite3.connect(path)
    mk = lambda t, cols, rows: (c.execute(f'create table "{t}" ({", ".join(chr(34) + k + chr(34) for k in cols)})'),
                                c.executemany(f'insert into "{t}" values ({",".join("?" * len(cols))})', rows))
    info = [("ModelFile", "SYNTHETIC.EDB"), ("PresentUnits", "N_mm_C"), ("DataUnits", "N_furlong_C" if d.get("bad_units") else "N_mm_C"),
            ("IncludesResults", "Yes" if d.get("results_flag") else "No"), ("ExporterVersion", "2"), ("ExportedAt", "2026-10-14 10:00:00")]
    if d.get("no_modelinfo"):
        info = []
    mk("_ModelInfo", ["Key", "Value"], info)
    mk("_Tables", ["TableKey", "TableName", "SqlTable", "ImportType", "TableVersion", "RecordCount", "Status"],
       [("a", "Joint Reactions" if d.get("results_flag") else "Story Definitions", None, None, None, 1, "OK"), ("b", "Options - Colors - Display", None, None, None, 3, "Error: bad" if d.get("failed_table") else "OK")])
    if d.get("results_flag"):
        mk("Joint_Reactions", ["Output Case", "FZ"], [("DL", 1.0)])
    mk("Program_Control", ["ProgramName", "Version", "CurrUnits", "StlFrmCode", "ConcFrmCode", "CompBmCode", "CompColCode", "ConcSlbCode", "ShrWallCode"],
       [("ETABS", "22.1.0", "kN, m, C", "EN 1993-1-1:2005", "Eurocode 2-2004", "Eurocode 4-2004", "Eurocode 4-2004", "Eurocode 2-2004", "Eurocode 2-2004")])
    mk("Project_Information", ["ClientName", "ProjectName", "ModelName"], [(None, None, "SYN")])
    mk("Story_Definitions", ["Tower", "Story", "Height"], [("T1", "L1", 3000.0), ("T1", "L2", 3000.0)])
    pts = [(1.0, "L1", 0, 0, 0), (2.0, "L1", 5000, 0, 0), (3.0, "L2", 0, 0, 3000), (4.0, "L2", 5000, 0, 3000)]
    mk("Point_Object_Connectivity", ["UniqueName", "Story", "X", "Y", "Z"], pts + ([(4.0, "L2", 9, 9, 9)] if d.get("dup_joint") else []))
    cols = [(10.0, "L1", 1.0, 3.0, 3000.0), (11.0, "L1", 2.0, 4.0, 3000.0)]
    mk("Column_Object_Connectivity", ["UniqueName", "Story", "UniquePtI", "UniquePtJ", "Length"], cols if not d.get("bad_joint") else [(10.0, "L1", 1.0, 99.0, 3000.0), cols[1]])
    mk("Beam_Object_Connectivity", ["UniqueName", "Story", "UniquePtI", "UniquePtJ", "Length"], [(12.0, "L2", 3.0, 4.0, 5000.0)])
    sect = "MISSING-SEC" if d.get("missing_section") else "C400"
    mk("Frame_Assignments_Summary", ["Story", "Label", "UniqueName", "Type", "Length", "AnalysisSect", "DesignSect"],
       [("L1", "C1", 10.0, "Column", 3000.0, sect, sect), ("L1", "C2", 11.0 if not d.get("dup_unique") else 10.0, "Column", 3000.0, "C400", "C400"), ("L2", "B1", 12.0, "Beam", 5000.0, "B300", "B300")])
    mk("Frame_Section_Property_Definitions_Summary", ["Name", "Material", "Shape"], [("C400", "C30/37", "Concrete Rectangular"), ("B300", "C30/37" if not d.get("bad_material") else "C99/99", "Concrete Rectangular")])
    mk("Material_Properties_General", ["Material", "Type"], [("C30/37", "Concrete"), ("SD500", "Rebar")])
    mk("Joint_Assignments_Restraints", ["Story", "Label", "UniqueName", "UX", "UY", "UZ", "RX", "RY", "RZ"], [] if d.get("no_supports") else [("L1", 1.0, 1.0, "Yes", "Yes", "Yes", "Yes", "Yes", "Yes"), ("L1", 2.0, 2.0, "Yes", "Yes", "Yes", "Yes", "Yes", "Yes")])
    mk("Load_Pattern_Definitions", ["Name", "Type", "SelfWtMult"], [("DL", "Dead", 1.0), ("LL", "Live", 0.0), ("WX", "Wind", 0.0)])
    mk("Load_Case_Definitions_Summary", ["Name", "Type"], [("DL", "Linear Static")] + ([] if d.get("missing_case") else [("LL", "Linear Static")]) + [("WX", "Linear Static")])
    mk("Load_Case_Definitions_Linear_Static", ["Name", "LoadType", "LoadName", "LoadSF"], [("DL", "Load", "DL", 1.0), ("LL", "Load", "LL", 1.0), ("WX", "Load", "WXX" if d.get("undefined_pattern") else "WX", 1.0)])
    f_ll = 1.35 if d.get("wrong_factor") else 1.5
    cb = [("ULS-1", "Linear Add", "DL", 1.35), ("ULS-1", None, "LL", f_ll)]
    if d.get("undefined_term"):
        cb.append(("ULS-1", None, "GHOST", 1.0))
    mk("Load_Combination_Definitions", ["Name", "Type", "LoadName", "SF"], cb)
    c.commit()
    c.close()


MEMBERS = "etabs_label,project_member_id\nC1,COL-1\nC2,COL-2\nB1,BM-1\n"
EXPECTED = "cases:\n  - name: DL\n  - name: LL\ncombos:\n  - name: ULS-1\n    terms: {DL: 1.35, LL: 1.5}\n"
