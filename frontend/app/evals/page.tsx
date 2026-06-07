"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { Button, MetricCard, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";

export default function EvalsPage() {
  const [runs, setRuns] = useState<Array<Record<string, unknown>>>([]);

  async function load() {
    setRuns(await api.evalRuns());
  }

  useEffect(() => {
    load().catch(() => setRuns([]));
  }, []);

  async function run() {
    await api.runEval();
    await load();
  }

  const latest = runs[0]?.metrics as Record<string, unknown> | undefined;
  return (
    <AppShell>
      <PageHeader title="Evaluations" description="Run local mock-provider evaluation cases for retrieval, citation, confidence, and keyword coverage." action={<Button onClick={run}>Run evaluation</Button>} />
      <div className="grid grid-cols-3 gap-4">
        <MetricCard label="Runs" value={runs.length} />
        <MetricCard label="Latest pass rate" value={latest?.pass_rate ? String(latest.pass_rate) : "0"} />
        <MetricCard label="Cases" value={latest?.cases ? String(latest.cases) : "0"} />
      </div>
      <section className="table-shell mt-6">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-4 py-3">Run</th><th>Status</th><th>Metrics</th><th>Created</th></tr></thead>
          <tbody>
            {runs.map((run) => (
              <tr key={String(run.id)} className="border-t border-line">
                <td className="px-4 py-3 font-semibold text-ink">{String(run.name)}</td>
                <td>{String(run.status)}</td>
                <td className="text-slate-600">{JSON.stringify(run.metrics)}</td>
                <td className="text-slate-600">{new Date(String(run.created_at)).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </AppShell>
  );
}

