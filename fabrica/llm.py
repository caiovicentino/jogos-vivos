"""Provider LLM OpenAI-compatível + MockLLM para rodar o grafo sem chave."""

from __future__ import annotations

import os
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

SYSTEM_BASE = "Você é parte de um pipeline autônomo e profissional de criação de jogos web. Seja conciso, específico e sem jargão."


class LLM:
    """Cliente mínimo sobre qualquer endpoint compatível com OpenAI."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None):
        self.model = model or os.environ.get("LLM_MODEL", "deepseek-chat")
        self.base_url = base_url or os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1")
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "LLM_API_KEY não definida. Exporte as variáveis de .env.example ou rode com --mock."
            )
        from openai import OpenAI  # import tardio: mantém o mock sem dependência

        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def json(self, system: str, user: str, schema: type[T], retries: int = 2) -> T:
        last_err: Exception | None = None
        for _ in range(retries + 1):
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.8,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user + "\n\nResponda APENAS com JSON válido no schema descrito."},
                ],
            )
            raw = resp.choices[0].message.content or "{}"
            try:
                return schema.model_validate_json(raw)
            except Exception as err:  # noqa: BLE001 — retry com o erro anexado
                last_err = err
        raise RuntimeError(f"LLM não produziu JSON válido para {schema.__name__}: {last_err}")

    def text(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0.9,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""


def strip_fences(code: str) -> str:
    code = code.strip()
    if code.startswith("```"):
        lines = code.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        code = "\n".join(lines)
    return code.strip()
