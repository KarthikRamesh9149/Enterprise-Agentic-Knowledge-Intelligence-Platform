# Evaluation

Evaluations run local questions through the same agentic RAG path used by chat.

## Datasets

- `demo-data/eval-annual-report.jsonl`
- `demo-data/eval-research.jsonl`

Each case includes question, expected keywords, expected documents, answer type, minimum citation count, and notes.

## Metrics

- keyword coverage
- citation count
- citation verification pass rate
- confidence score
- latency
- estimated token usage
- pass/fail status

## Running

Use the frontend Evaluations page or:

```bash
make evals
```

Evals default to mock providers and do not require OpenAI.

