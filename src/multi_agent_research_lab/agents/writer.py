"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`.
        """
        with trace_span("agent.writer") as span:
            references = []
            for idx, source in enumerate(state.sources, start=1):
                ref = f"[{idx}] {source.title}"
                if source.url:
                    ref += f" - {source.url}"
                references.append(ref)
            response = self.llm_client.complete(
                system_prompt="You are a clear technical writer. Be accurate and cite sources by [index].",
                user_prompt=(
                    f"Query: {state.request.query}\nAudience: {state.request.audience}\n\n"
                    f"Research notes:\n{state.research_notes or ''}\n\n"
                    f"Analysis notes:\n{state.analysis_notes or ''}\n\n"
                    "Write a concise answer with explicit source references [1], [2], etc.\n"
                    f"Available sources:\n{chr(10).join(references)}"
                ),
            )
            state.final_answer = response.content
            span["attributes"]["input_tokens"] = response.input_tokens
            span["attributes"]["output_tokens"] = response.output_tokens
            state.add_trace_event("agent.writer", span)
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.WRITER,
                    content=response.content,
                    metadata={"cost_usd": response.cost_usd},
                )
            )
            return state
