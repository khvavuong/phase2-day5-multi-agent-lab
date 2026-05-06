"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self, search_client: SearchClient | None = None) -> None:
        self.search_client = search_client or SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`.
        """
        with trace_span("agent.researcher", {"query": state.request.query, "max_sources": state.request.max_sources}) as span:
            docs = self.search_client.search(state.request.query, max_results=state.request.max_sources)
            state.sources = docs
            note_lines = []
            for idx, doc in enumerate(docs, start=1):
                source_line = f"[{idx}] {doc.title}"
                if doc.url:
                    source_line += f" ({doc.url})"
                source_line += f": {doc.snippet}"
                note_lines.append(source_line)
            state.research_notes = "\n".join(note_lines) if note_lines else "No reliable sources found."
            span["attributes"]["source_count"] = len(docs)
            state.add_trace_event("agent.researcher", span)
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.RESEARCHER,
                    content=state.research_notes,
                    metadata={"source_count": len(docs)},
                )
            )
            return state
