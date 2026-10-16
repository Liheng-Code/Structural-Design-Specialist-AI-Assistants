"""Order-independent signature of a DXF modelspace (type, layer, rounded geometry / text) for regression comparison."""
from collections import Counter
import ezdxf


def _r(v, n=2):
    return round(float(v), n)


def signature(path) -> Counter:
    doc = ezdxf.readfile(path)
    sig = Counter()
    for e in doc.modelspace():
        t, la = e.dxftype(), e.dxf.layer
        if t == "LINE":
            a, b = (_r(e.dxf.start.x), _r(e.dxf.start.y)), (_r(e.dxf.end.x), _r(e.dxf.end.y))
            k = (t, la, tuple(sorted([a, b])))
        elif t == "LWPOLYLINE":
            k = (t, la, bool(e.closed), tuple((_r(x), _r(y)) for x, y, *_ in e.get_points()))
        elif t == "CIRCLE":
            k = (t, la, _r(e.dxf.center.x), _r(e.dxf.center.y), _r(e.dxf.radius))
        elif t == "TEXT":
            p = e.dxf.align_point if e.dxf.hasattr("align_point") and e.dxf.halign + e.dxf.valign else e.dxf.insert
            k = (t, la, e.dxf.text, _r(p.x), _r(p.y), _r(e.dxf.height), _r(e.dxf.get("rotation", 0)))
        elif t == "INSERT":
            k = (t, la, e.dxf.name, tuple(sorted((a.dxf.tag, a.dxf.text) for a in e.attribs)))
        elif t == "HATCH":
            k = (t, la, e.dxf.pattern_name, len(e.paths))
        elif t == "SOLID":
            k = (t, la, tuple((_r(v.x), _r(v.y)) for v in e.vertices()))
        else:
            k = (t, la)
        sig[k] += 1
    return sig


def diff(a, b):
    return {"only_old": list((a - b).items())[:10], "only_new": list((b - a).items())[:10], "n_old": sum(a.values()), "n_new": sum(b.values())}
