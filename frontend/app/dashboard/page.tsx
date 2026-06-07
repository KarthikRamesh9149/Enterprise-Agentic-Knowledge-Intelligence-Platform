"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { Badge, MetricCard, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import type { DocumentItem } from "@/types/api";

export default function DashboardPage() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [analytics, setAnalytics] = useState<Record<string, unknown>>({});
  const [history, setHistory] = useState<Array<Record<string, unknown>>>([]);

  useEffect(() => {
    api.documents().then(setDocs).catch(() => setDocs([]));
    api.analytics().then(setAnalytics).catch(() => setAnalytics({}));
    api.history().then(setHistory).catch(() => setHistory([]));
  }, []);

  return (
    <AppShell>
      <PageHeader title="Dashboard" description="Operational view of local document intelligence, RAG confidence, review routing, and evidence quality." />
      <div className="grid grid-cols-4 gap-4">
        <MetricCard label="Documents" value={docs.length} note="Visible to current role" />
        <MetricCard label="Processed" value={docs.filter((d) => d.status === "processed").length} note="Ready for retrieval" />
        <MetricCard label="Queries" value={(analytics.total_queries as number) ?? history.length} note="Saved query history" />
        <MetricCard label="Avg confidence" value={analytics.average_confidence ? String(analytics.average_confidence) : "0"} note="Across stored queries" />
      </div>
      <div className="mt-6 grid grid-cols-[1.25fr_.75fr] gap-6">
        <section className="table-shell">
          <div className="border-b border-line px-4 py-3">
            <h2 className="font-semibold text-ink">Recent documents</h2>
          </div>
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr><th className="px-4 py-3">File</th><th>Status</th><th>Type</th><th>Uploaded</th></tr>
            </thead>
            <tbody>
              {docs.slice(0, 6).map((doc) => (
                <tr key={doc.id} className="border-t border-line">
                  <td className="px-4 py-3 font-medium text-ink">{doc.original_filename}</td>
                  <td><Badge tone={doc.status === "processed" ? "good" : doc.status === "failed" ? "bad" : "warn"}>{doc.status}</Badge></td>
                  <td className="text-slate-600">{doc.document_type}</td>
                  <td className="text-slate-600">{new Date(doc.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <section className="rounded-lg border border-line bg-white p-4 shadow-soft">
          <h2 className="font-semibold text-ink">Recent query confidence</h2>
          <div className="mt-4 space-y-3">
            {history.slice(0, 5).map((item) => (
              <div key={String(item.id)} className="border-b border-line pb-3 last:border-0">
                <p className="line-clamp-2 text-sm font-medium text-ink">{String(item.question)}</p>
                <p className="mt-1 text-xs text-slate-500">Confidence {String(item.confidence_score ?? 0)} · {String(item.status)}</p>
              </div>
            ))}
            {!history.length ? <p className="text-sm text-slate-500">Ask a grounded question to populate this panel.</p> : null}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

