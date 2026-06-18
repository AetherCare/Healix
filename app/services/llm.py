"""
LLM provider abstraction with strategy pattern for Groq, OpenAI, and Anthropic.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional

from app.core.config import Settings, get_settings


class LLMProvider(ABC):
    """Abstract large language model interface."""

    @abstractmethod
    async def complete(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        """Generate a completion from chat messages."""

    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Stream completion tokens from chat messages."""


class GroqProvider(LLMProvider):
    """Groq API provider using native groq SDK."""

    def __init__(self, api_key: str, model: str) -> None:
        from groq import AsyncGroq

        self.client = AsyncGroq(api_key=api_key)
        self.model = model

    async def complete(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        kwargs: Dict = {"model": self.model, "messages": messages}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class OpenAIProvider(LLMProvider):
    """OpenAI API provider for future hot-swap compatibility."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def complete(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        kwargs: Dict = {"model": self.model, "messages": messages}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider for future hot-swap compatibility."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022") -> None:
        from anthropic import AsyncAnthropic

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append({"role": msg["role"], "content": msg["content"]})
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_msg,
            messages=chat_messages,
        )
        return response.content[0].text

    async def stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append({"role": msg["role"], "content": msg["content"]})
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=system_msg,
            messages=chat_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text


def create_llm_provider(settings: Optional[Settings] = None) -> LLMProvider:
    """
    Factory returning the configured LLM provider implementation.

    Controlled by LLM_PROVIDER environment variable (groq | openai | anthropic).
    """
    cfg = settings or get_settings()
    provider = cfg.llm_provider.lower()

    if provider == "openai":
        return OpenAIProvider(api_key=cfg.openai_api_key)
    if provider == "anthropic":
        return AnthropicProvider(api_key=cfg.anthropic_api_key)
    return GroqProvider(api_key=cfg.groq_api_key, model=cfg.groq_model)
