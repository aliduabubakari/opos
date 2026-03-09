"""Adapter protocol for OPOS projection layers."""

from __future__ import annotations

from typing import Protocol

from opos_validator.adapters.models import AdapterCapability, ProjectionResult


class OposAdapter(Protocol):
    def capability(self) -> AdapterCapability:
        """Return adapter capability metadata."""

    def validate_invariants(self, opos_doc: dict) -> list[str]:
        """Validate projection invariants; return list of violations."""

    def project(self, opos_doc: dict) -> ProjectionResult:
        """Project OPOS into target-specific IR (stub in v1)."""
