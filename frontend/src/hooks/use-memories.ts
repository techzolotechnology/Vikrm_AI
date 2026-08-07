import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { Memory } from "@/types/memory";

export function useMemories(typeFilter?: string) {
  return useQuery({
    queryKey: ["memories", typeFilter],
    queryFn: async () => {
      const url = typeFilter ? `/memories?memory_type=${typeFilter}` : "/memories";
      const { data } = await apiClient.get<Memory[]>(url);
      return data;
    },
  });
}

export function useCreateMemory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { content: string; memory_type?: string; is_pinned?: boolean }) => {
      const { data } = await apiClient.post<Memory>("/memories", params);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memories"] });
    },
  });
}

export function useUpdateMemory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      memoryId,
      content,
      memory_type,
      is_pinned,
      is_archived,
    }: {
      memoryId: number;
      content?: string;
      memory_type?: string;
      is_pinned?: boolean;
      is_archived?: boolean;
    }) => {
      const { data } = await apiClient.patch<Memory>(`/memories/${memoryId}`, {
        content,
        memory_type,
        is_pinned,
        is_archived,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memories"] });
    },
  });
}

export function useDeleteMemory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (memoryId: number) => {
      await apiClient.delete(`/memories/${memoryId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memories"] });
    },
  });
}

export function useSearchMemories() {
  return useMutation({
    mutationFn: async (params: { query: string; top_k?: number }) => {
      const { data } = await apiClient.post<{ memory: Memory; distance: number }[]>(
        "/memories/search",
        params,
      );
      return data;
    },
  });
}
