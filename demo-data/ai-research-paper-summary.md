# AI Research Paper Summary

Recent retrieval augmented generation research shows that answer quality depends on retrieval recall, chunk quality, citation discipline, and model instruction hierarchy. RAG systems can fail when relevant context is not retrieved, when chunks are too broad, or when citations are attached to unsupported claims.

The research recommends separating document text from system instructions because uploaded content can contain prompt injection. Document text should be treated as untrusted evidence. Systems should verify that answer claims are grounded in retrieved passages and route weak answers to human review.

Key limitations include stale corpora, ambiguous questions, duplicated chunks, poor ranking, and overconfident generation. Evaluation should measure retrieval recall at k, citation coverage, unsupported claim rate, latency, and confidence calibration.

