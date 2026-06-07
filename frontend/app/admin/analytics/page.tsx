"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { MetricCard, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<Record<string, unknown>>({});
  useEffect(() => {
    api.analytics().then(setAnalytics).catch(() => setAnalytics({}));
  }, []);
  return (
    <AppShell>
      <PageHeader title="Admin analytics" description="Computed local metrics for documents, queries, confidence, citations, latency, and human review." />
      <div className="grid grid-cols-4 gap-4">
        {Object.entries(analytics).map(([key, value]) => (
          <MetricCard key={key} label={key.replaceAll("_", " ")} value={typeof value === "object" ? JSON.stringify(value) : String(value)} />
        ))}
      </div>
    </AppShell>
  );
}

