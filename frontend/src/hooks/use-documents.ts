import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { DocumentChunkResult, DocumentItem } from "@/types/document";

export function useDocuments() {
  return useQuery({
    queryKey: ["documents"],
    queryFn: async () => {
      const { data } = await apiClient.get<DocumentItem[]>("/documents");
      return data;
    },
    refetchInterval: (query) => {
      const docs = query.state.data as DocumentItem[] | undefined;
      const stillProcessing = docs?.some((d) => d.status === "processing");
      return stillProcessing ? 2000 : false;
    },
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.post<DocumentItem>("/documents", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (documentId: number) => {
      await apiClient.delete(`/documents/${documentId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useRenameDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, filename }: { documentId: number; filename: string }) => {
      const { data } = await apiClient.patch<DocumentItem>(`/documents/${documentId}`, { filename });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useDocumentContent(documentId: number | null) {
  return useQuery({
    queryKey: ["document-content", documentId],
    queryFn: async () => {
      if (!documentId) return null;
      const { data } = await apiClient.get<{ filename: string; chunks: string[] }>(`/documents/${documentId}/content`);
      return data;
    },
    enabled: !!documentId,
  });
}

export function useSearchDocuments() {
  return useMutation({
    mutationFn: async (params: { query: string; top_k?: number }) => {
      const { data } = await apiClient.post<DocumentChunkResult[]>("/documents/search", params);
      return data;
    },
  });
}
