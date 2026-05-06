"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import get_settings


class _LangSmithSpan:
    def __init__(self, name: str, attributes: dict[str, Any]) -> None:
        self._run: Any | None = None
        self._enabled = False
        settings = get_settings()
        tracing_enabled = os.getenv("LANGSMITH_TRACING", "").lower() == "true"
        if not tracing_enabled or not settings.langsmith_api_key:
            return
        try:
            from langsmith import Client
            from langsmith.run_trees import RunTree

            client = Client(api_key=settings.langsmith_api_key)
            self._run = RunTree(
                name=name,
                run_type="chain",
                inputs=attributes,
                project_name=settings.langsmith_project,
                ls_client=client,
            )
            self._run.post()
            self._enabled = True
        except Exception:
            self._enabled = False

    def close(self, outputs: dict[str, Any]) -> None:
        if not self._enabled or self._run is None:
            return
        try:
            self._run.end(outputs=outputs)
            self._run.patch()
        except Exception:
            return


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal span context used by the skeleton.

    TODO(student): Replace or augment with LangSmith/Langfuse provider spans.
    """

    started = perf_counter()
    safe_attributes = attributes or {}
    span: dict[str, Any] = {
        "name": name,
        "attributes": safe_attributes,
        "duration_seconds": None,
    }
    ls_span = _LangSmithSpan(name=name, attributes=safe_attributes)
    try:
        yield span
    finally:
        span["duration_seconds"] = perf_counter() - started
        ls_span.close(outputs=span)
