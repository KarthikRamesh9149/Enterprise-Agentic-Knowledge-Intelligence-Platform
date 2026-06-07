"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { Badge, Button, EmptyState, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import type { DocumentItem } from "@/types/api";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");

  async function load() {
    setDocs(await api.documents());
  }

  useEffect(() => {
    load().catch(() => setDocs([]));
  }, []);

  async function upload() {
    if (!file) return;
    setMessage("Uploading...");
    await api.upload(file);
    setFile(null);
    setMessage("Uploaded. Process the document to make it searchable.");
    await load();
  }

  async function process(id: string) {
    setMessage("Processing document...");
    await api.process(id);
    setMessage("Processing finished.");
    await load();
  }

  return (
    <AppShell>
      <PageHeader title="Documents" description="Upload AI research notes and annual report excerpts, process them into chunks, and prepare embeddings for local vector retrieval." />
      <section className="mb-6 rounded-lg border border-line bg-white p-4 shadow-soft">
        <div className="flex items-center gap-3">
          <input type="file" className="focus-ring flex-1 rounded-md border border-line px-3 py-2 text-sm" accept=".pdf,.txt,.md,.markdown,.csv" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <Button onClick={upload} disabled={!file}>Upload</Button>
        </div>
        {message ? <p className="mt-3 text-sm text-slate-600">{message}</p> : null}
      </section>
      {!docs.length ? <EmptyState title="No documents yet" body="Upload generated demo reports or research notes, then process them for retrieval." /> : null}
      <section className="table-shell">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr><th className="px-4 py-3">Document</th><th>Status</th><th>Type</th><th>Size</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {docs.map((doc) => (
              <tr key={doc.id} className="border-t border-line">
                <td className="px-4 py-3"><Link className="font-semibold text-teal-700" href={`/documents/${doc.id}`}>{doc.original_filename}</Link></td>
                <td><Badge tone={doc.status === "processed" ? "good" : doc.status === "failed" ? "bad" : "warn"}>{doc.status}</Badge></td>
                <td className="text-slate-600">{doc.document_type}</td>
                <td className="text-slate-600">{Math.round(doc.file_size / 1024)} KB</td>
                <td className="space-x-2">
                  {doc.status !== "processed" ? <button className="text-sm font-semibold text-teal-700" onClick={() => process(doc.id)}>Process</button> : null}
                  <button className="text-sm font-semibold text-rose-700" onClick={() => api.deleteDocument(doc.id).then(load)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </AppShell>
  );
}

