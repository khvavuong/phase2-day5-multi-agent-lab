from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow


class DummySupervisor:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, state: ResearchState) -> ResearchState:
        self.calls += 1
        route = "writer" if self.calls == 1 else "done"
        state.record_route(route)
        return state


class DummyWriter:
    def run(self, state: ResearchState) -> ResearchState:
        state.final_answer = "Final answer [1]"
        state.agent_results.append(
            AgentResult(agent=AgentName.WRITER, content=state.final_answer, metadata={"cost_usd": 0.001})
        )
        return state


def test_workflow_runs_until_done() -> None:
    workflow = MultiAgentWorkflow()
    workflow.build = lambda: {  # type: ignore[method-assign]
        "supervisor": DummySupervisor(),
        "writer": DummyWriter(),
    }
    initial = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = workflow.run(initial)
    assert result.final_answer is not None
    assert result.route_history == ["writer", "done"]
