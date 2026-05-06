"""Benchmark skeleton for single-agent vs multi-agent."""

import re
from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str,
    query: str,
    runner: Runner,
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and return benchmark metrics."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    estimated_cost = 0.0
    for result in state.agent_results:
        cost = result.metadata.get("cost_usd")
        if isinstance(cost, (int, float)):
            estimated_cost += float(cost)
    refs = re.findall(r"\[(\d+)\]", state.final_answer or "")
    valid_refs = 0
    for raw in refs:
        idx = int(raw)
        if 1 <= idx <= len(state.sources):
            valid_refs += 1
    coverage = None if len(state.sources) == 0 else min(1.0, valid_refs / len(state.sources))
    has_failure = 1.0 if state.errors else 0.0
    quality = _estimate_quality_score(state)
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=estimated_cost,
        quality_score=quality,
        citation_coverage=coverage,
        failure_rate=has_failure,
        notes=f"errors={len(state.errors)}, routes={state.route_history}",
    )
    return state, metrics


def _estimate_quality_score(state: ResearchState) -> float:
    answer = state.final_answer or ""
    if not answer.strip():
        return 0.0
    length_score = min(4.0, len(answer.split()) / 60)
    analysis_bonus = 2.0 if state.analysis_notes else 0.0
    source_bonus = min(2.0, len(state.sources) * 0.4)
    error_penalty = min(3.0, float(len(state.errors)))
    raw = length_score + analysis_bonus + source_bonus + 2.0 - error_penalty
    return max(0.0, min(10.0, raw))
