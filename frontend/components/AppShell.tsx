"use client";

import {
  BarChart3,
  ClipboardCheck,
  FileText,
  Gauge,
  History,
  LayoutDashboard,
  LogOut,
  MessageSquareText,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, clearToken } from "@/lib/api";
import type { Role, User } from "@/types/api";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["admin", "analyst", "reviewer", "viewer"] },
  { href: "/documents", label: "Documents", icon: FileText, roles: ["admin", "analyst", "reviewer", "viewer"] },
  { href: "/chat", label: "Chat", icon: MessageSquareText, roles: ["admin", "analyst", "reviewer", "viewer"] },
  { href: "/review", label: "Review", icon: ClipboardCheck, roles: ["admin", "reviewer"] },
  { href: "/evals", label: "Evaluations", icon: Gauge, roles: ["admin"] },
  { href: "/admin/audit-logs", label: "Audit Logs", icon: History, roles: ["admin"] },
  { href: "/admin/analytics", label: "Analytics", icon: BarChart3, roles: ["admin"] },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => router.replace("/login"));
  }, [router]);

  if (!user) {
    return <main className="flex min-h-screen items-center justify-center text-sm text-slate-600">Loading workspace...</main>;
  }

  const visible = nav.filter((item) => item.roles.includes(user.role));

  return (
    <div className="flex min-h-screen bg-[#f5f7f7]">
      <aside className="fixed inset-y-0 left-0 z-10 flex w-72 flex-col bg-[#0f2f35] px-4 py-5 text-white">
        <div className="mb-8 flex items-center gap-3 px-2">
          <div className="grid size-10 place-items-center rounded-lg bg-teal-500">
            <ShieldCheck size={21} />
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight">Enterprise Knowledge</p>
            <p className="text-xs text-teal-100">Agentic Intelligence</p>
          </div>
        </div>
        <nav className="space-y-1">
          {visible.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition ${
                  active ? "bg-white text-[#0f2f35]" : "text-teal-50 hover:bg-white/10"
                }`}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <button
          className="mt-auto flex items-center gap-3 rounded-md px-3 py-2.5 text-sm text-teal-50 hover:bg-white/10"
          onClick={() => {
            clearToken();
            router.replace("/login");
          }}
        >
          <LogOut size={18} />
          Sign out
        </button>
      </aside>
      <div className="ml-72 flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-line bg-white px-8">
          <div>
            <p className="text-sm font-semibold text-ink">Knowledge Intelligence Workspace</p>
            <p className="text-xs text-slate-500">AI research papers and annual reports</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-semibold text-ink">{user.email}</p>
            <p className="text-xs uppercase tracking-wide text-teal-700">{user.role}</p>
          </div>
        </header>
        <main className="flex-1 px-8 py-7">{children}</main>
      </div>
    </div>
  );
}

export function canUpload(role: Role) {
  return role === "admin" || role === "analyst";
}

