"""Optional critic agent skeleton for bonus work."""

import re

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings.
        """
        answer = state.final_answer or ""
        source_count = len(state.sources)
        refs = re.findall(r"\[(\d+)\]", answer)
        valid_refs = 0
        for raw in refs:
            idx = int(raw)
            if 1 <= idx <= source_count:
                valid_refs += 1
        coverage = 0.0 if source_count == 0 else min(1.0, valid_refs / source_count)
        warning_lines: list[str] = []
        if source_count == 0:
            warning_lines.append("No sources were collected.")
        if coverage < 0.5:
            warning_lines.append("Low citation coverage. Add more explicit source references.")
        if len(answer.split()) < 120:
            warning_lines.append("Answer may be too short for deep analysis.")
        critic_note = f"Citation coverage: {coverage:.2f}. " + (
            " ".join(warning_lines) if warning_lines else "No major issues detected."
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=critic_note,
                metadata={"citation_coverage": coverage, "warnings": warning_lines},
            )
        )
        state.add_trace_event("agent.critic", {"coverage": coverage, "warnings": warning_lines})
        return state
