"""Google Gemini API 클라이언트."""
from __future__ import annotations

import json
from dataclasses import dataclass

from loguru import logger

from app.config import settings
from app.utils.retry import retry_api_call

# Gemini 비용 단가 (per 1M tokens)
_COST_TABLE = {
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.0},
}
_DEFAULT_COST = {"input": 0.15, "output": 0.60}


@dataclass
class GeminiResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    cost_usd: float


def _calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = _COST_TABLE.get(model, _DEFAULT_COST)
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


class GeminiClient:
    def __init__(self, model: str | None = None) -> None:
        self._model = model or settings.GEMINI_MODEL
        self._api_key = settings.GEMINI_API_KEY

    @retry_api_call
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ) -> GeminiResponse:
        from google import genai

        client = genai.Client(api_key=self._api_key)

        config = genai.types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        response = client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=config,
        )

        text = response.text or ""
        input_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
        output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
        cost = _calc_cost(self._model, input_tokens, output_tokens)

        logger.debug(
            "Gemini response: model={} in={} out={} cost=${:.4f}",
            self._model, input_tokens, output_tokens, cost,
        )

        return GeminiResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self._model,
            cost_usd=cost,
        )

    @retry_api_call
    async def generate_json(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.3,
    ) -> dict:
        json_instruction = (
            (system_instruction or "")
            + "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no code blocks, no explanations."
        )
        response = await self.generate(
            prompt=prompt,
            system_instruction=json_instruction,
            temperature=temperature,
        )

        # JSON 추출: 코드블록 제거
        text = response.text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

        parsed = json.loads(text)

        # response 메타를 dict에 첨부
        parsed["_meta"] = {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "model": response.model,
            "cost_usd": response.cost_usd,
        }
        return parsed
