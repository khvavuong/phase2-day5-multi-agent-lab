"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
from json import dumps, loads
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client skeleton."""

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Connects to OpenAI Chat Completions API with retry and timeout.
        """

        settings = get_settings()
        if not settings.openai_api_key:
            raise AgentExecutionError("OPENAI_API_KEY is missing. Please set it in .env")

        payload = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        try:
            data = self._post_openai(
                api_key=settings.openai_api_key,
                payload=payload,
                timeout_seconds=settings.timeout_seconds,
            )
        except RetryError as exc:
            raise AgentExecutionError(f"LLM call failed after retries: {exc}") from exc

        choices = data.get("choices", [])
        content = ""
        if choices:
            content = str(choices[0].get("message", {}).get("content", "")).strip()
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens")
        output_tokens = usage.get("completion_tokens")
        return LLMResponse(
            content=content,
            input_tokens=input_tokens if isinstance(input_tokens, int) else None,
            output_tokens=output_tokens if isinstance(output_tokens, int) else None,
            cost_usd=self._estimate_cost_usd(
                model=settings.openai_model,
                input_tokens=input_tokens if isinstance(input_tokens, int) else 0,
                output_tokens=output_tokens if isinstance(output_tokens, int) else 0,
            ),
        )

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((URLError, HTTPError)),
    )
    def _post_openai(self, api_key: str, payload: dict[str, object], timeout_seconds: int) -> dict[str, object]:
        body = dumps(payload).encode("utf-8")
        request = Request(
            url="https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            parsed = loads(raw)
            if not isinstance(parsed, dict):
                raise AgentExecutionError("Unexpected OpenAI response format")
            return parsed

    def _estimate_cost_usd(self, model: str, input_tokens: int, output_tokens: int) -> float | None:
        # Lightweight estimates for benchmarking comparison only.
        pricing_per_million: dict[str, tuple[float, float]] = {
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4o": (5.00, 15.00),
            "gpt-4.1-mini": (0.40, 1.60),
            "gpt-4.1": (2.00, 8.00),
        }
        if model not in pricing_per_million:
            return None
        in_price, out_price = pricing_per_million[model]
        return (input_tokens / 1_000_000) * in_price + (output_tokens / 1_000_000) * out_price
