"""PipeSpec to OPOS compiler."""

from __future__ import annotations

from typing import Any

from opos_validator.compiler.mapper import compile_impl
from opos_validator.compiler.models import CompileOptions


def compile_pipespec_to_opos(
    pipespec: dict[str, Any], *, options: CompileOptions | None = None
) -> dict[str, Any]:
    opts = options or CompileOptions()
    return compile_impl(pipespec, opts)
