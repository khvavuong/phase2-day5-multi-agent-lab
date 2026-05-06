"""LangGraph workflow skeleton."""

from time import perf_counter

from multi_agent_research_lab.agents import AnalystAgent, CriticAgent, ResearcherAgent, SupervisorAgent, WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def build(self) -> object:
        """Create a LangGraph graph.
        """
        return {
            "supervisor": SupervisorAgent(),
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "writer": WriterAgent(),
            "critic": CriticAgent(),
        }

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state.
        """
        settings = get_settings()
        nodes = self.build()
        if not isinstance(nodes, dict):
            raise AgentExecutionError("Workflow build() must return a node mapping.")

        started = perf_counter()
        while True:
            if perf_counter() - started > settings.timeout_seconds:
                state.errors.append("Workflow timeout reached.")
                state.add_trace_event("workflow.timeout", {"timeout_seconds": settings.timeout_seconds})
                break
            if state.iteration >= settings.max_iterations:
                state.add_trace_event("workflow.stop", {"reason": "max_iterations"})
                break

            state = nodes["supervisor"].run(state)
            route = state.route_history[-1]
            if route == "done":
                state.add_trace_event("workflow.stop", {"reason": "done"})
                break

            node = nodes.get(route)
            if node is None:
                state.errors.append(f"Unknown route: {route}")
                state.add_trace_event("workflow.error", {"route": route})
                break
            try:
                state = node.run(state)
            except Exception as exc:  # noqa: BLE001
                state.errors.append(f"{route} failed: {exc}")
                state.add_trace_event("workflow.agent_error", {"route": route, "error": str(exc)})
                if route == "writer":
                    break
        return state
