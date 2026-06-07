import type { ChatResponse, ChunkItem, DocumentItem, ReviewItem, User } from "@/types/api";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("access_token");
}

export function setToken(token: string): void {
  window.localStorage.setItem("access_token", token);
}

export function clearToken(): void {
  window.localStorage.removeItem("access_token");
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(body.detail || "Request failed", res.status);
  }
  return res.json() as Promise<T>;
}

export const api = {
  register: (email: string, password: string, role: string) =>
    request<User>("/auth/register", { method: "POST", body: JSON.stringify({ email, password, role }) }),
  login: async (email: string, password: string) => {
    const body = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(body.access_token);
    return body;
  },
  me: () => request<User>("/auth/me"),
  documents: () => request<DocumentItem[]>("/documents"),
  document: (id: string) => request<DocumentItem>(`/documents/${id}`),
  chunks: (id: string) => request<ChunkItem[]>(`/documents/${id}/chunks`),
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentItem>("/documents/upload", { method: "POST", body: form });
  },
  process: (id: string) => request<DocumentItem>(`/documents/${id}/process`, { method: "POST" }),
  deleteDocument: (id: string) => request<{ status: string }>(`/documents/${id}`, { method: "DELETE" }),
  ask: (question: string) => request<ChatResponse>("/chat/query", { method: "POST", body: JSON.stringify({ question }) }),
  history: () => request<Array<Record<string, unknown>>>("/chat/history"),
  reviewItems: () => request<ReviewItem[]>("/review/items"),
  reviewAction: (id: string, action: "approve" | "edit" | "reject" | "regenerate", reviewed_answer?: string, reviewer_notes?: string) =>
    request<ReviewItem>(`/review/items/${id}/${action}`, {
      method: "POST",
      body: JSON.stringify({ reviewed_answer, reviewer_notes }),
    }),
  runEval: () => request<Record<string, unknown>>("/evals/run", { method: "POST", body: JSON.stringify({}) }),
  evalRuns: () => request<Array<Record<string, unknown>>>("/evals/runs"),
  auditLogs: () => request<Array<Record<string, unknown>>>("/admin/audit-logs"),
  analytics: () => request<Record<string, unknown>>("/admin/analytics"),
};

