"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { Badge, Button, EmptyState, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import type { ReviewItem } from "@/types/api";

export default function ReviewPage() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [notes, setNotes] = useState("");

  async function load() {
    setItems(await api.reviewItems());
  }

  useEffect(() => {
    load().catch(() => setItems([]));
  }, []);

  async function action(id: string, kind: "approve" | "edit" | "reject" | "regenerate") {
    await api.reviewAction(id, kind, kind === "edit" ? notes : undefined, notes);
    await load();
  }

  return (
    <AppShell>
      <PageHeader title="Human review" description="Review low-confidence or weakly supported answers routed by the agent workflow." />
      {!items.length ? <EmptyState title="No review items" body="Low-confidence answers will appear here for reviewer or admin action." /> : null}
      <div className="grid gap-4">
        {items.map((item) => (
          <article key={item.id} className="rounded-lg border border-line bg-white p-5 shadow-soft">
            <div className="flex items-center justify-between">
              <Badge tone={item.status === "pending" ? "warn" : "good"}>{item.status}</Badge>
              <p className="text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</p>
            </div>
            <p className="mt-3 text-sm font-semibold text-ink">{item.reason}</p>
            <pre className="mt-3 whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-sm leading-6 text-slate-700">{item.original_answer}</pre>
            <textarea className="mt-3 h-24 w-full resize-none rounded-md border border-line p-3 text-sm focus-ring" placeholder="Reviewer notes or edited answer" value={notes} onChange={(e) => setNotes(e.target.value)} />
            <div className="mt-3 flex gap-2">
              <Button onClick={() => action(item.id, "approve")}>Approve</Button>
              <Button onClick={() => action(item.id, "edit")}>Edit</Button>
              <Button onClick={() => action(item.id, "reject")}>Reject</Button>
              <Button onClick={() => action(item.id, "regenerate")}>Regenerate</Button>
            </div>
          </article>
        ))}
      </div>
    </AppShell>
  );
}

