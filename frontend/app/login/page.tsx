"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api } from "@/lib/api";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const demoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
  const [email, setEmail] = useState(demoMode ? "analyst@example.com" : "");
  const [password, setPassword] = useState(demoMode ? "LocalAnalyst123!" : "");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "register") await api.register(email, password);
      await api.login(email, password);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen grid-cols-1 bg-[#f5f7f7] lg:grid-cols-[1fr_440px]">
      <section className="flex items-center px-10 py-12">
        <div className="max-w-3xl">
          <h1 className="text-4xl font-semibold leading-tight text-ink">Enterprise Agentic Knowledge Intelligence Platform</h1>
          <p className="mt-4 text-lg leading-8 text-slate-600">
            Local-first AI research and annual report intelligence with document ingestion, citation-grounded RAG, confidence scoring, human review, audit logs, and evaluations.
          </p>
          <div className="mt-8 grid max-w-2xl grid-cols-3 gap-3 text-sm">
            {["Cited answers", "Agent traces", "Review queue"].map((item) => (
              <div key={item} className="rounded-lg border border-line bg-white p-4 font-medium text-ink shadow-soft">
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>
      <section className="flex items-center border-l border-line bg-white px-8">
        <form onSubmit={submit} className="w-full">
          <h2 className="text-2xl font-semibold text-ink">{mode === "login" ? "Sign in" : "Register"}</h2>
          <p className="mt-1 text-sm text-slate-600">Use a seeded demo account or create a local user.</p>
          <label className="mt-6 block text-sm font-medium text-ink">Email</label>
          <input className="mt-2 w-full rounded-md border border-line px-3 py-2 focus-ring" value={email} onChange={(e) => setEmail(e.target.value)} />
          <label className="mt-4 block text-sm font-medium text-ink">Password</label>
          <input className="mt-2 w-full rounded-md border border-line px-3 py-2 focus-ring" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          {mode === "register" ? <p className="mt-4 text-xs text-slate-600">New accounts receive Viewer access. An administrator must grant any additional privileges.</p> : null}
          {error ? <p className="mt-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}
          <button className="mt-6 w-full rounded-md bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-800" disabled={loading}>
            {loading ? "Working..." : mode === "login" ? "Sign in" : "Create account"}
          </button>
          <button type="button" className="mt-4 text-sm font-medium text-teal-700" onClick={() => setMode(mode === "login" ? "register" : "login")}>
            {mode === "login" ? "Create a local account" : "Back to sign in"}
          </button>
          {demoMode ? <div className="mt-8 rounded-lg bg-slate-50 p-4 text-xs leading-6 text-slate-600">Local demo mode is enabled. Seeded accounts and passwords are documented in the README.</div> : null}
        </form>
      </section>
    </main>
  );
}
