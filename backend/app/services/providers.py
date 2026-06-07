import hashlib
import math
from dataclasses import dataclass

import httpx

from app.core.config import settings


class EmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class MockEmbeddingProvider(EmbeddingProvider):
    def embed(self, text: str) -> list[float]:
        vector = [0.0] * settings.embedding_dimension
        words = [word.strip(".,:;!?()[]{}").lower() for word in text.split()]
        for word in words:
            if not word:
                continue
            digest = hashlib.sha256(word.encode()).digest()
            idx = int.from_bytes(digest[:4], "big") % settings.embedding_dimension
            sign = 1 if digest[4] % 2 == 0 else -1
            vector[idx] += sign * (1 + len(word) / 20)
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [round(v / norm, 6) for v in vector]


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    def embed(self, text: str) -> list[float]:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI-compatible embeddings")
        payload: dict[str, object] = {"model": settings.openai_embedding_model, "input": text}
        if settings.openai_embedding_model.startswith("text-embedding-3"):
            payload["dimensions"] = settings.embedding_dimension
        response = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]


def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider == "openai":
        return OpenAICompatibleEmbeddingProvider()
    return MockEmbeddingProvider()


@dataclass
class LLMResult:
    answer: str
    total_tokens: int = 0
    estimated_cost: float = 0


class LLMProvider:
    def generate(self, question: str, contexts: list[dict]) -> LLMResult:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    def generate(self, question: str, contexts: list[dict]) -> LLMResult:
        if not contexts:
            return LLMResult(
                "The uploaded documents do not provide enough relevant evidence to answer this question."
            )
        bullets = []
        for index, ctx in enumerate(contexts[:4], start=1):
            quote = ctx["content"].replace("\n", " ").strip()[:280]
            bullets.append(f"- Evidence {index}: {quote} [C{index}]")
        answer = (
            f"Based on the processed AI research and annual report evidence, the answer to '{question}' is grounded in the retrieved documents.\n"
            + "\n".join(bullets)
            + "\nLimitations: this mock local provider only synthesizes from retrieved chunks and avoids unsupported claims."
        )
        return LLMResult(answer=answer, total_tokens=sum(len(c["content"].split()) for c in contexts) + len(question.split()))


class OpenAICompatibleLLMProvider(LLMProvider):
    @staticmethod
    def _extract_output_text(body: dict) -> str:
        if body.get("output_text"):
            return str(body["output_text"]).strip()
        parts: list[str] = []
        for item in body.get("output", []):
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if not isinstance(content, dict):
                    continue
                text = content.get("text") or content.get("value")
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()

    def generate(self, question: str, contexts: list[dict]) -> LLMResult:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI-compatible chat")
        context_parts = []
        remaining = settings.rag_max_context_chars
        for i, context in enumerate(contexts, start=1):
            content = str(context["content"])[:remaining]
            if not content:
                break
            context_parts.append(f"[C{i}] {content}")
            remaining -= len(content)
        context_text = "\n\n".join(context_parts)
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_chat_model,
                "max_output_tokens": settings.max_output_tokens,
                "reasoning": {"effort": settings.openai_reasoning_effort},
                "text": {"verbosity": settings.openai_text_verbosity},
                "input": [
                    {
                        "role": "system",
                        "content": "You are an enterprise RAG analyst. Use only the provided evidence. Cite claims with [C#]. Prefer concise answers. State limitations when evidence is weak.",
                    },
                    {"role": "user", "content": f"Question: {question}\nEvidence:\n{context_text}"},
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
        body = response.json()
        usage = body.get("usage", {})
        text = self._extract_output_text(body)
        if not text:
            fallback = MockLLMProvider().generate(question, contexts)
            return LLMResult(
                answer=(
                    fallback.answer
                    + "\nProvider note: OpenAI returned no assistant text for this request, so the local grounded fallback assembled this answer from retrieved evidence."
                ),
                total_tokens=usage.get("total_tokens", fallback.total_tokens),
                estimated_cost=0.0,
            )
        return LLMResult(text, usage.get("total_tokens", 0), 0.0)


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "openai":
        return OpenAICompatibleLLMProvider()
    return MockLLMProvider()
