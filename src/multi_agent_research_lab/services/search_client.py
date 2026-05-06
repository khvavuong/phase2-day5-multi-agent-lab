"""Search client abstraction for ResearcherAgent."""

from json import dumps, loads
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client skeleton."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Uses Tavily API and maps results to SourceDocument.
        """
        settings = get_settings()
        if not settings.tavily_api_key:
            raise AgentExecutionError("TAVILY_API_KEY is missing. Please set it in .env")
        payload = {
            "api_key": settings.tavily_api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced",
            "include_answer": False,
            "include_raw_content": False,
        }
        try:
            data = self._post_tavily(payload=payload, timeout_seconds=settings.timeout_seconds)
        except RetryError as exc:
            raise AgentExecutionError(f"Search call failed after retries: {exc}") from exc

        results: list[SourceDocument] = []
        raw_results = data.get("results", [])
        if not isinstance(raw_results, list):
            return results
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "Untitled Source")).strip()
            url = item.get("url")
            url_value = str(url).strip() if isinstance(url, str) and url else None
            snippet = str(item.get("content", "")).strip()
            score = item.get("score")
            metadata = {"score": score} if isinstance(score, (int, float)) else {}
            if snippet:
                results.append(SourceDocument(title=title, url=url_value, snippet=snippet, metadata=metadata))
        return results

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((URLError, HTTPError)),
    )
    def _post_tavily(self, payload: dict[str, object], timeout_seconds: int) -> dict[str, object]:
        body = dumps(payload).encode("utf-8")
        request = Request(
            url="https://api.tavily.com/search",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            parsed = loads(raw)
            if not isinstance(parsed, dict):
                raise AgentExecutionError("Unexpected Tavily response format")
            return parsed
