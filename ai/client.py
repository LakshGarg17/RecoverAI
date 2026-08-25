import os
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from pydantic import BaseModel


class RecoverAIClient:
    """Wrapper client for OpenAI-powered recovery agent decisions."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def get_structured_decision(
        self, prompt: str, system_message: str, response_format_schema: type[BaseModel]
    ) -> BaseModel:
        """Execute OpenAI completion and parse into Pydantic structured response."""
        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            response_format=response_format_schema,
        )
        return response.choices[0].message.parsed
