"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline with a real LLM call."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    llm = LLMClient()
    response = llm.complete(
        system_prompt=(
            "You are a research assistant. "
            "Answer clearly and cite uncertainty when needed."
        ),
        user_prompt=f"Research and answer this query:\n{query}",
    )
    state.final_answer = response.content
    state.add_trace_event(
        "baseline.run",
        {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": response.cost_usd,
        },
    )
    console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    try:
        result = workflow.run(state)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    query: Annotated[
        list[str] | None,
        typer.Option("--query", "-q", help="Benchmark query. Can be passed multiple times."),
    ] = None,
    output: Annotated[
        str,
        typer.Option("--output", "-o", help="Output markdown report path."),
    ] = "reports/benchmark_report.md",
) -> None:
    """Run baseline and multi-agent benchmarks, then write markdown report."""

    _init()
    queries = query or [
        "Research GraphRAG state-of-the-art and write a 300-word summary",
        "Compare RAG and long-context models for enterprise QA",
        "List top failure modes of tool-using AI agents and mitigations",
    ]
    llm = LLMClient()
    workflow = MultiAgentWorkflow()

    def _baseline_runner(user_query: str) -> ResearchState:
        state = ResearchState(request=ResearchQuery(query=user_query))
        response = llm.complete(
            system_prompt=(
                "You are a research assistant. "
                "Answer clearly and cite uncertainty when needed."
            ),
            user_prompt=f"Research and answer this query:\n{user_query}",
        )
        state.final_answer = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={"cost_usd": response.cost_usd},
            )
        )
        return state

    def _multi_runner(user_query: str) -> ResearchState:
        state = ResearchState(request=ResearchQuery(query=user_query))
        return workflow.run(state)

    all_metrics = []
    for idx, item in enumerate(queries, start=1):
        _, base_metrics = run_benchmark(
            run_name=f"baseline_q{idx}",
            query=item,
            runner=_baseline_runner,
        )
        _, multi_metrics = run_benchmark(
            run_name=f"multi_agent_q{idx}",
            query=item,
            runner=_multi_runner,
        )
        all_metrics.extend([base_metrics, multi_metrics])

    report = render_markdown_report(all_metrics)
    with open(output, "w", encoding="utf-8") as handle:
        handle.write(report)

    console.print(Panel.fit(f"Benchmark report saved to {output}", title="Benchmark Done"))
    console.print(report)


if __name__ == "__main__":
    app()
