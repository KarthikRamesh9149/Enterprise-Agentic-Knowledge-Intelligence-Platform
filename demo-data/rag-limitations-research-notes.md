# RAG Limitations Research Notes

Retrieval augmented generation improves grounding, but it does not guarantee correctness. If the retriever misses the relevant passage, if chunks remove important surrounding context, or if the generator ignores weak evidence, the final answer can still be incomplete or misleading.

Common failure modes include low recall at k, semantically similar but wrong passages, duplicate evidence, stale documents, table extraction errors, citation drift, and unsupported synthesis across unrelated sources. Evaluation should measure retrieval recall, answer relevance, citation coverage, unsupported claim rate, and latency.

Useful mitigations include hybrid retrieval, reranking, query rewriting, page-level citations, confidence scoring, answer abstention, and human review for low-confidence responses.

