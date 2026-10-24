"""Shared data models for the engineering core (Development Plan v2 M0; ADR-001, ADR-005).

Quantities are pint Quantities typed by kind (Length, Force, Stress...): a field rejects bare numbers and wrong
dimensions, and serialises as {"value", "unit"}. Plan coordinates are the one exception: Point2D holds floats in the
model's declared length_unit (always mm), to keep large polylines light.

Every value that enters a calculation can say where it came from (ValueSource). A CheckResult cannot be PASS or FAIL
without a value, a limit, a utilisation, a method reference and a registry version, and NOT EVALUATED / BLOCKED must
say what is missing. Nothing here records approval: approval is a human record kept outside these models.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from enum import Enum
from typing import Annotated, Literal, Optional

import pint
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    WithJsonSchema,
    field_validator,
    model_validator,
)

from calc_lib.core import units
from calc_lib.core.status import CheckStatus

SCHEMA_VERSION = "0.1.0"

_QTY_JSON = {"type": "object", "properties": {"value": {"type": "number"}, "unit": {"type": "string"}},
             "required": ["value", "unit"]}


_SERIALISE = PlainSerializer(units.to_dict, return_type=dict)


def _kind(kind: str) -> BeforeValidator:
    return BeforeValidator(lambda v: units.require(v, kind))


def _schema(kind: str) -> WithJsonSchema:
    return WithJsonSchema({**_QTY_JSON, "description": f"quantity ({kind})"})


# Spelled out one by one so type checkers see real aliases.
AnyQty = Annotated[pint.Quantity, BeforeValidator(units.parse), _SERIALISE, _schema("any dimension")]
Dimensionless = Annotated[pint.Quantity, _kind("dimensionless"), _SERIALISE, _schema("dimensionless")]
Length = Annotated[pint.Quantity, _kind("length"), _SERIALISE, _schema("length")]
Area = Annotated[pint.Quantity, _kind("area"), _SERIALISE, _schema("area")]
Force = Annotated[pint.Quantity, _kind("force"), _SERIALISE, _schema("force")]
ForcePerLength = Annotated[pint.Quantity, _kind("force_per_length"), _SERIALISE, _schema("force_per_length")]
Stress = Annotated[pint.Quantity, _kind("pressure"), _SERIALISE, _schema("pressure")]
Moment = Annotated[pint.Quantity, _kind("moment"), _SERIALISE, _schema("moment")]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)


def content_hash(model: BaseModel) -> str:
    """SHA-256 of the model's canonical JSON. Used for immutable input snapshots."""
    payload = json.dumps(model.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------------------------- provenance
class ValueSource(str, Enum):
    DESIGN_BASIS = "design_basis"
    PT_BASIS = "pt_basis"
    REGISTRY = "registry"
    MANUFACTURER = "manufacturer"
    EXTRACTED_FROM_CAD = "extracted_from_cad"
    ENGINEER_ENTERED = "engineer_entered"
    ANALYSIS_IMPORT = "analysis_import"
    CALCULATED = "calculated"
    ASSUMED = "assumed"


class SourcedValue(_Model):
    value: AnyQty
    source: ValueSource
    ref: Optional[str] = None       # e.g. registry param id, design-basis path, file name, calculation id


class FileRecord(_Model):
    name: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


# --------------------------------------------------------------------------------------------- geometry
class Point2D(_Model):
    x: float
    y: float

    @field_validator("x", "y")
    @classmethod
    def _finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("coordinate must be finite")
        return v


def _polyline(pts: list[Point2D], minimum: int, what: str) -> list[Point2D]:
    if len(pts) < minimum:
        raise ValueError(f"{what} needs at least {minimum} points")
    if len({(p.x, p.y) for p in pts}) < minimum:
        raise ValueError(f"{what} has fewer than {minimum} distinct points")
    return pts


class _Element(_Model):
    id: str = Field(min_length=1)
    source: Literal[ValueSource.EXTRACTED_FROM_CAD, ValueSource.ENGINEER_ENTERED]
    cad_handle: Optional[str] = None    # DXF entity handle, for traceability back to the drawing


class Grid(_Model):
    label: str
    axis: Literal["X", "Y"]             # X: line of constant x
    offset: float


class Column(_Element):
    centre: Point2D
    shape: Literal["rectangular", "circular"]
    b: Optional[Length] = None
    h: Optional[Length] = None
    diameter: Optional[Length] = None
    rotation_deg: float = 0.0

    @model_validator(mode="after")
    def _dims(self) -> Column:
        if self.shape == "rectangular" and (self.b is None or self.h is None or self.diameter is not None):
            raise ValueError(f"column {self.id}: rectangular needs b and h only")
        if self.shape == "circular" and (self.diameter is None or self.b is not None or self.h is not None):
            raise ValueError(f"column {self.id}: circular needs diameter only")
        return self


class Wall(_Element):
    path: list[Point2D]
    thickness: Length

    @field_validator("path")
    @classmethod
    def _path(cls, v: list[Point2D]) -> list[Point2D]:
        return _polyline(v, 2, "wall path")


class SlabRegion(_Element):
    outline: list[Point2D]
    thickness: Length

    @field_validator("outline")
    @classmethod
    def _outline(cls, v: list[Point2D]) -> list[Point2D]:
        return _polyline(v, 3, "slab outline")


class BandBeam(_Element):
    centreline: list[Point2D]
    width: Length
    depth: Length                       # overall depth including slab

    @field_validator("centreline")
    @classmethod
    def _cl(cls, v: list[Point2D]) -> list[Point2D]:
        return _polyline(v, 2, "band beam centreline")


class Opening(_Element):
    outline: list[Point2D]

    @field_validator("outline")
    @classmethod
    def _outline(cls, v: list[Point2D]) -> list[Point2D]:
        return _polyline(v, 3, "opening outline")


class DropPanel(_Element):
    outline: list[Point2D]
    depth: Length                       # overall depth including slab

    @field_validator("outline")
    @classmethod
    def _outline(cls, v: list[Point2D]) -> list[Point2D]:
        return _polyline(v, 3, "drop panel outline")


class GeometryReview(_Model):
    state: Literal["UNREVIEWED", "CONFIRMED"] = "UNREVIEWED"
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[dt.datetime] = None

    @model_validator(mode="after")
    def _who(self) -> GeometryReview:
        if self.state == "CONFIRMED" and not (self.reviewed_by and self.reviewed_at):
            raise ValueError("CONFIRMED geometry needs reviewed_by and reviewed_at")
        return self


class GeometryModel(_Model):
    schema_version: str = SCHEMA_VERSION
    project_code: str
    floor_label: str
    length_unit: Literal["mm"] = "mm"   # unit of every Point2D in this model
    source_file: Optional[FileRecord] = None
    grids: list[Grid] = Field(default_factory=list)
    columns: list[Column] = Field(default_factory=list)
    walls: list[Wall] = Field(default_factory=list)
    slabs: list[SlabRegion] = Field(default_factory=list)
    band_beams: list[BandBeam] = Field(default_factory=list)
    openings: list[Opening] = Field(default_factory=list)
    drop_panels: list[DropPanel] = Field(default_factory=list)
    review: GeometryReview = Field(default_factory=GeometryReview)

    @model_validator(mode="after")
    def _unique(self) -> GeometryModel:
        ids = [e.id for group in (self.columns, self.walls, self.slabs, self.band_beams, self.openings,
                                  self.drop_panels) for e in group]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            raise ValueError(f"duplicate element ids: {dup}")
        labels = [g.label for g in self.grids]
        dup = sorted({g for g in labels if labels.count(g) > 1})
        if dup:
            raise ValueError(f"duplicate grid labels: {dup}")
        return self


# --------------------------------------------------------------------------------------------- analysis results
class AnalysisSource(_Model):
    adapter: str                        # e.g. "safe_etabs_tables"
    adapter_version: str
    software: Optional[str] = None      # e.g. "SAFE"
    software_version: Optional[str] = None
    model_file: Optional[str] = None
    files: list[FileRecord] = Field(min_length=1)
    run_date: Optional[dt.date] = None


class LoadCase(_Model):
    name: str
    kind: Literal["self_weight", "superimposed_dead", "imposed", "prestress", "construction", "other"]
    description: Optional[str] = None


class Combination(_Model):
    name: str
    limit_state: Literal["ULS", "SLS_CHARACTERISTIC", "SLS_FREQUENT", "SLS_QUASI_PERMANENT", "TRANSFER", "OTHER"]
    factors: dict[str, float] = Field(min_length=1)     # load case name -> factor


class Reaction(_Model):
    support_id: str
    case: str                           # load case or combination name
    fx: Force
    fy: Force
    fz: Force
    mx: Moment
    my: Moment
    mz: Moment


class StripForce(_Model):
    strip_id: str
    station: Length
    case: str                           # load case or combination name
    moment: Moment                      # total over the strip width
    shear: Force
    axial: Optional[Force] = None


class EquilibriumCheck(_Model):
    case: str
    applied_fz: Force
    reaction_fz: Force
    tolerance_ratio: float = Field(gt=0)
    status: CheckStatus


class AnalysisResults(_Model):
    schema_version: str = SCHEMA_VERSION
    source: AnalysisSource
    geometry_sha256: Optional[str] = None
    load_cases: list[LoadCase] = Field(min_length=1)
    combinations: list[Combination] = Field(default_factory=list)
    reactions: list[Reaction] = Field(default_factory=list)
    strip_forces: list[StripForce] = Field(default_factory=list)
    equilibrium: list[EquilibriumCheck] = Field(default_factory=list)

    @model_validator(mode="after")
    def _refs(self) -> AnalysisResults:
        cases = [c.name for c in self.load_cases]
        combos = [c.name for c in self.combinations]
        names = cases + combos
        dup = sorted({n for n in names if names.count(n) > 1})
        if dup:
            raise ValueError(f"load case / combination names repeated: {dup}")
        for c in self.combinations:
            unknown = sorted(set(c.factors) - set(cases))
            if unknown:
                raise ValueError(f"combination {c.name} uses unknown load cases {unknown}")
        known = set(names)
        used = [r.case for r in self.reactions] + [f.case for f in self.strip_forces] + \
            [e.case for e in self.equilibrium]
        for case in used:
            if case not in known:
                raise ValueError(f"result refers to unknown case {case!r}")
        return self


# --------------------------------------------------------------------------------------------- tendons and losses
class ProfilePoint(_Model):
    chainage: Length                    # along the tendon from the start anchor
    height: Length                      # tendon centroid above the local soffit
    kind: Literal["anchor", "high", "low", "inflection", "station"]


class Tendon(_Model):
    mark: str = Field(min_length=1)
    group: Optional[str] = None
    strand_count: int = Field(gt=0)
    strand_ref: str                     # strand entry in the PT basis
    duct_width: Length
    duct_height: Length
    stressing: Literal["start", "end", "both"]
    plan_path: list[Point2D]
    profile: list[ProfilePoint]
    jacking_force_per_strand: Optional[Force] = None   # None: take from the PT basis

    @field_validator("plan_path")
    @classmethod
    def _plan(cls, v: list[Point2D]) -> list[Point2D]:
        return _polyline(v, 2, "tendon plan path")

    @model_validator(mode="after")
    def _profile(self) -> Tendon:
        if len(self.profile) < 2:
            raise ValueError(f"tendon {self.mark}: profile needs at least 2 points")
        ch = [units.to_internal(p.chainage, "length") for p in self.profile]
        if any(b <= a for a, b in zip(ch, ch[1:])):
            raise ValueError(f"tendon {self.mark}: profile chainages must increase")
        if ch[0] != 0.0:
            raise ValueError(f"tendon {self.mark}: profile must start at chainage 0")
        if self.profile[0].kind != "anchor" or self.profile[-1].kind != "anchor":
            raise ValueError(f"tendon {self.mark}: profile must start and end at an anchor")
        return self


class LossStation(_Model):
    chainage: Length
    after_friction: Optional[Force] = None
    after_draw_in: Optional[Force] = None
    after_elastic: Optional[Force] = None
    long_term: Optional[Force] = None


class LossResult(_Model):
    tendon_mark: str
    status: Literal["EVALUATED", "NOT EVALUATED"]
    stations: list[LossStation] = Field(default_factory=list)
    inputs: dict[str, SourcedValue] = Field(default_factory=dict)
    method_refs: list[str] = Field(default_factory=list)
    registry_version: Optional[str] = None
    missing: list[str] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _status(self) -> LossResult:
        if self.status == "EVALUATED" and not (self.stations and self.method_refs and self.registry_version):
            raise ValueError("EVALUATED losses need stations, method_refs and registry_version")
        if self.status == "NOT EVALUATED" and not self.missing:
            raise ValueError("NOT EVALUATED losses must list what is missing")
        return self


# --------------------------------------------------------------------------------------------- checks
class CheckResult(_Model):
    id: str
    check_type: str                     # e.g. "punching_shear", "sls_stress_transfer"
    element_id: str
    location: Optional[str] = None
    limit_state: Literal["ULS", "SLS", "TRANSFER", "DETAILING", "OTHER"]
    combination: Optional[str] = None
    status: CheckStatus
    value: Optional[AnyQty] = None      # governing design action / calculated value
    limit: Optional[AnyQty] = None      # resistance / limit
    utilisation: Optional[float] = None
    governing: Optional[str] = None
    method_ref: Optional[str] = None
    registry_version: Optional[str] = None
    inputs: dict[str, SourcedValue] = Field(default_factory=dict)
    trace: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _rules(self) -> CheckResult:
        s = self.status
        if self.utilisation is not None and (not math.isfinite(self.utilisation) or self.utilisation < 0):
            raise ValueError("utilisation must be a finite number >= 0")
        if self.value is not None and self.limit is not None and \
                self.value.dimensionality != self.limit.dimensionality:
            raise ValueError(f"value ({self.value.units}) and limit ({self.limit.units}) have different dimensions")
        if s in (CheckStatus.PASS, CheckStatus.FAIL):
            need = [f for f in ("value", "limit", "utilisation", "method_ref", "registry_version")
                    if getattr(self, f) is None]
            if need:
                raise ValueError(f"{s.value} needs {need}")
            if self.missing:
                raise ValueError(f"{s.value} cannot have missing inputs {self.missing}")
            assert self.utilisation is not None
            if s is CheckStatus.PASS and self.utilisation > 1.0:
                raise ValueError("PASS with utilisation > 1.0")
            if s is CheckStatus.FAIL and self.utilisation <= 1.0:
                raise ValueError("FAIL with utilisation <= 1.0; record the reason as a message and use another status")
        if s in (CheckStatus.NOT_EVALUATED, CheckStatus.BLOCKED) and not (self.missing or self.messages):
            raise ValueError(f"{s.value} must say what is missing or why")
        if s in (CheckStatus.WARNING, CheckStatus.ENGINEER_REVIEW_REQUIRED) and not self.messages:
            raise ValueError(f"{s.value} needs a message")
        return self


# --------------------------------------------------------------------------------------------- reinforcement
class ReinforcementGroup(_Model):
    """Fields from v1 Part 11. Schedules and drawings read the same object."""
    mark: str = Field(min_length=1)
    element_id: str
    design_revision: str
    bar_diameter: Length
    grade: str
    quantity: Optional[int] = Field(default=None, gt=0)
    spacing: Optional[Length] = None
    orientation: Literal["X", "Y", "along_element", "across_element", "other"]
    layer: Literal["T1", "T2", "B1", "B2", "LINKS", "OTHER"]
    shape_code: str
    bar_length: Length
    bending: dict[str, Length] = Field(default_factory=dict)   # shape dimensions by schedule letter
    placement: list[Point2D] = Field(default_factory=list)     # placement region or start/end
    cover: Length
    calc_ref: Optional[str] = None
    drawing_ref: Optional[str] = None

    @model_validator(mode="after")
    def _count(self) -> ReinforcementGroup:
        if self.quantity is None and self.spacing is None:
            raise ValueError(f"bar group {self.mark}: give quantity or spacing")
        return self
