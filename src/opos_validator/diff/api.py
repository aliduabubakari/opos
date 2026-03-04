"""Semantic diff for OPOS documents."""

from __future__ import annotations

from typing import Any

from opos_validator.diff.core import semantic_diff_impl
from opos_validator.diff.models import DiffReport


def semantic_diff_opos(left: dict[str, Any], right: dict[str, Any]) -> DiffReport:
    return DiffReport(changes=semantic_diff_impl(left, right))
