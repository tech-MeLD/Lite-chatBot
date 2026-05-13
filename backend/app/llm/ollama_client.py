import asyncio
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout
        self._max_retries = 2

    async def chat(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_exc = None
        for attempt in range(self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/api/chat",
                        json={
                            "model": self.model,
                            "messages": messages,
                            "stream": False,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["message"]["content"]
            except (httpx.RemoteProtocolError, httpx.ReadError) as e:
                last_exc = e
                if attempt < self._max_retries:
                    logger.warning(
                        "Ollama chat attempt %d/%d failed: %s, retrying in %.1fs...",
                        attempt + 1, self._max_retries + 1, e, 1.5,
                    )
                    await asyncio.sleep(1.5)
                else:
                    raise
            except httpx.TimeoutException as e:
                last_exc = e
                if attempt < self._max_retries:
                    logger.warning(
                        "Ollama chat timed out (attempt %d/%d), retrying...",
                        attempt + 1, self._max_retries + 1,
                    )
                    await asyncio.sleep(2.0)
                else:
                    raise

        raise last_exc  # type: ignore[misc]

    async def chat_stream(self, prompt: str, system: str | None = None):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_exc = None
        for attempt in range(self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/api/chat",
                        json={
                            "model": self.model,
                            "messages": messages,
                            "stream": True,
                        },
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    import json
                                    data = json.loads(line)
                                    if "message" in data and "content" in data["message"]:
                                        yield data["message"]["content"]
                                    if data.get("done"):
                                        break
                                except json.JSONDecodeError:
                                    continue
                return  # success — exit retry loop
            except (httpx.RemoteProtocolError, httpx.ReadError) as e:
                last_exc = e
                if attempt < self._max_retries:
                    logger.warning(
                        "Ollama chat_stream attempt %d/%d failed: %s, retrying in %.1fs...",
                        attempt + 1, self._max_retries + 1, e, 1.5,
                    )
                    await asyncio.sleep(1.5)
                else:
                    raise
            except httpx.TimeoutException as e:
                last_exc = e
                if attempt < self._max_retries:
                    logger.warning(
                        "Ollama chat_stream timed out (attempt %d/%d), retrying...",
                        attempt + 1, self._max_retries + 1,
                    )
                    await asyncio.sleep(2.0)
                else:
                    raise

        raise last_exc  # type: ignore[misc]
