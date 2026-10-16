"""Shared foundations for the engineering core (Development Plan v2, M0).

- units      : pint registry, internal units, dimension checks (ADR-007)
- status     : check status categories and how they combine (v1 Part 16)
- registry   : versioned design-code registry (ADR-004)
- schemas    : shared data models - geometry, analysis results, tendons, losses, checks, reinforcement (ADR-001)

Nothing in this package contains engineering values. Values come from the project design basis, the PT basis,
approved PT system data or the code registry.
"""
