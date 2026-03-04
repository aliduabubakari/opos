"""Semantic validation rules for OPOS v1.0."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from opos_validator.validation.models import ValidationIssue


def _component_ids(doc: dict[str, Any]) -> list[str]:
    return [c.get("id") for c in doc.get("components", []) if c.get("id")]


def _integration_ids(doc: dict[str, Any]) -> list[str]:
    return [i.get("id") for i in doc.get("integrations", []) if i.get("id")]


def validate_semantics(doc: dict[str, Any]) -> tuple[list[ValidationIssue], list[ValidationIssue]]:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    components = _component_ids(doc)
    component_set = set(components)
    integrations = _integration_ids(doc)
    integration_set = set(integrations)

    entry_points = doc.get("flow", {}).get("entry_points", [])
    for ep in entry_points:
        if ep not in component_set:
            errors.append(ValidationIssue("SEM001", f"entry point '{ep}' not found", "$.flow.entry_points"))

    edges = doc.get("flow", {}).get("edges", [])
    for idx, edge in enumerate(edges):
        if edge.get("from") not in component_set or edge.get("to") not in component_set:
            errors.append(
                ValidationIssue("SEM002", "edge references unknown component", f"$.flow.edges[{idx}]")
            )

    pattern = doc.get("flow", {}).get("pattern")
    if pattern in {"sequential", "parallel", "dag"}:
        graph: dict[str, list[str]] = {cid: [] for cid in components}
        indeg: dict[str, int] = {cid: 0 for cid in components}
        for edge in edges:
            src = edge.get("from")
            dst = edge.get("to")
            if src in graph and dst in indeg:
                graph[src].append(dst)
                indeg[dst] += 1

        q = deque([n for n in components if indeg[n] == 0])
        seen = 0
        while q:
            n = q.popleft()
            seen += 1
            for nxt in graph[n]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    q.append(nxt)
        if seen != len(components):
            errors.append(ValidationIssue("SEM003", "flow contains cycle", "$.flow.edges"))

    for idx, comp in enumerate(doc.get("components", [])):
        for integration in comp.get("integrations_used", []):
            if integration not in integration_set:
                errors.append(
                    ValidationIssue(
                        "SEM004",
                        f"component integration '{integration}' not declared",
                        f"$.components[{idx}].integrations_used",
                    )
                )
        for io_idx, io in enumerate((comp.get("inputs") or []) + (comp.get("outputs") or [])):
            integration_id = io.get("integration_id")
            if integration_id and integration_id not in integration_set:
                errors.append(
                    ValidationIssue(
                        "SEM005",
                        f"io integration '{integration_id}' not declared",
                        f"$.components[{idx}].io[{io_idx}]",
                    )
                )

    secret_set = {s.get("name") for s in doc.get("secrets", []) if s.get("name")}
    for idx, integ in enumerate(doc.get("integrations", [])):
        auth = integ.get("authentication") or {}
        for secret_key in ("secret_ref", "username_secret", "password_secret"):
            secret_name = auth.get(secret_key)
            if secret_name and secret_name not in secret_set:
                errors.append(
                    ValidationIssue(
                        "SEM006",
                        f"integration secret '{secret_name}' not declared",
                        f"$.integrations[{idx}].authentication.{secret_key}",
                    )
                )

    if len(component_set) != len(components):
        errors.append(ValidationIssue("SEM007", "duplicate component ids", "$.components"))
    if len(integration_set) != len(integrations):
        errors.append(ValidationIssue("SEM007", "duplicate integration ids", "$.integrations"))

    if pattern == "sequential":
        fanout: dict[str, int] = defaultdict(int)
        for edge in edges:
            fanout[edge.get("from", "")] += 1
        offenders = [node for node, count in fanout.items() if count > 1]
        if offenders:
            errors.append(
                ValidationIssue(
                    "SEM008",
                    f"sequential flow has branching nodes: {', '.join(sorted(offenders))}",
                    "$.flow.edges",
                )
            )

    schedule = doc.get("schedule") or {}
    if schedule.get("enabled") and not schedule.get("cron"):
        errors.append(ValidationIssue("SEM009", "schedule enabled requires cron", "$.schedule"))

    allowed = {
        "Extractor": {"python_script", "http_request", "container", "custom"},
        "Transformer": {"python_script", "sql", "bash", "container", "custom"},
        "Loader": {"python_script", "sql", "container", "custom"},
        "QualityCheck": {"python_script", "sql", "bash", "custom"},
        "Notifier": {"email", "http_request", "custom"},
        "Sensor": {"http_request", "python_script", "custom"},
        "Reconciliator": {"python_script", "sql", "custom"},
        "Custom": {"custom", "python_script", "container", "bash", "sql", "http_request", "email"}
    }
    for idx, comp in enumerate(doc.get("components", [])):
        category = comp.get("category")
        executor = (comp.get("executor") or {}).get("type")
        if category in allowed and executor and executor not in allowed[category]:
            warnings.append(
                ValidationIssue(
                    "SEM010",
                    f"category '{category}' usually incompatible with executor '{executor}'",
                    f"$.components[{idx}]",
                )
            )

    return errors, warnings
