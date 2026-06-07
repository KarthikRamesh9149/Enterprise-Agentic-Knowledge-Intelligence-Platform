"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/ui";
import { api } from "@/lib/api";

export default function AuditLogsPage() {
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  useEffect(() => {
    api.auditLogs().then(setRows).catch(() => setRows([]));
  }, []);
  return (
    <AppShell>
      <PageHeader title="Audit logs" description="Admin-only view of authentication, document, chat, review, evaluation, and permission events." />
      <section className="table-shell">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-4 py-3">Action</th><th>Resource</th><th>User</th><th>Time</th></tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={String(row.id)} className="border-t border-line">
                <td className="px-4 py-3 font-semibold text-ink">{String(row.action)}</td>
                <td>{String(row.resource_type)} {row.resource_id ? `· ${String(row.resource_id).slice(0, 8)}` : ""}</td>
                <td className="text-slate-600">{String(row.user_id ?? "system")}</td>
                <td className="text-slate-600">{new Date(String(row.created_at)).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </AppShell>
  );
}

