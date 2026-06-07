"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { Badge, EmptyState, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import type { ChunkItem, DocumentItem } from "@/types/api";

export default function DocumentDetailPage() {
  const params = useParams<{ id: string }>();
  const [doc, setDoc] = useState<DocumentItem | null>(null);
  const [chunks, setChunks] = useState<ChunkItem[]>([]);

  useEffect(() => {
    api.document(params.id).then(setDoc);
    api.chunks(params.id).then(setChunks).catch(() => setChunks([]));
  }, [params.id]);

  const warnings = (doc?.event_metadata?.prompt_injection_warnings as string[] | undefined) || [];

  return (
    <AppShell>
      <PageHeader title="Document detail" description="Metadata, processing warnings, and chunk previews for the selected uploaded document." />
      {!doc ? <EmptyState title="Loading document" body="Fetching metadata and chunks." /> : (
        <>
          <section className="rounded-lg border border-line bg-white p-5 shadow-soft">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-ink">{doc.original_filename}</h2>
                <p className="mt-1 text-sm text-slate-600">Hash {doc.content_hash.slice(0, 18)} · {doc.document_type}</p>
              </div>
              <Badge tone={doc.status === "processed" ? "good" : doc.status === "failed" ? "bad" : "warn"}>{doc.status}</Badge>
            </div>
            {warnings.length ? <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">Prompt-injection warnings detected: {warnings.join(", ")}</p> : null}
          </section>
          <section className="mt-6 grid gap-4">
            {chunks.map((chunk) => (
              <article key={chunk.id} className="rounded-lg border border-line bg-white p-4">
                <p className="text-xs font-semibold uppercase text-slate-500">Chunk {chunk.chunk_index} {chunk.page_number ? `· Page ${chunk.page_number}` : ""}</p>
                <p className="mt-2 text-sm leading-6 text-slate-700">{chunk.content}</p>
              </article>
            ))}
            {!chunks.length ? <EmptyState title="No chunks available" body="Process the document to create searchable chunks and embeddings." /> : null}
          </section>
        </>
      )}
    </AppShell>
  );
}

