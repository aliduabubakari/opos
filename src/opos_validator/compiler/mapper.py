"""Deterministic mapping from PipeSpec v1.0 to OPOS v1.0."""

from __future__ import annotations

from collections import deque
from typing import Any

from opos_validator.compiler.mapping_spec import executor_mapping, parameter_type_mapping
from opos_validator.compiler.models import CompileError, CompileOptions
from opos_validator.compiler.profile import validate_pipespec_profile

EXECUTOR_MAP = executor_mapping()
TYPE_MAP = parameter_type_mapping()


def _omits_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None and v != {}}


def _require(value: Any, code: str, message: str, path: str) -> Any:
    if value is None or value == "":
        raise CompileError(code, message, path)
    return value


def _topo_components(component_ids: set[str], edges: list[dict[str, str]]) -> list[str]:
    graph: dict[str, list[str]] = {cid: [] for cid in component_ids}
    indeg: dict[str, int] = {cid: 0 for cid in component_ids}

    for edge in edges:
        src = edge["from"]
        dst = edge["to"]
        if src in graph and dst in graph:
            graph[src].append(dst)
            indeg[dst] += 1

    ready = deque(sorted([n for n in component_ids if indeg[n] == 0]))
    out: list[str] = []

    while ready:
        node = ready.popleft()
        out.append(node)
        for nxt in sorted(graph[node]):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                ready.append(nxt)

    if len(out) != len(component_ids):
        return sorted(component_ids)

    return out


def _normalize_parameter(raw: dict[str, Any]) -> dict[str, Any]:
    raw_type = str(raw.get("type", "string")).lower()
    return _omits_none(
        {
            "type": TYPE_MAP.get(raw_type, "STRING"),
            "default": raw.get("default"),
            "description": raw.get("description"),
            "required": bool(raw.get("required", False)),
            "constraints": raw.get("constraints"),
        }
    )


def _collect_secrets(params_env: dict[str, Any]) -> list[dict[str, Any]]:
    secrets: list[dict[str, Any]] = []
    for name, spec in sorted(params_env.items()):
        entry = {
            "name": name,
            "description": spec.get("description"),
            "required_by_component": spec.get("associated_component_id"),
        }
        secrets.append(_omits_none(entry))
    return secrets


