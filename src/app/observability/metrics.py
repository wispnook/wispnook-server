from __future__ import annotations

from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()


def setup_metrics(app):  # type: ignore[annotations]
    instrumentator.instrument(app).expose(app, include_in_schema=False, tags=["metrics"])
