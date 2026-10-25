"""Units for the engineering core (ADR-007).

Every quantity that crosses a module boundary is a pint Quantity. A module converts to its internal units on entry
(`to_internal`) and does plain-float arithmetic only after that. A dimension mismatch raises `DimensionError`; it is
never coerced. Bare numbers are rejected wherever a quantity is expected.

INTERNAL_UNITS: N, mm, MPa, decided by the user 25-OCT-2026 (ADR-007). Forces and moments are entered and reported in
kN and kN*m; they are converted here, never stored internally in kN (kN with mm and MPa is not a consistent set).
"""
from __future__ import annotations

import re
from typing import Any, Mapping

import pint

ureg: pint.UnitRegistry = pint.UnitRegistry()
Quantity = ureg.Quantity

# Decided 25-OCT-2026 (ADR-007). Quantity kind -> internal unit. The unit also fixes the kind's dimension.
INTERNAL_UNITS: Mapping[str, str] = {
    "dimensionless": "dimensionless",
    "strain": "dimensionless",
    "angle": "radian",
    "length": "mm",
    "area": "mm**2",
    "second_moment": "mm**4",
    "force": "N",
    "force_per_length": "N/mm",
    "pressure": "MPa",                  # stresses and area loads share this dimension
    "moment": "N*mm",
    "moment_per_length": "N*mm/mm",
    "unit_weight": "N/mm**3",
    "density": "kg/m**3",
    "time": "day",
    "curvature": "1/mm",
}


class DimensionError(ValueError):
    """A quantity has the wrong dimension, or a bare number was given where a quantity is required."""


def _unit(kind: str) -> pint.Unit:
    if kind not in INTERNAL_UNITS:
        raise KeyError(f"unknown quantity kind {kind!r}; known: {sorted(INTERNAL_UNITS)}")
    return ureg.Unit(INTERNAL_UNITS[kind])


# Text form: exactly one number, then one unit. Nothing is evaluated as arithmetic, so "55-80 mm" (a range) and
# "100 mm - 20 mm" are rejected instead of becoming -25 mm or 80 mm. A unit starts with a letter, a symbol, or "1/".
_TEXT = re.compile(r"^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*((?:1/|[^\W\d_]|[°%µ]).*?)\s*$")


def _parse_unit(text: str, original: Any) -> pint.Unit:
    rest = re.sub(r"(\*\*|\^)\s*-?\d+(\.\d+)?", "", text[2:] if text.startswith("1/") else text)
    if re.search(r"[\d+\-]", rest):                     # digits or signs left over: arithmetic, a range, or junk
        raise DimensionError(f"{original!r}: unit {text!r} looks like arithmetic or a range; give one value")
    try:
        return ureg.Unit(text)
    except (pint.PintError, ValueError, TypeError, AttributeError) as exc:
        raise DimensionError(f"{original!r}: {text!r} is not a unit ({exc})") from exc


def parse(value: Any) -> pint.Quantity:
    """Quantity from a Quantity, a {'value', 'unit'} mapping, or a string such as '12.5 kN'. Bare numbers fail."""
    if isinstance(value, pint.Quantity):
        return value
    if isinstance(value, Mapping):
        if set(value) != {"value", "unit"}:
            raise DimensionError(f"quantity mapping needs exactly 'value' and 'unit', got {sorted(value)}")
        v = value["value"]
        if v is None:
            raise DimensionError("quantity value is null; a missing value is handled by the caller, not converted")
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise DimensionError(f"quantity value must be a number, got {v!r}")
        return Quantity(float(v), _parse_unit(str(value["unit"]), value))
    if isinstance(value, str):
        m = _TEXT.match(value)
        if not m:
            raise DimensionError(f"{value!r} is not '<number> <unit>' (a bare number, range or expression?)")
        return Quantity(float(m.group(1)), _parse_unit(m.group(2), value))
    if isinstance(value, (bool, int, float)):
        raise DimensionError(f"bare number {value!r} given where a quantity with units is required")
    raise DimensionError(f"cannot read a quantity from {type(value).__name__}")


def require(value: Any, kind: str) -> pint.Quantity:
    """Return value as a Quantity of the given kind, or raise DimensionError."""
    unit = _unit(kind)
    qty = parse(value)
    if qty.dimensionality != unit.dimensionality:
        raise DimensionError(f"expected {kind} (like {unit:~}), got {qty.units:~} with dimension {qty.dimensionality}")
    return qty


def to_internal(value: Any, kind: str) -> float:
    """Magnitude in the core's internal unit for this kind, after a dimension check."""
    return float(require(value, kind).to(_unit(kind)).magnitude)


def from_internal(value: float, kind: str) -> pint.Quantity:
    """Wrap a float that is already in internal units back into a Quantity."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DimensionError(f"expected a number in internal units, got {value!r}")
    return Quantity(float(value), _unit(kind))


def to_dict(q: pint.Quantity) -> dict[str, Any]:
    """Serialise a Quantity as {'value', 'unit'}; parse() reads it back unchanged."""
    return {"value": float(q.magnitude), "unit": str(q.units)}
