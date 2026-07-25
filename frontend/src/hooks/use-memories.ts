import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { Memory } from "@/types/memory";

export function useMemories() {
  return useQuery({
    queryKey: ["memories"],
    queryFn: async () => {
      const { data } = await apiClient.get<Memory[]>("/memories");
      return data;
    },
  });
}

export function useCreateMemory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { content: string; memory_type?: string }) => {
      const { data } = await apiClient.post<Memory>("/memories", params);
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
