export interface DocumentItem {
  id: number;
  filename: string;
  content_type: string;
  status: "processing" | "ready" | "failed";
  char_count: number;
  chunk_count: number;
  error: string | null;
  created_at: string;
}

export interface DocumentChunkResult {
  document_id: number;
  filename: string;
  chunk_index: number;
  content: string;
  distance: number;
}
