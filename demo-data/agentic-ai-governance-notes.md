# Agentic AI Governance Notes

Agentic AI systems introduce orchestration risks beyond a single model call. A workflow may classify intent, plan retrieval, call tools, generate an answer, critique its own output, and route uncertain results to a human reviewer. Each node should produce traceable state so teams can explain what happened during a business-critical answer.

Strong governance patterns include least-privilege tool access, deterministic evaluation datasets, prompt-injection detection, citation verification, confidence thresholds, and audit logs. Human oversight is especially important when answers influence board reporting, financial analysis, customer commitments, or security decisions.

Operational risks include tool misuse, hidden context loss, stale retrieval indexes, brittle routing rules, and overconfident final answers. Mature teams track latency, citation pass rate, review rate, and unsupported-claim indicators over time.

