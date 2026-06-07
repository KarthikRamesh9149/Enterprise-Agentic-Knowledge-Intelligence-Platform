# OpenAI Token Plan

## Default Recommendation

Use mock providers for tests and local portfolio demos. Enable OpenAI only when you want higher-quality generated answers.

Recommended OpenAI settings:

```env
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-5-mini
MAX_OUTPUT_TOKENS=900
RAG_TOP_K=8
RAG_MAX_CONTEXT_CHARS=12000
CITATION_MAX_CHARS=360
```

## Why These Defaults

- `text-embedding-3-small` keeps embedding cost low.
- `gpt-5-mini` is the cost-efficient GPT-5 option for precise, well-scoped prompts.
- The OpenAI provider uses the Responses API, which OpenAI recommends for reasoning and agentic workflows.
- RAG uses retrieved snippets rather than full documents.
- Citation quotes are capped.
- Output length is capped.
- Low-confidence answers are routed to review instead of spending more tokens trying to force confidence.

## Prompt Strategy

The OpenAI-compatible provider sends a concise system message:

- answer only from retrieved evidence
- cite factual claims with `[C#]`
- prefer concise enterprise-style responses
- state limitations when support is weak

The app does not send uploaded documents as instructions. Uploaded text is treated as untrusted evidence only.

## Cost Controls

- Lower `RAG_TOP_K` to 4 for quick demos.
- Lower `RAG_MAX_CONTEXT_CHARS` to 6000 for short annual report excerpts.
- Keep `MAX_OUTPUT_TOKENS` between 500 and 900 for portfolio demos.
- Use evals with mock providers by default.
- Avoid running full eval suites with paid providers unless intentionally benchmarking.

## Quality Controls

- Increase `RAG_TOP_K` only when answers miss citations.
- Increase `RAG_MAX_CONTEXT_CHARS` only when relevant evidence is being truncated.
- Prefer better chunking and retrieval before raising model spend.
- Use human review for weak answers rather than generating long speculative responses.

## Model Tiers

- Default quality/cost: `gpt-5-mini`.
- Lowest-cost exploratory mode: `gpt-5-nano` with smaller `RAG_TOP_K`.
- Higher-quality board summaries: raise to a stronger GPT-5 family model only for final executive outputs or eval benchmarking.
- Embeddings: start with `text-embedding-3-small`; move to `text-embedding-3-large` only if retrieval evals show recall gaps.