def _build_integrations(pipespec: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, connection in enumerate(pipespec.get("integrations", {}).get("connections", [])):
        connection_id = _require(
            connection.get("id"),
            "COMP007",
            "integration id is required",
            f"$.integrations.connections[{idx}].id",
        )

        auth = connection.get("authentication") or {}
        cfg = connection.get("config") or {}

        auth_method = auth.get("type", "none")
        if auth_method == "token":
            method = "token"
        elif auth_method == "connection":
            method = "basic"
        else:
            method = auth_method

        integration = {
            "id": connection_id,
            "name": connection.get("name"),
            "type": connection.get("type", "custom"),
            "protocol": cfg.get("protocol"),
            "base_url": cfg.get("base_url"),
            "base_path": cfg.get("base_path"),
            "authentication": _omits_none(
                {
                    "method": method,
                    "secret_ref": auth.get("token_env_var") or auth.get("connection_env_var"),
                }
            ),
            "used_by_components": sorted(connection.get("used_by_components") or []),
            "direction": connection.get("direction"),
            "rate_limit": connection.get("rate_limit"),
        }
        out.append(_omits_none(integration))

    return sorted(out, key=lambda x: x["id"])


def _convert_component(comp: dict[str, Any], strict: bool, comp_idx: int) -> dict[str, Any]:
    comp_id = _require(comp.get("id"), "COMP002", "component id is required", f"$.components[{comp_idx}].id")
    comp_name = _require(
        comp.get("name"), "COMP003", "component name is required", f"$.components[{comp_idx}].name"
    )
    comp_category = _require(
        comp.get("category"),
        "COMP004",
        "component category is required",
        f"$.components[{comp_idx}].category",
    )

    executor_type_raw = str(comp.get("executor_type", "custom")).lower()
    mapped = EXECUTOR_MAP.get(executor_type_raw)
    if mapped is None:
        if strict:
            raise CompileError(
                "COMP001",
                f"unsupported executor_type: {executor_type_raw}",
                f"$.components[{comp_idx}].executor_type",
            )
        mapped = "custom"

    io_specs = []
    for io_idx, io in enumerate(comp.get("io_spec", [])):
        io_name = _require(
            io.get("name"),
            "COMP005",
            "io name is required",
            f"$.components[{comp_idx}].io_spec[{io_idx}].name",
        )
        io_kind = _require(
            io.get("kind"),
            "COMP006",
            "io kind is required",
            f"$.components[{comp_idx}].io_spec[{io_idx}].kind",
        )
        io_specs.append(
            _omits_none(
                {
                    "name": io_name,
                    "direction": io.get("direction"),
                    "kind": io_kind,
                    "format": io.get("format"),
                    "path_pattern": io.get("path_pattern"),
                    "integration_id": io.get("connection_id"),
                }
            )
        )

    retry = comp.get("retry_policy") or {}
    retry_policy = _omits_none(
        {
            "max_attempts": retry.get("max_attempts", 1),
            "delay_seconds": retry.get("delay_seconds", 30),
            "strategy": "exponential" if retry.get("exponential_backoff") else "constant",
            "multiplier": retry.get("multiplier"),
            "max_delay_seconds": retry.get("max_delay_seconds"),
            "retry_on": retry.get("retry_on"),
        }
    )

    upstream = comp.get("upstream_policy") or {}

    return _omits_none(
        {
            "id": comp_id,
            "name": comp_name,
            "description": comp.get("description"),
            "category": comp_category,
            "executor": {"type": mapped},
            "inputs": [s for s in io_specs if s.get("direction") == "input"],
            "outputs": [s for s in io_specs if s.get("direction") == "output"],
            "parameters": comp.get("executor_config") or {},
            "retry": retry_policy,
            "upstream_policy": upstream.get("type", "all_success"),
            "integrations_used": sorted(
                {c.get("id") for c in comp.get("connections", []) if c.get("id") is not None}
            ),
        }
    )


def compile_impl(pipespec: dict[str, Any], options: CompileOptions) -> dict[str, Any]:
    if options.enforce_profile:
        validate_pipespec_profile(pipespec)

    if pipespec.get("pipespec_version") != "1.0":
        raise CompileError("COMP008", "unsupported pipespec_version (expected 1.0)", "$.pipespec_version")

    flow = pipespec.get("flow_structure") or {}
    components = pipespec.get("components") or []
    if not components:
        raise CompileError("COMP009", "pipespec must contain at least one component", "$.components")

    component_ids = {c.get("id") for c in components if c.get("id")}
    edges = [
        _omits_none(
            {
                "from": e.get("from"),
                "to": e.get("to"),
                "condition": e.get("condition"),
                "edge_type": e.get("edge_type", "success"),
            }
        )
        for e in flow.get("edges", [])
    ]

    ordered_ids = _topo_components(component_ids, edges)
    by_id = {c["id"]: c for c in components if c.get("id")}
    index_by_id = {c.get("id"): idx for idx, c in enumerate(components)}

    component_out = [
        _convert_component(by_id[cid], options.strict, index_by_id[cid])
        for cid in ordered_ids
        if cid in by_id
    ]

    p_summary = pipespec.get("pipeline_summary") or {}
    p_meta = pipespec.get("metadata") or {}
    params = pipespec.get("parameters") or {}

    pipeline_name = _require(
        p_summary.get("name"),
        "COMP010",
        "pipeline_summary.name is required",
        "$.pipeline_summary.name",
    )
    pipeline_description = _require(
        p_summary.get("description"),
        "COMP011",
        "pipeline_summary.description is required",
        "$.pipeline_summary.description",
    )

    pipeline_params: dict[str, Any] = {}
    for section_name in ("pipeline", "components"):
        section = params.get(section_name) or {}
        for key, val in section.items():
            if isinstance(val, dict) and "type" in val:
                pipeline_params[key] = _normalize_parameter(val)
            elif isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    pipeline_params[f"{key}.{sub_key}"] = _normalize_parameter(sub_val)

    integrations = _build_integrations(pipespec)

    out = {
        "opos_version": "1.0",
        "pipeline_id": str(pipeline_name).lower().replace(" ", "_"),
        "description": pipeline_description,
        "metadata": _omits_none(
            {
                "name": pipeline_name,
                "owner": "unknown",
                "domain": "general",
                "complexity": p_summary.get("complexity", "medium"),
                "generator": "llm" if p_meta.get("llm_model") else "template",
                "llm_model": p_meta.get("llm_model"),
                "created": (p_meta.get("analysis_timestamp") or "")[:10] or None,
            }
        ),
        "schedule": _omits_none(
            {
                "enabled": bool(((params.get("schedule") or {}).get("enabled") or {}).get("default", False)),
            }
        ),
        "parameters": pipeline_params,
        "secrets": _collect_secrets(params.get("environment") or {}),
        "integrations": integrations,
        "components": component_out,
        "flow": {
            "pattern": flow.get("pattern", "dag"),
            "entry_points": sorted(flow.get("entry_points", [])),
            "edges": sorted(edges, key=lambda e: (e.get("from", ""), e.get("to", ""))),
        },
        "provenance": _omits_none(
            {
                "source_file": p_meta.get("source_file"),
                "source_type": "step1_json",
                "generated_at": p_meta.get("analysis_timestamp"),
                "generator_id": p_meta.get("llm_provider"),
                "generator_version": p_meta.get("llm_model"),
            }
        ),
    }

    for key in list(out.keys()):
        val = out[key]
        if val in ({}, [], None):
            del out[key]

    return out
