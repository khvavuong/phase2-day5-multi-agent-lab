"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`.
        """
        with trace_span("agent.analyst") as span:
            prompt = (
                "Convert research notes into structured analysis with sections:\n"
                "1) Key claims\n2) Conflicting viewpoints\n3) Weak evidence / unknowns\n"
                "Keep concise and actionable."
            )
            response = self.llm_client.complete(
                system_prompt="You are a rigorous research analyst.",
                user_prompt=f"Query: {state.request.query}\n\nResearch notes:\n{state.research_notes or ''}\n\n{prompt}",
            )
            state.analysis_notes = response.content
            span["attributes"]["input_tokens"] = response.input_tokens
            span["attributes"]["output_tokens"] = response.output_tokens
            state.add_trace_event("agent.analyst", span)
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.ANALYST,
                    content=response.content,
                    metadata={"cost_usd": response.cost_usd},
                )
            )
            return state
