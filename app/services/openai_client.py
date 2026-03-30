"""OpenAI API 클라이언트 (ChatGPT, TTS, DALL-E)."""
from __future__ import annotations

from dataclasses import dataclass

import httpx
from loguru import logger
from openai import AsyncOpenAI

from app.config import settings
from app.utils.retry import retry_api_call

# 비용 단가 (per 1M tokens)
_CHAT_COST = {
    "gpt-4o": {"input": 2.50, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}
_DEFAULT_CHAT_COST = {"input": 2.50, "output": 10.0}


@dataclass
class ChatResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    cost_usd: float


def _calc_chat_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = _CHAT_COST.get(model, _DEFAULT_CHAT_COST)
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


class OpenAIClient:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    @retry_api_call
    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.3,
        response_format: dict | None = None,
    ) -> ChatResponse:
        model = model or settings.OPENAI_CHAT_MODEL
        kwargs: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format

        resp = await self._client.chat.completions.create(**kwargs)

        text = resp.choices[0].message.content or ""
        usage = resp.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        cost = _calc_chat_cost(model, input_tokens, output_tokens)

        logger.debug(
            "OpenAI chat: model={} in={} out={} cost=${:.4f}",
            model, input_tokens, output_tokens, cost,
        )

        return ChatResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            cost_usd=cost,
        )

    @retry_api_call
    async def tts(
        self,
        text: str,
        voice: str | None = None,
        model: str | None = None,
    ) -> tuple[bytes, float]:
        model = model or settings.OPENAI_TTS_MODEL
        voice = voice or settings.OPENAI_TTS_VOICE

        resp = await self._client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format="mp3",
        )

        audio_bytes = resp.content
        char_count = len(text)
        cost = (char_count / 1000) * settings.TTS_COST_PER_1K_CHARS

        logger.debug("OpenAI TTS: chars={} cost=${:.4f}", char_count, cost)
        return audio_bytes, cost

    @retry_api_call
    async def generate_image(
        self,
        prompt: str,
        size: str | None = None,
        quality: str = "standard",
    ) -> tuple[bytes, float]:
        size = size or settings.OPENAI_IMAGE_SIZE
        model = settings.OPENAI_IMAGE_MODEL

        resp = await self._client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )

        image_url = resp.data[0].url
        async with httpx.AsyncClient(timeout=60.0) as http:
            img_resp = await http.get(image_url)
            img_resp.raise_for_status()
            image_bytes = img_resp.content

        cost = settings.DALLE_COST_PER_IMAGE
        logger.debug("OpenAI DALL-E: size={} cost=${:.4f}", size, cost)
        return image_bytes, cost
