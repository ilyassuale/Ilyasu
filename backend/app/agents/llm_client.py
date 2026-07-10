"""OpenAI / LangChain LLM client with prompt templating."""
from __future__ import annotations

import json
import os
from typing import Any, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import settings


def _api_key() -> SecretStr | None:
    key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
    return SecretStr(key) if key else None


def get_llm(temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=temperature,
        api_key=_api_key(),
    )


def _parse_json(content: str) -> dict[str, Any]:
    # Try to extract JSON from markdown code fences
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        return cast(dict[str, Any], json.loads(text))
    except json.JSONDecodeError:
        # Fallback: wrap as raw text field
        return {"raw": text, "parse_error": True}


def chat(system: str, user: str, temperature: float = 0.2, parse_json_output: bool = False) -> Any:
    llm = get_llm(temperature)
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    response = llm.invoke(messages)
    content = response.content
    if isinstance(content, (list, dict)):
        content = json.dumps(content)
    if parse_json_output:
        return _parse_json(content)
    return content


def embeddings(texts: list[str]) -> list[list[float]]:
    from langchain_openai import OpenAIEmbeddings

    client = OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=_api_key(),
    )
    return client.embed_documents(texts)
