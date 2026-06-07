"use client";

import { Send } from "lucide-react";
import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import { Badge, Button, EmptyState, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import type { ChatResponse } from "@/types/api";

export default function ChatPage() {
  const [question, setQuestion] = useState("Summarize the main AI infrastructure risks across the uploaded annual reports.");
  const [answer, setAnswer] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function ask() {
    setLoading(true);
    setError("");
    try {
      setAnswer(await api.ask(question));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <PageHeader title="Agentic chat" description="Ask board-level or analyst questions over processed research and annual report evidence with citations, confidence, and trace visibility." />
      <section className="grid grid-cols-[1fr_380px] gap-6">
        <div className="space-y-4">
          <div className="rounded-lg border border-line bg-white p-4 shadow-soft">
            <textarea className="h-28 w-full resize-none rounded-md border border-line p-3 text-sm focus-ring" value={question} onChange={(e) => setQuestion(e.target.value)} />
            <div className="mt-3 flex items-center justify-between">
              {error ? <p className="text-sm text-rose-700">{error}</p> : <p className="text-sm text-slate-500">Document text is treated as untrusted evidence.</p>}
              <Button onClick={ask} disabled={loading}><Send className="mr-2" size={16} />{loading ? "Running..." : "Ask"}</Button>
            </div>
          </div>
          {answer ? (
            <article className="rounded-lg border border-line bg-white p-5 shadow-soft">
              <div className="mb-3 flex items-center gap-2">
                <Badge tone={answer.confidence_band === "high" ? "good" : answer.confidence_band === "medium" ? "warn" : "bad"}>{answer.confidence_band} confidence</Badge>
                {answer.human_review_required ? <Badge tone="warn">human review</Badge> : null}
                <span className="text-xs text-slate-500">{answer.latency_ms} ms</span>
              </div>
              <pre className="whitespace-pre-wrap text-sm leading-6 text-ink">{answer.answer}</pre>
            </article>
          ) : <EmptyState title="No answer yet" body="Ask a question after uploading and processing demo documents." />}
          {answer ? (
            <section className="grid gap-3">
              <h2 className="font-semibold text-ink">Citations</h2>
              {answer.citations.map((citation, index) => (
                <div key={citation.id} className="rounded-lg border border-line bg-white p-4">
                  <p className="text-xs font-semibold text-teal-700">C{index + 1} · {citation.verification_status} · relevance {citation.relevance_score}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-700">{citation.quote}</p>
                </div>
              ))}
            </section>
          ) : null}
        </div>
        <aside className="space-y-4">
          <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
            <h2 className="font-semibold text-ink">Agent trace</h2>
            <div className="mt-4 space-y-3">
              {answer?.trace.map((step) => (
                <div key={step.node_name} className="border-l-2 border-teal-600 pl-3">
                  <p className="text-sm font-semibold text-ink">{step.node_name}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-600">{step.output_summary}</p>
                  <p className="mt-1 text-xs text-slate-400">{step.latency_ms} ms</p>
                </div>
              )) ?? <p className="text-sm text-slate-500">Trace steps appear after a query.</p>}
            </div>
          </section>
          <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
            <h2 className="font-semibold text-ink">Retrieved evidence</h2>
            <div className="mt-4 space-y-3">
              {answer?.retrieved_evidence.slice(0, 5).map((item, i) => (
                <p key={i} className="text-xs leading-5 text-slate-600">{String(item.document_name)} · relevance {String(item.relevance_score)}</p>
              )) ?? <p className="text-sm text-slate-500">Evidence ranking appears after a query.</p>}
            </div>
          </section>
        </aside>
      </section>
    </AppShell>
  );
}

