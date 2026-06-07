export type Role = "admin" | "analyst" | "reviewer" | "viewer";

export type User = {
  id: string;
  email: string;
  role: Role;
  created_at: string;
};

export type DocumentItem = {
  id: string;
  filename: string;
  original_filename: string;
  document_type: string;
  source_type: string;
  uploaded_by: string;
  status: "uploaded" | "processing" | "processed" | "failed";
  file_size: number;
  content_hash: string;
  error_message?: string | null;
  event_metadata: Record<string, unknown>;
  created_at: string;
  processed_at?: string | null;
};

export type ChunkItem = {
  id: string;
  chunk_index: number;
  content: string;
  page_number?: number | null;
  section_title?: string | null;
  event_metadata: Record<string, unknown>;
};

export type Citation = {
  id: string;
  document_id: string;
  chunk_id: string;
  quote: string;
  page_number?: number | null;
  relevance_score: number;
  verification_status: string;
};

export type TraceStep = {
  node_name: string;
  input_summary: string;
  output_summary: string;
  status: string;
  latency_ms: number;
};

export type ChatResponse = {
  query_id: string;
  session_id: string;
  answer: string;
  citations: Citation[];
  confidence_score: number;
  confidence_band: string;
  status: string;
  human_review_required: boolean;
  retrieved_evidence: Array<Record<string, unknown>>;
  trace: TraceStep[];
  latency_ms: number;
};

export type ReviewItem = {
  id: string;
  query_id: string;
  status: string;
  reason: string;
  original_answer: string;
  reviewed_answer?: string | null;
  reviewer_notes?: string | null;
  created_at: string;
};

