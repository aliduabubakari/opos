"""Adapter registry."""

from __future__ import annotations

from opos_validator.adapters.interface import OposAdapter
from opos_validator.adapters.stubs import (
    AirflowAdapter,
    ArgoAdapter,
    DagsterAdapter,
    FlyteAdapter,
    KestraAdapter,
    KubeflowAdapter,
    PrefectAdapter,
)


def get_default_adapters() -> list[OposAdapter]:
    return [
        AirflowAdapter(),
        PrefectAdapter(),
        DagsterAdapter(),
        KestraAdapter(),
        ArgoAdapter(),
        KubeflowAdapter(),
        FlyteAdapter(),
    ]
