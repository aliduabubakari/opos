from __future__ import annotations

import json
from pathlib import Path

import pytest

from opos_validator import CompileOptions, compile_pipespec_to_opos
from opos_validator.compiler.mapping_spec import load_mapping_spec

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict:
    return json.loads((ROOT / "spec" / "examples" / "pipespec" / name).read_text(encoding="utf-8"))


def test_profile_rejects_unknown_top_level_key() -> None:
    pipespec = _load("pm25_alert_pipeline.json")
    pipespec["unexpected"] = "x"

    with pytest.raises(ValueError) as exc:
        compile_pipespec_to_opos(pipespec, options=CompileOptions(strict=True, enforce_profile=True))

    assert "COMP012" in str(exc.value)


def test_mapping_spec_has_required_sections() -> None:
    spec = load_mapping_spec()
    assert spec["mapping_version"] == "1.0"
    assert "executor_mapping" in spec
    assert spec["executor_mapping"]["python"] == "python_script"
    assert "parameter_type_mapping" in spec
    assert spec["parameter_type_mapping"]["float"] == "FLOAT"
    assert "orchestrator_invariants" in spec
