"""Versioned design-code registry (ADR-004).

Files: 04_tools/code_registry/*.yaml, one per (standard, edition, national annex). A CEN_RECOMMENDED file holds the
full parameter list; an NA file overrides it for one country. Format: 04_tools/code_registry/README.md.

Rules enforced here:
- `require()` returns a value only if it is present and VERIFIED; otherwise it raises NotEvaluated naming the parameter.
- Under a National Annex, a parameter marked `ndp: true` must come from the NA file; it never falls back to CEN.
- The project's selection comes from its design basis (standards[].edition, national_annex.mode/country). An unresolved
  NA or a missing edition raises NotEvaluated instead of guessing.
- Every view has a version string (file versions + content hash) for calculation records.
No clause text is stored, only references.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
from enum import Enum
from typing import Any, Literal, Mapping, Optional

import pint
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from calc_lib.core import units
from calc_lib.core.status import NotEvaluated

CEN = "CEN_RECOMMENDED"
NA = "NA"


class EntryStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"


class RegistryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str
    kind: str
    unit: str
    value: Optional[float] = None
    ndp: bool = False                       # nationally determined parameter
    source_ref: Optional[str] = None        # clause / table / equation number only
    status: EntryStatus = EntryStatus.UNVERIFIED
    verified_by: Optional[str] = None
    verified_date: Optional[dt.date] = None
    note: Optional[str] = None

    @model_validator(mode="after")
    def _consistent(self) -> RegistryEntry:
        units.require(units.Quantity(1.0, self.unit), self.kind)  # unit must match kind
        if self.status is EntryStatus.VERIFIED:
            missing = [f for f in ("value", "source_ref", "verified_by", "verified_date") if getattr(self, f) is None]
            if missing:
                raise ValueError(f"VERIFIED entry is missing {missing}")
        return self


class RegistryFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    file_version: int = Field(ge=1)
    standard: str
    edition: str
    national_annex: Literal["CEN_RECOMMENDED", "NA"]
    country: Optional[str] = None
    na_reference: Optional[str] = None
    effective_date: Optional[dt.date] = None
    parameters: dict[str, RegistryEntry] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _na_fields(self) -> RegistryFile:
        if self.national_annex == NA and not (self.country and self.na_reference):
            raise ValueError("an NA file needs country and na_reference")
        if self.national_annex == CEN and (self.country or self.na_reference):
            raise ValueError("a CEN_RECOMMENDED file must not set country or na_reference")
        return self

    @property
    def key(self) -> tuple[str, str, str, Optional[str]]:
        return (self.standard, self.edition, self.national_annex, self.country)


class RegistryError(ValueError):
    """The registry files themselves are invalid (bad format, duplicates, orphan NA file)."""


def _digest(files: list[tuple[str, RegistryFile]]) -> str:
    payload = json.dumps([[name, f.model_dump(mode="json")] for name, f in files], sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class RegistryView:
    """The registry as it applies to one standard edition under one NA choice."""

    def __init__(self, base: tuple[str, RegistryFile], overlay: Optional[tuple[str, RegistryFile]] = None) -> None:
        self.base: RegistryFile = base[1]
        self.overlay: Optional[RegistryFile] = overlay[1] if overlay else None
        used = [base] + ([overlay] if overlay else [])
        label = f"{self.base.standard}:{self.base.edition}"
        if self.overlay:
            label += f" NA[{self.overlay.country}] v{self.base.file_version}+v{self.overlay.file_version}"
        else:
            label += f" CEN v{self.base.file_version}"
        self.version = f"{label} sha256:{_digest(used)[:12]}"

    def entry(self, param_id: str) -> RegistryEntry:
        """The entry that applies, whatever its status. Raises NotEvaluated if there is none."""
        base = self.base.parameters.get(param_id)
        if self.overlay is not None:
            if param_id in self.overlay.parameters:
                return self.overlay.parameters[param_id]
            if base is not None and base.ndp:
                raise NotEvaluated(f"{param_id} is nationally determined and not set in the "
                                   f"{self.overlay.country} NA file", [param_id])
        if base is None:
            raise NotEvaluated(f"{param_id} is not in the registry for {self.base.standard}:{self.base.edition}",
                               [param_id])
        return base

    def require(self, param_id: str) -> pint.Quantity:
        """The value as a Quantity, only if present and VERIFIED. Otherwise NotEvaluated."""
        e = self.entry(param_id)
        if e.value is None:
            raise NotEvaluated(f"{param_id} has no value in the registry", [param_id])
        if e.status is not EntryStatus.VERIFIED:
            raise NotEvaluated(f"{param_id} is {e.status.value}; an engineer must verify it before use", [param_id])
        return units.Quantity(e.value, e.unit)

    def source_ref(self, param_id: str) -> str:
        """'<standard>:<edition> <ref>' for calculation traces."""
        e = self.entry(param_id)
        std = self.overlay.na_reference if (self.overlay and param_id in self.overlay.parameters) else \
            f"{self.base.standard}:{self.base.edition}"
        return f"{std} {e.source_ref or '(reference not recorded)'}"


class CodeRegistry:
    def __init__(self, files: Mapping[str, RegistryFile]) -> None:
        self.files = dict(files)
        by_key: dict[tuple[str, str, str, Optional[str]], str] = {}
        for name, f in self.files.items():
            if f.key in by_key:
                raise RegistryError(f"{name} and {by_key[f.key]} both define {f.key}")
            by_key[f.key] = name
        self._by_key = by_key
        for name, f in self.files.items():
            if f.national_annex == NA:
                if (f.standard, f.edition, CEN, None) not in by_key:
                    raise RegistryError(f"{name}: NA file has no CEN_RECOMMENDED base for {f.standard}:{f.edition}")
                base = self.files[by_key[(f.standard, f.edition, CEN, None)]]
                unknown = sorted(set(f.parameters) - set(base.parameters))
                if unknown:
                    raise RegistryError(f"{name}: parameters not in the CEN base file: {unknown}")

    @classmethod
    def load(cls, directory: pathlib.Path | str) -> CodeRegistry:
        directory = pathlib.Path(directory)
        files: dict[str, RegistryFile] = {}
        for p in sorted(directory.glob("*.yaml")):
            raw: Any = yaml.safe_load(p.read_text(encoding="utf-8"))
            try:
                files[p.name] = RegistryFile.model_validate(raw)
            except Exception as exc:  # pydantic.ValidationError or unit errors
                raise RegistryError(f"{p.name}: {exc}") from exc
        return cls(files)

    def select(self, standard: str, edition: Optional[str], na_mode: Optional[str],
               country: Optional[str] = None) -> RegistryView:
        if not edition:
            raise NotEvaluated(f"{standard}: edition not recorded in the design basis", [f"{standard}.edition"])
        base_key = (standard, str(edition), CEN, None)
        if base_key not in self._by_key:
            raise NotEvaluated(f"no registry file for {standard}:{edition}", [f"registry:{standard}:{edition}"])
        base = (self._by_key[base_key], self.files[self._by_key[base_key]])
        if na_mode == CEN:
            return RegistryView(base)
        if na_mode == NA:
            if not country:
                raise NotEvaluated("National Annex mode is NA but no country is recorded", ["national_annex.country"])
            na_key = (standard, str(edition), NA, country)
            if na_key not in self._by_key:
                raise NotEvaluated(f"no {country} NA registry file for {standard}:{edition}",
                                   [f"registry:{standard}:{edition}:NA:{country}"])
            return RegistryView(base, (self._by_key[na_key], self.files[self._by_key[na_key]]))
        raise NotEvaluated(f"National Annex choice is {na_mode or 'missing'}; it must be NA or CEN_RECOMMENDED",
                           ["national_annex.mode"])

    def select_for_project(self, design_basis: Mapping[str, Any], standard: str) -> RegistryView:
        """Select using the project design basis (standards[] and national_annex)."""
        entries = [s for s in design_basis.get("standards") or [] if s.get("id") == standard]
        if not entries:
            raise NotEvaluated(f"{standard} is not listed in the design basis standards", [f"standards:{standard}"])
        editions = {str(s.get("edition")) for s in entries if s.get("edition")}
        if len(editions) > 1:
            raise NotEvaluated(f"{standard} is listed with conflicting editions {sorted(editions)}",
                               [f"standards:{standard}.edition"])
        na = design_basis.get("national_annex") or {}
        return self.select(standard, next(iter(editions), None), na.get("mode"), na.get("country"))
